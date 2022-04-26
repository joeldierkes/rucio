# -*- coding: utf-8 -*-
# Copyright CERN since 2014
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

"""
Abacus-Account is a daemon to update Account counters.
"""

import logging
import os
import socket
import threading
import time
import traceback

import rucio.db.sqla.util
from rucio.common import exception
from rucio.common.logging import formatted_logger, setup_logging
from rucio.common.utils import (daemon_sleep,
                                get_thread_with_periodic_running_function)
from rucio.core.account_counter import (fill_account_counter_history_table,
                                        get_updated_account_counters,
                                        update_account_counter)
from rucio.core.heartbeat import die, live, sanity_check

graceful_stop = threading.Event()


def account_update(once=False, sleep_time=10):
    """
    Main loop to check and update the Account Counters.
    """

    # Make an initial heartbeat so that all abacus-account daemons have the correct worker number on the next try
    executable = 'abacus-account'
    hostname = socket.gethostname()
    pid = os.getpid()
    current_thread = threading.current_thread()
    live(executable=executable, hostname=hostname, pid=pid, thread=current_thread)

    while not graceful_stop.is_set():
        try:
            # Heartbeat
            heartbeat = live(executable=executable, hostname=hostname, pid=pid, thread=current_thread)

            prepend_str = 'account_update[%i/%i] : ' % (heartbeat['assign_thread'], heartbeat['nr_threads'])
            logger = formatted_logger(logging.log, prepend_str + '%s')

            # Select a bunch of rses for to update for this worker
            start = time.time()  # NOQA
            account_rse_ids = get_updated_account_counters(total_workers=heartbeat['nr_threads'],
                                                           worker_number=heartbeat['assign_thread'])
            logger(logging.DEBUG, 'Index query time %f size=%d' % (time.time() - start, len(account_rse_ids)))

            # If the list is empty, sent the worker to sleep
            if not account_rse_ids and not once:
                logger(logging.INFO, 'did not get any work')
                daemon_sleep(start_time=start, sleep_time=sleep_time, graceful_stop=graceful_stop)
            else:
                for account_rse_id in account_rse_ids:
                    if graceful_stop.is_set():
                        break
                    start_time = time.time()
                    update_account_counter(account=account_rse_id[0], rse_id=account_rse_id[1])
                    logger(logging.DEBUG, 'update of account-rse counter "%s-%s" took %f' % (account_rse_id[0], account_rse_id[1], time.time() - start_time))
        except Exception:
            logger(logging.ERROR, traceback.format_exc())

        if once:
            break

    logging.info('account_update: graceful stop requested')
    die(executable=executable, hostname=hostname, pid=pid, thread=current_thread)
    logging.info('account_update: graceful stop done')


def stop(signum=None, frame=None):
    """
    Graceful exit.
    """

    graceful_stop.set()


def run(once=False, threads=1, fill_history_table=False, sleep_time=10):
    """
    Starts up the Abacus-Account threads.
    """
    setup_logging()

    if rucio.db.sqla.util.is_old_db():
        raise exception.DatabaseException('Database was not updated, daemon won\'t start')

    executable = 'abacus-account'
    hostname = socket.gethostname()
    sanity_check(executable=executable, hostname=hostname)

    if once:
        logging.info('main: executing one iteration only')
        account_update(once)
    else:
        logging.info('main: starting threads')
        threads = [threading.Thread(target=account_update, kwargs={'once': once, 'sleep_time': sleep_time}) for i in
                   range(0, threads)]
        if fill_history_table:
            threads.append(get_thread_with_periodic_running_function(3600, fill_account_counter_history_table, graceful_stop))
        [t.start() for t in threads]
        logging.info('main: waiting for interrupts')
        # Interruptible joins require a timeout.
        while threads[0].is_alive():
            [t.join(timeout=3.14) for t in threads]
