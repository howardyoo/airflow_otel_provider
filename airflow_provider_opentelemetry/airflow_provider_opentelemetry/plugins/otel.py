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

from airflow.plugins_manager import AirflowPlugin
from airflow_provider_opentelemetry.hooks.otel import is_listener_enabled, is_otel_traces_enabled
from airflow_provider_opentelemetry.plugins.otel_listener import get_opentelemetry_listener
from airflow_provider_opentelemetry.plugins.otel_extra_link import get_opentelemetry_links

class OtelPlugin(AirflowPlugin):
    """provide listener for OpenTelemetry."""

    name = "OtelPlugin"
    if is_listener_enabled() and not is_otel_traces_enabled():
        listeners = [get_opentelemetry_listener()]

    global_operator_extra_links = get_opentelemetry_links()