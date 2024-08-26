# airflow_otel_provider
Airflow Provider for OpenTelemetry

## How to install the provider
You can install the opentelemetry provider using pip:
```
pip install ./airflow_provider_opentelemetry
```

## How to use the OTEL Hook
You can use `span` decorator to indicate that a particular function would be emitting its span when running.

```python
from airflow_provider_opentelemetry.hooks.otel import OtelHook

    # get otel hook first
    otel_hook = OtelHook("otel_conn")
...

    # use hotel_hook's span decorator
    @otel_hook.span
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

```python
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

You can also submit your very own log message which then can automatically converted and linked to OTEL log record within the span context.

```python
    def setup(**dag_context):
        with otel_hook.start_as_current_span(name="do_setup", dag_context=dag_context) as s:
            s.set_attribute("data quality", "fair")
            s.set_attribute("description", "You can add attributes in otel hook to have business or data specific details on top of existing task instnace span.")
            with otel_hook.start_as_current_span(name="do_sleep") as ss:
                ss.set_attribute("sleep for", "one second")

                # emit 'info' log.
                otel_hook.otellog('info','this is an information log')

                time.sleep(1)

    # simple setup operator in python
    t0 = PythonOperator(
        task_id="setup",
        python_callable=setup
    )
```
