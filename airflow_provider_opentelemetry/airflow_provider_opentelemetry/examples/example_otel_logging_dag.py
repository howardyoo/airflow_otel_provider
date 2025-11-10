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
Example DAG demonstrating OpenTelemetry Logging Provider.

This DAG shows how to use the OTEL logging provider with various scenarios:
1. Basic task logging that automatically goes to OTEL
2. Logging with custom spans
3. Different log levels
4. Integration with OTEL hook for traces and logs
"""
from __future__ import annotations

from datetime import datetime, timedelta
import logging
import time
import random

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.decorators import task, dag

try:
    from airflow_provider_opentelemetry.hooks.otel import OtelHook
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logging.warning("OtelHook not available. Install airflow-provider-opentelemetry to enable OTEL features.")


# Default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}


def basic_logging_task():
    """
    Demonstrate basic logging that automatically goes to OTEL.
    
    When the OTEL logging provider is enabled, all standard Python
    logging calls will automatically be sent to your OTEL collector
    with trace correlation.
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Task started - this log will be sent to OTEL")
    
    # Simulate some work
    time.sleep(1)
    
    logger.info("Processing data...")
    processed_records = random.randint(100, 1000)
    logger.info(f"Processed {processed_records} records")
    
    logger.info("Task completed successfully")
    
    return processed_records


def multi_level_logging_task():
    """
    Demonstrate different log levels.
    
    All log levels are captured and sent to OTEL with appropriate severity.
    """
    logger = logging.getLogger(__name__)
    
    logger.debug("Debug message - detailed information for troubleshooting")
    logger.info("Info message - general information about task progress")
    logger.warning("Warning message - something unexpected but not critical")
    
    try:
        # Simulate some processing that might raise an error
        risk_factor = random.random()
        if risk_factor > 0.8:
            raise ValueError("Simulated error condition")
        logger.info(f"Risk factor {risk_factor:.2f} is acceptable")
    except ValueError as e:
        logger.error(f"Error occurred: {e}", exc_info=True)
        # In production, you might want to re-raise or handle differently
    
    logger.info("Multi-level logging task completed")


@task
def logging_with_custom_spans(**context):
    """
    Demonstrate logging within custom OTEL spans.
    
    Logs within custom spans are automatically correlated with those spans,
    allowing for fine-grained observability.
    """
    if not OTEL_AVAILABLE:
        logging.warning("OTEL not available, skipping custom span example")
        return
    
    otel_hook = OtelHook()
    logger = logging.getLogger(__name__)
    
    logger.info("Starting task with custom spans")
    
    # Create a main processing span
    with otel_hook.start_as_current_span("data_validation", dag_context=context):
        logger.info("Validating input data")
        time.sleep(0.5)
        
        # Nested span for specific operation
        with otel_hook.start_as_current_span("check_data_quality"):
            logger.info("Checking data quality metrics")
            quality_score = random.uniform(0.7, 1.0)
            logger.info(f"Data quality score: {quality_score:.2f}")
            
            if quality_score < 0.8:
                logger.warning(f"Quality score {quality_score:.2f} below threshold")
        
        logger.info("Data validation completed")
    
    # Another top-level span for processing
    with otel_hook.start_as_current_span("data_processing", dag_context=context):
        logger.info("Processing validated data")
        
        for i in range(3):
            with otel_hook.start_as_current_span(f"process_batch_{i+1}"):
                logger.info(f"Processing batch {i+1}")
                time.sleep(0.3)
                records = random.randint(50, 200)
                logger.info(f"Batch {i+1} processed {records} records")
        
        logger.info("All batches processed")
    
    logger.info("Task with custom spans completed")


@task
def logging_with_otel_hook(**context):
    """
    Demonstrate using OTEL hook's otellog method alongside standard logging.
    
    The otellog method provides explicit control over log emission to OTEL,
    while standard logging goes through the logging provider.
    """
    if not OTEL_AVAILABLE:
        logging.warning("OTEL not available, skipping OTEL hook example")
        return
    
    otel_hook = OtelHook()
    logger = logging.getLogger(__name__)
    
    # Standard logging (goes through logging provider)
    logger.info("Using standard Python logging")
    
    with otel_hook.start_as_current_span("custom_operation", dag_context=context):
        # Standard logging within span
        logger.info("Inside custom span - standard logging")
        
        # OTEL hook's explicit logging method
        otel_hook.otellog('info', 'Using OTEL hook explicit log method')
        
        time.sleep(0.5)
        
        # Mix both approaches
        logger.warning("Standard warning log")
        otel_hook.otellog('warning', 'OTEL hook warning log')
        
        logger.info("Operation completed")


def error_handling_with_logging():
    """
    Demonstrate error handling with proper logging.
    
    Shows how errors are logged and captured in OTEL with full context.
    """
    logger = logging.getLogger(__name__)
    
    logger.info("Starting error handling demonstration")
    
    try:
        logger.info("Attempting risky operation")
        
        # Simulate different error scenarios
        error_type = random.choice(['none', 'value_error', 'runtime_error'])
        
        if error_type == 'value_error':
            raise ValueError("Invalid input data detected")
        elif error_type == 'runtime_error':
            raise RuntimeError("System resource unavailable")
        
        logger.info("Risky operation completed successfully")
        
    except ValueError as e:
        logger.error(f"Value error encountered: {e}", exc_info=True)
        logger.info("Applying fallback logic for value error")
        # Handle gracefully
        
    except RuntimeError as e:
        logger.error(f"Runtime error encountered: {e}", exc_info=True)
        logger.warning("Manual intervention may be required")
        # Handle gracefully or re-raise
        
    except Exception as e:
        logger.critical(f"Unexpected error: {e}", exc_info=True)
        raise  # Re-raise unexpected errors
    
    finally:
        logger.info("Error handling demonstration completed")


# Create the DAG
with DAG(
    'example_otel_logging',
    default_args=default_args,
    description='Example DAG demonstrating OpenTelemetry Logging Provider',
    schedule=None,  # Manual trigger only
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'otel', 'logging'],
) as example_dag:
    
    # Task 1: Basic logging
    t1 = PythonOperator(
        task_id='basic_logging',
        python_callable=basic_logging_task,
    )
    
    # Task 2: Multi-level logging
    t2 = PythonOperator(
        task_id='multi_level_logging',
        python_callable=multi_level_logging_task,
    )
    
    # Task 3: Logging with custom spans (using decorator)
    t3 = logging_with_custom_spans()
    
    # Task 4: Logging with OTEL hook (using decorator)
    t4 = logging_with_otel_hook()
    
    # Task 5: Error handling with logging
    t5 = PythonOperator(
        task_id='error_handling_logging',
        python_callable=error_handling_with_logging,
    )
    
    # Set task dependencies
    t1 >> t2 >> t3 >> t4 >> t5


# Optional: If you want to use the TaskFlow API exclusively
@dag(
    dag_id='example_otel_logging_taskflow',
    default_args=default_args,
    description='Example DAG using TaskFlow API with OTEL Logging',
    schedule=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['example', 'otel', 'logging', 'taskflow'],
)
def example_otel_logging_taskflow():
    """
    TaskFlow API version of the OTEL logging example.
    """
    
    @task
    def log_start():
        logger = logging.getLogger(__name__)
        logger.info("Starting OTEL logging example with TaskFlow API")
        return "started"
    
    @task
    def process_data(status: str):
        logger = logging.getLogger(__name__)
        logger.info(f"Processing data - status: {status}")
        
        records = random.randint(100, 500)
        logger.info(f"Processed {records} records")
        
        return {"status": "success", "records": records}
    
    @task
    def log_summary(result: dict):
        logger = logging.getLogger(__name__)
        logger.info(f"Task summary: {result}")
        logger.info("OTEL logging example completed")
    
    # Build the task flow
    status = log_start()
    result = process_data(status)
    log_summary(result)


# Instantiate the TaskFlow DAG
taskflow_dag = example_otel_logging_taskflow()

