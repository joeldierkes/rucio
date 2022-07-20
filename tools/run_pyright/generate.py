# -*- coding: utf-8 -*-
# Copyright European Organization for Nuclear Research (CERN) since 2012
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from argparse import ArgumentParser, Namespace
from pathlib import Path
import copy
import json
import subprocess
from typing import Any, Callable, Dict

from .models import ReportDict, Report
from .utils import save_json


PATHS = (
    'lib/',
)


def setup_parser(parser: ArgumentParser) -> Callable[[Namespace], int]:
    parser.add_argument('out', type=Path, help='Store Pyright report at this path.')
    parser.add_argument('--strip', choices=['line', 'character', 'range'], help='Strip certain attributes from the output.')
    parser.add_argument('--Werror', action='store_true', help='Treat warnings as errors.')
    return generate


def generate(args: Namespace) -> int:
    """Generate a pyright-report and save it at the specified path."""
    reportdict = _run_pyright()

    if args.strip:
        reportdict = _strip_dict(reportdict, args.strip)

    save_json(args.out, reportdict)

    report = Report.from_dict(reportdict)

    num_errors = report.summary.num_errors
    if args.Werror:
        num_errors += report.summary.num_warnings

    return 1 if num_errors > 0 else 0


def _run_pyright() -> ReportDict:
    """Runs the pyright type-checker and returns its output as json."""
    cmdline = ['pyright', '--outputjson', *PATHS]
    process = subprocess.run(cmdline, stdout=subprocess.PIPE)
    return json.loads(process.stdout)


def _strip_dict(data: ReportDict, strip_mode: str) -> ReportDict:
    """Strip certain keys from each row under the `generalDiagnostics` key."""
    result = copy.deepcopy(data)

    diagnostic: Dict[str, Any]
    for diagnostic in result['generalDiagnostics']:
        if strip_mode == 'range':
            diagnostic.pop('range')
        elif strip_mode == 'line':
            diagnostic['range']['start'].pop('line')
            diagnostic['range']['end'].pop('line')
        elif strip_mode == 'character':
            diagnostic['range']['start'].pop('character')
            diagnostic['range']['end'].pop('character')

    return result
