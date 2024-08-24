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

def get_provider_info():
    return {
        "package-name": "airflow_provider_opentelemetry",
        "name": "Opentelemetry provider for Airflow",
        "description": "Opentelemetry provider to produce Spans, Metrics within the DAG code",
        "versions": ["1.0.0"],
        "hooks": ["airflow_provider_opentelemetry.hooks.otel.OtelHook"],
        "operators": [],
        "sensors": [],
        "listeners": ["airflow_provider_opentelemetry.plugins.otel_listener.OpenTelemetryListener"],
        "connection_types": [
            {
                "hook-class-name": "airflow.providers.opentelemetry.hooks.otel.OtelHook",
                "connection-type": "opentelemetry",
            }
        ]
    }