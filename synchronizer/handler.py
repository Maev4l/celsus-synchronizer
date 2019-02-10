import json
import logging
import os
from contextlib import closing
import uuid
from datetime import datetime, timezone


import psycopg2


from synchronizer.utils import makeResponse
from synchronizer.libraries import handle_libraries_sync
from synchronizer.books import (
    handle_books_begin_sync, handle_books_sync, handle_books_end_sync, cleanup_old_sync)

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
    session: <sync session id>
    pagesCount: <number of pages for updated/created books>
    libraries: [<created/updated libraries>],
    deletedLibraries: [<deleted libraries identifiers>],
    deletedBooks: [<deleted books identifiers>]
}
"""


def begin_synchronize(event, context):
    try:
        with closing(getConnection()) as connection:

            user_id = event['requestContext']['authorizer']['claims']['sub']
            payload = json.loads(event['body'])

            schema = os.environ['PGSCHEMA']

            synchronization_session_id = str(uuid.uuid4()).replace('-', '')

            response = {
                'session': synchronization_session_id,
                'deletedLibraries': [],
                'libraries': [],
                'deletedBooks': []
            }

            sync_libraries_result = handle_libraries_sync(connection=connection,
                                                          user_id=user_id,
                                                          payload=payload,
                                                          schema=schema)
            response['deletedLibraries'] = sync_libraries_result['deletedLibraries']
            response['libraries'] = sync_libraries_result['libraries']

            sync_books_result = handle_books_begin_sync(connection=connection,
                                                        sync_session=synchronization_session_id,
                                                        timestamp=datetime.now(
                                                            timezone.utc),
                                                        user_id=user_id,
                                                        payload=payload,
                                                        schema=schema)

            connection.commit()

            response['deletedBooks'] = sync_books_result['deletedBooks']
            response['pagesCount'] = sync_books_result['pagesCount']

            result = makeResponse(201, response)
            return result

    except psycopg2.Error as e:
        logger.error(f"Synchronize error: {e}")
        return makeResponse(500, {'message': str(e)})


"""
The response looks like:
{
    page: current returned page
    addedBooks: [<added books>],
    updatedBooks: [<updated books>],
}
"""


def synchronize(event, context):
    try:
        with closing(getConnection()) as connection:
            synchronization_session_id = event['pathParameters']['session']
            query_params = event['queryStringParameters']
            page = int(query_params['page']) if query_params['page'] else 1

            schema = os.environ['PGSCHEMA']

            sync_books_result = handle_books_sync(connection=connection,
                                                  sync_session=synchronization_session_id,
                                                  page=page,
                                                  schema=schema)
            response = {
                'page': sync_books_result['page'],
                'addedBooks': sync_books_result['addedBooks'],
                'updatedBooks': sync_books_result['updatedBooks'],
            }

            result = makeResponse(200, response)
            return result

    except psycopg2.Error as e:
        logger.error(f"Synchronize error: {e}")
        return makeResponse(500, {'message': str(e)})


def end_synchronize(event, context):
    try:
        with closing(getConnection()) as connection:
            synchronization_session_id = event['pathParameters']['session']

            schema = os.environ['PGSCHEMA']

            handle_books_end_sync(connection=connection,
                                  sync_session=synchronization_session_id,
                                  schema=schema)

            connection.commit()

            result = makeResponse(204, '')
            return result

    except psycopg2.Error as e:
        logger.error(f"Synchronize error: {e}")
        return makeResponse(500, {'message': str(e)})


def cleanup(event, context):
    try:
        with closing(getConnection()) as connection:
            schema = os.environ['PGSCHEMA']

            # Cleanup older synchronization which may have failed
            cleanup_old_sync(connection=connection, schema=schema)

            connection.commit()

    except psycopg2.Error as e:
        logger.error(f"Cleanup error: {e}")
