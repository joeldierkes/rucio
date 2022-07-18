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

import json
from pathlib import Path
from typing import IO, Any, TypeVar, Iterable, Callable, Dict, List, Union

from .models import ReportDict


_T = TypeVar('_T')
_K = TypeVar('_K')


def group_by(iterable: Iterable[_T], key: Callable[[_T], _K]) -> Dict[_K, List[_T]]:
    result: Dict[_K, List[_T]] = {}
    for elem in iterable:
        k = key(elem)
        result.setdefault(k, []).append(elem)
    return result


def load_json(path: Path) -> ReportDict:
    with open(path, 'r') as f:
        return json.load(f)


def save_json(out: Union[Path, IO[str]], data: Dict[str, Any]) -> None:
    if isinstance(out, Path):
        with open(out, 'w') as f:
            save_json(f, data)
    else:
        json.dump(data, out, indent=4)
        out.write('\n')
