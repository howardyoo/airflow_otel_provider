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

from typing import TYPE_CHECKING
from airflow.utils.hashlib_wrapper import md5
from airflow.utils.state import TaskInstanceState
from airflow.models.taskinstancekey import TaskInstanceKey
from airflow import __version__ as airflow_version

if TYPE_CHECKING:
    from airflow.models import DagRun, TaskInstance

TRACE_ID = 0
NO_TRACE_ID = 1
SPAN_ID = 16

def _gen_id(seeds: list[str], as_int: bool = False, type: int = TRACE_ID) -> str | int:
    seed_str = "_".join(seeds).encode("utf-8")
    hash_hex = md5(seed_str).hexdigest()[type:]
    return int(hash_hex, 16) if as_int else hash_hex

def get_try_number(ti: TaskInstance):
    # todo: decrese by 1 when min airflow version >= 2.10.1
    from packaging.version import parse

    if parse(parse(airflow_version).base_version) < parse("2.10.1"):
        return ti.try_number - 1
    else:
        return ti.try_number

def gen_trace_id(dag_run: DagRun, as_int: bool = False) -> str | int:
    if dag_run.start_date is None:
        return NO_TRACE_ID

    """Generate trace id from DagRun."""
    return _gen_id(
        [dag_run.dag_id, str(dag_run.run_id), str(dag_run.start_date.timestamp())],
        as_int,
    )

def gen_trace_id_from_ti_key(ti_key: TaskInstanceKey, start_date, as_int: bool = False) -> str | int:
    if start_date is None:
        return NO_TRACE_ID
    
    return _gen_id(
        [ti_key.dag_id, str(ti_key.run_id), str(start_date.timestamp())],
        as_int,
    )

def gen_span_id_from_ti_key(ti_key: TaskInstanceKey, as_int: bool = False) -> str | int:
    from packaging.version import parse
    """Generate span id from the task instance."""
    # fix: issue #1
    if parse(parse(airflow_version).base_version) == parse("2.10.0"):
        try_number = ti_key.try_number - 1
    else:
        try_number = ti_key.try_number
    return _gen_id(
        [ti_key.dag_id, ti_key.run_id, ti_key.task_id, str(try_number)],
        as_int,
        SPAN_ID,
    )

def gen_dag_span_id(dag_run: DagRun, as_int: bool = False) -> str | int:
    """Generate dag's root span id using dag_run."""
    if dag_run.start_date is None:
        return NO_TRACE_ID

    return _gen_id(
        [dag_run.dag_id, str(dag_run.run_id), str(dag_run.start_date.timestamp())],
        as_int,
        SPAN_ID,
    )

def gen_span_id(ti: TaskInstance, as_int: bool = False) -> str | int:
    from packaging.version import parse
    """Generate span id from the task instance."""
    dag_run = ti.dag_run
    if ti.state == TaskInstanceState.SUCCESS or ti.state == TaskInstanceState.FAILED:
        try_number = get_try_number(ti)
    else:
        # fix: issue #1
        if parse(parse(airflow_version).base_version) == parse("2.10.0"):
            try_number = ti.try_number - 1
        else:
            try_number = ti.try_number
    return _gen_id(
        [dag_run.dag_id, dag_run.run_id, ti.task_id, str(try_number)],
        as_int,
        SPAN_ID,
    )

def datetime_to_nano(datetime) -> int:
    """Convert datetime to nanoseconds."""
    return int(datetime.timestamp() * 1000000000)
