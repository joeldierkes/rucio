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

from inspect import getfullargspec

import pytest

from rucio.common.exception import InputValidationError
from rucio.db.sqla.session import (NullPool, QueuePool, SingletonThreadPool,
                                   _get_engine_poolclass, get_session,
                                   read_session, stream_session,
                                   transactional_session)


def test_db_connection():
    """ DB (CORE): Test db connection """
    session = get_session()
    if session.bind.dialect.name == 'oracle':
        session.execute('select 1 from dual')
    else:
        session.execute('select 1')
    session.close()


def test_config_poolclass():
    assert _get_engine_poolclass('nullpool') is NullPool
    assert _get_engine_poolclass('queuepool') is QueuePool
    assert _get_engine_poolclass('singletonthreadpool') is SingletonThreadPool

    with pytest.raises(InputValidationError, match='Unknown poolclass: unknown'):
        _get_engine_poolclass('unknown')


@pytest.mark.parametrize("session_type", [read_session, transactional_session, stream_session])
def test_session_decorator_preserves_function_signature(session_type):
    def function(a, b, c, d=3, *, e=5, f=None):
        pass

    decorated_func = session_type(function)

    assert getfullargspec(function) == getfullargspec(decorated_func)
