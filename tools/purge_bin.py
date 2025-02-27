#!/usr/bin/env python
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

import sys
import os.path
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(base_path)
os.chdir(base_path)

from rucio.db.sqla.session import get_session  # noqa: E402

# Exit statuses
OK, WARNING, CRITICAL, UNKNOWN = 0, 1, 2, 3


def purge_bin():
    try:
        session = get_session()
        sql = "select table_name from user_tables"
        for table in session.execute(sql):
            query = "drop table %s cascade constraints purge" % table[0]
            session.execute(query)
    except:
        pass
    finally:
        session.remove()


if __name__ == "__main__":
    purge_bin()
