from setuptools import setup, find_packages

setup(
    name='airflow_provider_opentelemetry',
    version='1.0.0',
    description='Opentelemetry provider for Airflow',
    long_description='Opentelemetry provider to produce Spans, Metrics within the DAG code',
    long_description_content_type='text/markdown',
    author='Howard Yoo',
    packages=find_packages(include=['airflow_provider_opentelemetry', 'airflow_provider_opentelemetry.*']),
    install_requires=[
        'apache-airflow>=2.8.0',
        'opentelemetry-api>=1.15.0',
        'opentelemetry-exporter-otlp'
    ],
    entry_points={
        'apache_airflow_provider': [
            'provider_info=airflow_provider_opentelemetry.__init__:get_provider_info'
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: Apache Software License',
    ],
)