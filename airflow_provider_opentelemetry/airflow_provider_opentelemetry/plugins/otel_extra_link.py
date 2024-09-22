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

import os
from airflow.models.baseoperator import BaseOperator
from airflow.models.baseoperatorlink import BaseOperatorLink
from airflow.models.taskinstancekey import TaskInstanceKey
from airflow.models.dagrun import DagRun
from airflow_provider_opentelemetry.util import gen_trace_id
from airflow_provider_opentelemetry.util import gen_span_id_from_ti_key

OTEL_TRACE_LINK = 'AIRFLOW_OTEL_TRACE_LINK'

def get_opentelemetry_links():
    links = []
    link_template = os.getenv(OTEL_TRACE_LINK, None)
    if link_template is not None:
        links.append(OtelTraceLink())
    return links

class OtelTraceLink(BaseOperatorLink):
    name = "OTEL Trace Link"

    def get_link(self, operator: BaseOperator, *, ti_key: TaskInstanceKey):
        dag_run = DagRun.find(dag_id=ti_key.dag_id, run_id=ti_key.run_id)[0]
        if dag_run is not None:
            trace_id = gen_trace_id(dag_run)
            span_id = gen_span_id_from_ti_key(ti_key)
            start_date_ts = int(dag_run.start_date.timestamp()) - 10
            end_date_ts = int(dag_run.end_date.timestamp()) + 10
            template = os.getenv(OTEL_TRACE_LINK)
            return template.format(trace_id=trace_id, span_id=span_id, start_date_ts=start_date_ts, end_date_ts=end_date_ts)