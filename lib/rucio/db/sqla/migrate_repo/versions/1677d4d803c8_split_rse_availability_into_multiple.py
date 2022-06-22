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

""" split rse availability into multiple """

import sqlalchemy as sa
from alembic import context
from alembic.op import add_column, drop_column, get_bind

from rucio.common.utils import Availability
from rucio.db.sqla.types import GUID

# Alembic revision identifiers
revision = "1677d4d803c8"
down_revision = "fe1a65b176c9"


SCHEMA = context.get_context().version_table_schema if context.get_context().version_table_schema else ""

OLD_RSE = sa.sql.table(
    "rses",
    sa.Column("id", GUID()),
    sa.Column("availability", sa.Integer),
    schema=SCHEMA,
)

NEW_RSE = sa.sql.table(
    "rses",
    sa.Column("id", GUID()),
    sa.Column("availability_read", sa.Boolean),
    sa.Column("availability_write", sa.Boolean),
    sa.Column("availability_delete", sa.Boolean),
    schema=SCHEMA,
)


def upgrade():
    """
    Upgrade the database to this revision
    """

    conn = get_bind()
    if context.get_context().dialect.name in ["oracle", "mysql", "postgresql"]:
        add_column("rses", sa.Column("availability_read", sa.Boolean), schema=SCHEMA)
        add_column("rses", sa.Column("availability_write", sa.Boolean), schema=SCHEMA)
        add_column("rses", sa.Column("availability_delete", sa.Boolean), schema=SCHEMA)

        conn = get_bind()
        rses = conn.execute(OLD_RSE.select()).fetchall()

        transformed_rses = [
            {
                "rse_id": rse.id,
                "availability_read": Availability.from_integer(rse.availability).read,
                "availability_write": Availability.from_integer(rse.availability).write,
                "availability_delete": Availability.from_integer(rse.availability).delete,
            }
            for rse in rses
        ]

        if transformed_rses:
            conn.execute(
                NEW_RSE.update()
                .where(NEW_RSE.c.id == sa.bindparam("rse_id"))
                .values(
                    {
                        "availability_read": sa.bindparam("availability_read"),
                        "availability_write": sa.bindparam("availability_write"),
                        "availability_delete": sa.bindparam("availability_delete"),
                    }
                ),
                transformed_rses,
            )

        drop_column("rses", "availability", schema=SCHEMA)


def downgrade():
    """
    Downgrade the database to the previous revision
    """

    if context.get_context().dialect.name in ["oracle", "mysql", "postgresql"]:
        add_column("rses", sa.Column("availability", sa.Integer), schema=SCHEMA)

        conn = get_bind()
        rses = conn.execute(NEW_RSE.select()).fetchall()

        transformed_rses = [
            {
                "rse_id": rse.id,
                "availability": Availability(
                    rse.availability_read,
                    rse.availability_write,
                    rse.availability_delete,
                ).integer,
            }
            for rse in rses
        ]

        if transformed_rses:
            conn.execute(
                OLD_RSE.update()
                .where(OLD_RSE.c.id == sa.bindparam("rse_id"))
                .values(
                    {
                        "availability": sa.bindparam("availability"),
                    }
                ),
                transformed_rses,
            )

        drop_column("rses", "availability_read", schema=SCHEMA)
        drop_column("rses", "availability_write", schema=SCHEMA)
        drop_column("rses", "availability_delete", schema=SCHEMA)
