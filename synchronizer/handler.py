import json
import logging
import os
from contextlib import closing


import psycopg2


from synchronizer.utils import makeResponse
from synchronizer.libraries import handle_libraries_sync
from synchronizer.books import handle_books_sync

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


"""
The synchronization request is a JSON object in the following structure
 {
    libraries: [<library identifiers>],
    books: [
        {id: <book identifier>, hash: <book hash value>}
    ]
}
The response looks like:
{
    libraries: [<created/updated libraries>],
    deletedLibraries: [<deleted libraries identifiers>],
    addedBooks: [<added books>],
    updatedBooks: [<updated books>],
    deletedBooks: [<deleted books identifiers>]
}
"""


def synchronize(event, context):
    try:
        with closing(getConnection()) as connection:

            user_id = event['requestContext']['authorizer']['claims']['sub']
            payload = json.loads(event['body'])

            schema = os.environ['PGSCHEMA']

            response = {
                'deletedLibraries': [],
                'libraries': [],
                'addedBooks': [],
                'updatedBooks': [],
                'deletedBooks': []
            }

            sync_libraries_result = handle_libraries_sync(connection=connection,
                                                          user_id=user_id,
                                                          payload=payload,
                                                          schema=schema)
            response['deletedLibraries'] = sync_libraries_result['deletedLibraries']
            response['libraries'] = sync_libraries_result['libraries']

            sync_books_result = handle_books_sync(connection=connection,
                                                  user_id=user_id,
                                                  payload=payload,
                                                  schema=schema)

            response['addedBooks'] = sync_books_result['addedBooks']
            response['updatedBooks'] = sync_books_result['updatedBooks']
            response['deletedBooks'] = sync_books_result['deletedBooks']

            result = makeResponse(200, response)
            return result

    except psycopg2.Error as e:
        logger.error(f"Synchronize error: {e}")
        return makeResponse(500, {'message': str(e)})
