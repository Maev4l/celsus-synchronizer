import pytest
import os
import psycopg2
from psycopg2.extras import NamedTupleCursor
from contextlib import closing

import synchronizer.handler as handler
from fixtures import provision_database  # noqa: F401


@pytest.mark.usefixtures('provision_database')
class TestCleanupSynchronization(object):
    def test_cleanup(self):
        hostname = os.environ['PGHOST']
        port = os.environ['PGPORT']
        database = os.environ['PGDATABASE']
        user = os.environ['PGUSER']
        schema = os.environ['PGSCHEMA']
        password = os.environ['PGPASSWORD']

        connection = psycopg2.connect(
            host=f'{hostname}',
            port=f'{port}',
            database=f'{database}',
            user=f'{user}',
            password=f'{password}'
        )

        handler.cleanup(None, None)

        with closing(connection):
            with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
                cursor.execute(
                    f'SELECT COUNT(*) AS outdated_count FROM "{schema}"."book_synchronization"')
                for record in cursor:
                    assert record.outdated_count == 1

                cursor.execute(
                    f'SELECT "session" FROM "{schema}"."book_synchronization"')
                for record in cursor:
                    assert record.session == "session--002"
