# airflow_otel_provider
Airflow Provider for OpenTelemetry is an Airflow provider composed of the follwing:
- OTEL hook : provides means for user to emit trace(spans), metrics, and logs within their DAG file
- OTEL listener : provides alternative means to generate trace on the DAG run

## How the provider works with Airflow
[Airflow release 2.10.0](https://airflow.apache.org/docs/apache-airflow/2.10.0/release_notes.html#opentelemetry-traces-for-apache-airflow-37948) Now has OTEL traces implemented, which means that Airflow can natively emit traces on jobs and DAG runs in OTEL format. This provider works well with the version of Airflow that has this trace enabled.

- If the airflow is enabled with traces (and sending trace data), provider's listener will be `disabled`, while otel hook would use the connection configuration not from its connection info, but directly from the airflor's otel configuration. That means users don't have to create redundant connection to it.
- If the airflow is disabled with traces or does not support traces (due to of it being older version), then provider's listener will be `enabled`, and otel hook would use the connection configuration from the connections of type `otel`.
- If the airflow does not support any traces, and connection is not defined, then provider's listener and hooks will `NOT` function.

## How to install the provider
After checking out this repo in your local env, you can install the opentelemetry provider using pip.
```
pip install ./airflow_provider_opentelemetry
```

## How to use the OTEL Hook

### configuring the connection

OTEL Connection would have the following parameters in its configuration UI:

- OTEL endpoint URL
- HTTP Header Name for API key
- API Key
- Export interval in ms(for metrics)
- disabled

#### OTEL endpoint URL
It's the URL for emitting OTEL data (in OTLP HTTP protocol). Example: http://my-otel-endpoint:4318

#### HTTP Header Name for API key (Optional)
Sometimes, the endpoint may require you to specify header name of the API Key. In that case, you may provide one.

#### API Key (Optional)
API key that is paired with the HTTP header name

#### Export internal in ms(for metrics)
As for sending metrics data, everything is sent in timed interval (e.g. every 30 seconds). This will specify that internal
in the unit of milliseconds.

#### Disabled (Optional)
This is currently NOT implemented (coming up in future), but when checked, this will effectively 'disable' the hook and listener.
You may need to restart Airflow in order for this to take action, but a great way to turn it off without deleting the connection.

### Using Otel hook inside the DAG file

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
