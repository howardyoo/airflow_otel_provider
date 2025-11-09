# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import TYPE_CHECKING

from opentelemetry import trace
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import HOST_NAME, SERVICE_NAME, Resource

from airflow.configuration import conf
from airflow.utils.log.file_task_handler import FileTaskHandler
from airflow.utils.net import get_hostname
from airflow_provider_opentelemetry.hooks.otel import (
    is_otel_traces_enabled,
    DEFAULT_SERVICE_NAME,
    OTEL_CONN_ID,
)
from airflow_provider_opentelemetry.util import gen_trace_id, gen_span_id

if TYPE_CHECKING:
    from airflow.models import TaskInstance

log = logging.getLogger(__name__)


class OtelTaskHandler(FileTaskHandler):
    """
    OpenTelemetry Task Handler for Apache Airflow.
    
    This handler extends the FileTaskHandler to emit task logs to an OpenTelemetry
    collector in OTLP format while maintaining the standard file-based logging.
    
    Logs are automatically associated with the task's trace and span context,
    allowing for correlation between traces, spans, and logs in observability platforms.
    """

    def __init__(self, base_log_folder: str, filename_template: str | None = None, **kwargs):
        """
        Initialize OtelTaskHandler.
        
        :param base_log_folder: Base log folder for file-based logging
        :param filename_template: Template for log file names
        """
        super().__init__(base_log_folder, filename_template, **kwargs)
        
        self.otel_enabled = False
        self.logger_provider = None
        self.otel_handler = None
        
        try:
            # Initialize OTEL logging if configuration is available
            self._initialize_otel_logging()
        except Exception as e:
            log.warning(f"Failed to initialize OpenTelemetry logging: {e}")

    def _initialize_otel_logging(self):
        """Initialize OpenTelemetry logging components."""
        # Get OTEL configuration
        otel_url = None
        otel_service = DEFAULT_SERVICE_NAME
        api_key = None
        header_name = None
        
        # Check if OTEL traces are enabled in Airflow config
        if is_otel_traces_enabled():
            ssl_active = conf.getboolean("traces", "otel_ssl_active")
            host = conf.get("traces", "otel_host")
            port = conf.getint("traces", "otel_port")
            protocol = "https" if ssl_active else "http"
            otel_url = f"{protocol}://{host}:{port}"
            otel_service = conf.get("traces", "otel_service")
        else:
            # Try to get configuration from environment or connection
            # This allows the logging provider to work independently
            otel_url = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
            otel_service = os.getenv("OTEL_SERVICE_NAME", DEFAULT_SERVICE_NAME)
            api_key = os.getenv("OTEL_EXPORTER_OTLP_HEADERS_API_KEY")
            header_name = os.getenv("OTEL_EXPORTER_OTLP_HEADERS_API_KEY_NAME")
        
        if not otel_url:
            log.info("OTEL endpoint not configured, OpenTelemetry logging disabled")
            return
        
        # Create resource with service information
        resource = Resource.create(
            attributes={
                HOST_NAME: get_hostname(),
                SERVICE_NAME: otel_service,
                "component": "airflow.task.logs",
            }
        )
        
        # Setup headers for authentication if needed
        headers = {"Content-Type": "application/json"}
        if api_key and header_name:
            headers[header_name] = api_key
        
        # Create OTLP log exporter
        log_exporter = OTLPLogExporter(
            endpoint=f"{otel_url}/v1/logs",
            headers=headers
        )
        
        # Create logger provider with batch processor
        self.logger_provider = LoggerProvider(resource=resource)
        self.logger_provider.add_log_record_processor(
            BatchLogRecordProcessor(log_exporter)
        )
        
        # Create logging handler
        self.otel_handler = LoggingHandler(
            level=logging.NOTSET,
            logger_provider=self.logger_provider
        )
        
        self.otel_enabled = True
        log.info("OpenTelemetry task logging initialized successfully")

    def set_context(self, ti: TaskInstance, *, identifier: str | None = None):
        """
        Set context for the handler and attach OTEL handler with trace context.
        
        :param ti: TaskInstance
        :param identifier: Optional identifier for the log
        """
        super().set_context(ti, identifier=identifier)
        
        if self.otel_enabled and self.otel_handler and ti:
            # Get the logger for this task
            logger = logging.getLogger(f"airflow.task.{ti.dag_id}.{ti.task_id}")
            
            # Remove any existing OTEL handlers to avoid duplicates
            logger.handlers = [h for h in logger.handlers if not isinstance(h, LoggingHandler)]
            
            # Add OTEL handler with trace context
            logger.addHandler(self.otel_handler)
            
            # Add trace context attributes to logs
            try:
                # Get trace and span IDs for correlation
                trace_id_str = gen_trace_id(dag_run=ti.dag_run)
                span_id_str = gen_span_id(ti=ti)
                
                # Set context in logger for OTEL correlation
                # This allows logs to be linked to traces/spans
                self._set_trace_context(logger, trace_id_str, span_id_str, ti)
            except Exception as e:
                log.warning(f"Failed to set trace context for task logs: {e}")

    def _set_trace_context(self, logger, trace_id_str: str, span_id_str: str, ti: TaskInstance):
        """
        Set trace context for log correlation.
        
        :param logger: Logger instance
        :param trace_id_str: Trace ID as hex string
        :param span_id_str: Span ID as hex string
        :param ti: TaskInstance
        """
        # Add a filter to inject trace context into log records
        class TraceContextFilter(logging.Filter):
            def __init__(self, trace_id: str, span_id: str, task_instance: TaskInstance):
                super().__init__()
                self.trace_id = trace_id
                self.span_id = span_id
                self.task_instance = task_instance
            
            def filter(self, record):
                # Add trace context to the record
                record.otel_trace_id = self.trace_id
                record.otel_span_id = self.span_id
                record.dag_id = self.task_instance.dag_id
                record.task_id = self.task_instance.task_id
                record.execution_date = str(self.task_instance.execution_date)
                record.try_number = self.task_instance.try_number
                return True
        
        # Remove any existing trace context filters
        logger.filters = [f for f in logger.filters if not isinstance(f, TraceContextFilter)]
        
        # Add new trace context filter
        logger.addFilter(TraceContextFilter(trace_id_str, span_id_str, ti))

    def close(self):
        """Close the handler and flush any pending logs."""
        if self.otel_enabled and self.logger_provider:
            try:
                self.logger_provider.force_flush()
            except Exception as e:
                log.warning(f"Failed to flush OTEL logs: {e}")
        
        super().close()

    def __del__(self):
        """Cleanup when handler is destroyed."""
        self.close()

