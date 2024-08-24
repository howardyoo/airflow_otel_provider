# airflow_otel_provider
Airflow Provider for OpenTelemetry

## How to install the provider
You can install the opentelemetry provider using pip:
```
pip install ./airflow_provider_opentelemetry
```

## How to use the OTEL Hook
You can use `span` decorator to indicate that a particular function would be emitting its span when running.

```
from airflow_provider_opentelemetry.hooks.otel import OtelHook

...

    @OtelHook.span
    def setup():
        span = trace.get_current_span()
        span.set_attribute('app.msg', 'sleeping for 1 second')
        time.sleep(1)

    # simple setup operator in python
    t0 = PythonOperator(
        task_id="setup",
        python_callable=setup
    )

```

You can also use a special parameter called `dag_context` to receive the DAG run's context as input of the function, to initiate a new span.

```
from airflow_provider_opentelemetry.hooks.otel import OtelHook

...

    def setup(**dag_context):
        with otel_hook.start_as_current_span(name="do_setup", dag_context=dag_context) as s:
            s.set_attribute("data quality", "fair")
            s.set_attribute("description", "You can add attributes in otel hook to have business or data specific details on top of existing task instnace span.")
            with otel_hook.start_as_current_span(name="do_sleep") as ss:
                ss.set_attribute("sleep for", "one second")
                time.sleep(1)

    # simple setup operator in python
    t0 = PythonOperator(
        task_id="setup",
        python_callable=setup
    )
```
