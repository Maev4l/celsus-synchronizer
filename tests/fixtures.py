import pytest
import os
from subprocess import run


@pytest.fixture(scope="class")
def provision_database():
    print('Provision database')
    hostname = os.environ['PGHOST']
    port = os.environ['PGPORT']
    database = os.environ['PGDATABASE']
    user = os.environ['PGUSER']
    schema = os.environ['PGSCHEMA']

    run(['psql', f'--host={hostname}',
         f'--dbname={database}', f'--username={user}', f'--port={port}',
         '--file=./tests/scripts/initialize.sql'])
    yield
    print('Drop database')
    run(['psql', f'--host={hostname}',
         f'--dbname={database}', f'--username={user}', f'--port={port}',
         f'--command=DROP SCHEMA \"{schema}\" CASCADE'])
