import json
import logging
import os
from contextlib import closing

import psycopg2
from psycopg2.extras import NamedTupleCursor, execute_values

logger = logging.getLogger()


def getConnection():
    hostname = os.environ['PGHOST']
    port = os.environ['PGPORT']
    database = os.environ['PGDATABASE']
    user = os.environ['PGUSER']
    password = os.environ['PGPASSWORD']

    connection = psycopg2.connect(
        host=f'{hostname}',
        port=f'{port}',
        database=f'{database}',
        user=f'{user}',
        password=f'{password}'
    )

    logger.debug(f'Connected successfully to database {database}')
    return connection


def makeResponse(body):
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        },
        'body': body
    }


"""
The synchronization request is a JSON object in the following structure
 {
    libraries: [<library identifiers>],
    books: [
        {id: <book identifier>, hash: <book hash value>}
    ]
}
"""


def synchronize(event, context):
    try:
        with closing(getConnection()) as connection:
            with closing(connection.cursor(
                cursor_factory=NamedTupleCursor)
            ) as cursor:

                response = {
                    'deletedLibraries': [],
                    'libraries': [],
                    'addeBooks': [],
                    'updatedBooks': [],
                    'deletedBooks': []
                }
                userId = event['requestContext']['authorizer']['claims']['sub']
                payload = json.loads(event['body'])

                schema = os.environ['PGSCHEMA']

                # 1. Handle libraries difference
                # 1.1. Insert all libraries identifiers into a temporary table
                tmp_table_name = 'libraries_identifiers_tmp'
                cursor.execute(
                    f'CREATE TEMPORARY TABLE "{tmp_table_name}" '
                    '("id" VARCHAR(36) NOT NULL)'
                )
                # Change the list of libraries identifiers into a list of
                # tuples with one element, the library id
                libraries_identifiers = list(
                    map(lambda l: (l,), payload['libraries']))
                execute_values(cursor,
                               f'INSERT INTO "{tmp_table_name}" ("id") VALUES %s',
                               libraries_identifiers,
                               template=None,
                               page_size=1000
                               )
                # 1.2. Execute the diff query
                query = 'SELECT L."id", L."user_id", L."name", L."description",' \
                    f'"{tmp_table_name}"."id" AS "remote_library_id" FROM "{tmp_table_name}" ' \
                    f'LEFT OUTER JOIN "{schema}"."library" L ON L."id"="{tmp_table_name}"."id" ' \
                    f'AND L."user_id"=%s ' \
                    'UNION ' \
                    f'SELECT L."id", L."user_id", L."name", L."description", ' \
                    f'"{tmp_table_name}"."id" AS "remote_library_id" FROM "{schema}"."library" L ' \
                    f'LEFT OUTER JOIN "{tmp_table_name}" ON L."id"= "{tmp_table_name}"."id" ' \
                    f'WHERE "{tmp_table_name}"."id" IS NULL AND L."user_id"=%s'

                # 1.3. populate the response
                cursor.execute(query, [userId, userId])
                for record in cursor:
                    if record.id is None:
                        response['deletedLibraries'].append(
                            record.remote_library_id)
                    else:
                        response['libraries'].append({
                            'id': record.id,
                            'userId': record.user_id,
                            'name': record.name,
                            'description': record.description
                        })

                return makeResponse(response)

    except psycopg2.Error as e:
        logger.error(f"Synchronize error: {e}")
