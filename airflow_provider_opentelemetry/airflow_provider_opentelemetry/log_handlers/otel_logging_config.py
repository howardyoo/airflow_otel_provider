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
"""
Configuration and utilities for OpenTelemetry logging integration.

This module provides configuration templates and helper functions for setting up
OpenTelemetry logging in Apache Airflow.
"""
from __future__ import annotations

# Default configuration template for airflow.cfg
AIRFLOW_OTEL_LOGGING_CONFIG = """
[logging]
# Use the OpenTelemetry task handler for task logs
task_log_reader = task
remote_logging = False
logging_config_class = airflow_provider_opentelemetry.log_handlers.otel_logging_config.OTEL_LOGGING_CONFIG

# OpenTelemetry endpoint configuration (alternative to connection-based config)
# These are used when Airflow's native OTEL traces are not enabled
# OTEL_EXPORTER_OTLP_ENDPOINT = http://localhost:4318
# OTEL_SERVICE_NAME = Airflow
# OTEL_EXPORTER_OTLP_HEADERS_API_KEY_NAME = x-api-key
# OTEL_EXPORTER_OTLP_HEADERS_API_KEY = your-api-key-here
"""

# Python logging configuration dict for OTEL integration
OTEL_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'airflow': {
            'format': '[%(asctime)s] {%(filename)s:%(lineno)d} %(levelname)s - %(message)s'
        },
        'otel': {
            'format': '%(asctime)s [%(levelname)s] [trace_id=%(otel_trace_id)s span_id=%(otel_span_id)s] %(name)s - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'filters': {
        'mask_secrets': {
            '()': 'airflow.utils.log.secrets_masker.SecretsMasker',
        },
    },
    'handlers': {
        'console': {
            'class': 'airflow.utils.log.logging_mixin.RedirectStdHandler',
            'formatter': 'airflow',
            'stream': 'sys.stdout',
            'filters': ['mask_secrets'],
        },
        'task': {
            'class': 'airflow_provider_opentelemetry.log_handlers.otel_task_handler.OtelTaskHandler',
            'formatter': 'airflow',
            'base_log_folder': '{{ AIRFLOW_HOME }}/logs',
            'filters': ['mask_secrets'],
        },
        'processor': {
            'class': 'airflow.utils.log.file_processor_handler.FileProcessorHandler',
            'formatter': 'airflow',
            'base_log_folder': '{{ AIRFLOW_HOME }}/logs',
            'filename_template': '{{ filename }}.log',
            'filters': ['mask_secrets'],
        },
    },
    'loggers': {
        'airflow.processor': {
            'handlers': ['processor'],
            'level': 'INFO',
            'propagate': False,
        },
        'airflow.task': {
            'handlers': ['task'],
            'level': 'INFO',
            'propagate': False,
            'qualname': 'airflow.task',
        },
        'flask_appbuilder': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}


def get_otel_logging_config():
    """
    Get the OpenTelemetry logging configuration dict.
    
    This function can be used in airflow.cfg as:
    logging_config_class = airflow_provider_opentelemetry.log_handlers.otel_logging_config.get_otel_logging_config
    
    :return: Logging configuration dictionary
    """
    return OTEL_LOGGING_CONFIG

