# OpenTelemetry Logging Provider - Quick Start Guide

This guide will help you quickly set up and start using the OpenTelemetry Logging Provider for Apache Airflow.

## Prerequisites

- Apache Airflow 2.8.0 or higher
- Python 3.8 or higher
- Access to an OpenTelemetry collector or observability platform
- The airflow-provider-opentelemetry package installed

## 5-Minute Setup

### Step 1: Install the Provider

```bash
pip install ./airflow_provider_opentelemetry
```

### Step 2: Configure OTEL Endpoint

Choose one of the following methods:

#### Method A: Environment Variables (Simplest)

```bash
export OTEL_EXPORTER_OTLP_ENDPOINT=http://localhost:4318
export OTEL_SERVICE_NAME=Airflow
```

#### Method B: Airflow Configuration (Recommended for Production)

Edit your `airflow.cfg`:

```ini
[traces]
otel_on = True
otel_host = localhost
otel_port = 4318
otel_ssl_active = False
otel_service = Airflow
```

### Step 3: Enable OTEL Logging

Edit your `airflow.cfg`:

```ini
[logging]
logging_config_class = airflow_provider_opentelemetry.log_handlers.otel_logging_config.OTEL_LOGGING_CONFIG
```

### Step 4: Restart Airflow

```bash
# Stop existing Airflow processes
pkill -f airflow

# Start Airflow
airflow webserver -D
airflow scheduler -D
```

### Step 5: Test with Example DAG

Copy the example DAG to your DAGs folder:

```bash
cp airflow_provider_opentelemetry/examples/example_otel_logging_dag.py $AIRFLOW_HOME/dags/
```

Trigger the DAG:

```bash
airflow dags trigger example_otel_logging
```

### Step 6: Verify

1. Check Airflow logs for initialization message:
   ```
   OpenTelemetry task logging initialized successfully
   ```

2. Check your OTEL backend (e.g., Honeycomb, Jaeger, Grafana) for:
   - Log records from your DAG tasks
   - Correlation between traces and logs via trace_id and span_id

## What You Get

With OTEL logging enabled, you automatically get:

✅ **Task logs sent to OTEL** - All task execution logs are sent to your OTEL collector

✅ **Trace correlation** - Logs are automatically linked to traces and spans

✅ **Rich context** - Every log includes dag_id, task_id, execution_date, try_number

✅ **Backward compatibility** - File-based logging continues to work as before

✅ **Zero code changes** - Existing DAGs work without modification

## Using in Your DAGs

### Basic Usage (No Code Changes Required)

```python
from airflow import DAG
from airflow.operators.python import PythonOperator
import logging

def my_task():
    logger = logging.getLogger(__name__)
    logger.info("This log automatically goes to OTEL!")
    # Your task logic here

with DAG('my_dag', ...) as dag:
    task = PythonOperator(task_id='my_task', python_callable=my_task)
```

### Advanced Usage with Custom Spans

```python
from airflow_provider_opentelemetry.hooks.otel import OtelHook
from airflow.decorators import task
import logging

@task
def advanced_task(**context):
    otel_hook = OtelHook()
    logger = logging.getLogger(__name__)
    
    with otel_hook.start_as_current_span("custom_operation", dag_context=context):
        logger.info("Log correlated with custom span")
        # Your task logic here
```

## Troubleshooting

### Logs not appearing in OTEL backend?

1. Verify endpoint connectivity:
   ```bash
   curl -X POST http://your-otel-endpoint:4318/v1/logs
   ```

2. Check Airflow logs for errors:
   ```bash
   grep -i "otel" $AIRFLOW_HOME/logs/scheduler/latest/*.log
   ```

3. Verify configuration:
   ```bash
   airflow config get-value logging logging_config_class
   ```

### Logs missing trace correlation?

- Ensure OTEL traces are enabled (either via Airflow native support or OTEL connection)
- Restart Airflow after configuration changes
- Check that the OTEL hook is properly initialized

## Next Steps

- 📖 Read the full [README.md](README.md) for comprehensive documentation
- 🔧 See [airflow_otel_logging_config_example.cfg](airflow_provider_opentelemetry/log_handlers/airflow_otel_logging_config_example.cfg) for advanced configuration
- 💡 Explore [example_otel_logging_dag.py](airflow_provider_opentelemetry/examples/example_otel_logging_dag.py) for usage patterns
- 🎯 Configure your observability platform to query logs by `trace_id` and `span_id`

## Common Observability Platform Configurations

### Honeycomb

```ini
[traces]
otel_on = True
otel_host = api.honeycomb.io
otel_port = 443
otel_ssl_active = True
otel_service = Airflow
```

```bash
export OTEL_EXPORTER_OTLP_HEADERS_API_KEY_NAME=x-honeycomb-team
export OTEL_EXPORTER_OTLP_HEADERS_API_KEY=your-api-key
```

### Grafana Cloud

```ini
[traces]
otel_on = True
otel_host = otlp-gateway-prod-us-central-0.grafana.net
otel_port = 443
otel_ssl_active = True
otel_service = Airflow
```

```bash
export OTEL_EXPORTER_OTLP_HEADERS_API_KEY_NAME=Authorization
export OTEL_EXPORTER_OTLP_HEADERS_API_KEY="Basic <base64-credentials>"
```

### Jaeger (Local)

```ini
[traces]
otel_on = True
otel_host = localhost
otel_port = 4318
otel_ssl_active = False
otel_service = Airflow
```

## Support

- 🐛 Report issues: [GitHub Issues](https://github.com/yourusername/airflow_otel_provider/issues)
- 💬 Ask questions: [Airflow Slack](https://apache-airflow.slack.com/)
- 📚 Documentation: [README.md](README.md)

## Quick Reference Card

| What | How |
|------|-----|
| Enable OTEL Logging | Set `logging_config_class` in airflow.cfg |
| Configure Endpoint | Use `[traces]` section, env vars, or OTEL connection |
| View Logs in OTEL | Query by `trace_id`, `span_id`, `dag_id`, or `task_id` |
| Custom Spans | Use `otel_hook.start_as_current_span()` |
| Explicit OTEL Logs | Use `otel_hook.otellog()` |
| Check Status | Look for "OpenTelemetry task logging initialized" |
| Restart Required | Yes, after config changes |
| Code Changes Required | No, for basic logging |

---

**Happy Observability! 🎉**

