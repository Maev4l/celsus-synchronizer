from contextlib import closing
from psycopg2.extras import execute_values, NamedTupleCursor
from math import ceil
from synchronizer.utils import get_attribute


BOOKS_PER_PAGE = 10


def cleanup_old_sync(connection, schema):
    with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
        query = f'DELETE FROM "{schema}"."book_synchronization" ' \
                f'WHERE "ts" < now() at time zone \'utc\' - interval \'1 day\''
        cursor.execute(query)


def handle_books_begin_sync(connection, sync_session, timestamp, user_id, payload, schema):
    with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
        # 1. Insert all books identifiers into a temporary table
        tmp_table_name = 'books_identifiers_tmp'
        cursor.execute(
            f'CREATE TEMPORARY TABLE "{tmp_table_name}" '
            '("id" VARCHAR(36) NOT NULL,'
            '"hash" VARCHAR(64))'
        )

        # Change the list of books (identifiers, hash) into a list of
        # tuples
        books_identifiers_hash = list(
            map(lambda b: (b['id'], b['hash']),
                get_attribute(payload, 'books', [])))
        execute_values(cursor,
                       f'INSERT INTO "{tmp_table_name}" ("id","hash") VALUES %s',
                       books_identifiers_hash,
                       template=None,
                       page_size=1000
                       )

        # 2. Execute the diff query
        # Sub query to filter out the books for the given user
        sub_query = f'SELECT * FROM "{schema}"."book" WHERE "user_id"=\'{user_id}\''

        # Query to return the updated books on the server
        query_updated_books = f'SELECT \'{sync_session}\', \'{timestamp}\', ' \
            f'B.*, T."id" AS "local_id" FROM ({sub_query}) B ' \
            f'LEFT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE B."hash" <> T."hash"'

        # Insert the updated book in the synchronization table for further queries
        query = f'INSERT INTO "{schema}"."book_synchronization" ("session", "ts", ' \
            f'"id", "user_id", "library_id","title", "description", "isbn10", "isbn13", ' \
            f'"thumbnail", "authors", "tags", "hash", "language", "book_set", "book_set_order", ' \
            f'"local_id") ' \
            f'({query_updated_books})'
        cursor.execute(query)

        # Query to return the added books on the server
        query_added_books = f'SELECT \'{sync_session}\', \'{timestamp}\',' \
            f'B.*, T."id" AS "local_id" FROM ({sub_query}) B ' \
            f'LEFT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE T."id" IS NULL'

        # Insert the added book in the synchronization table for further queries
        query = f'INSERT INTO "{schema}"."book_synchronization" ("session", "ts", ' \
            f'"id", "user_id", "library_id","title", "description", "isbn10", "isbn13", ' \
            f'"thumbnail", "authors", "tags", "hash", "language", "book_set", "book_set_order", ' \
            f'"local_id") ' \
            f'({query_added_books})'
        cursor.execute(query)

        # Query to return the deleted books on the server
        query_deleted_books = f'SELECT B.*, T."id" AS "local_id" FROM ({sub_query}) B ' \
            f'RIGHT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE B."id" IS NULL'

        result = {
            'deletedBooks': [],
            'pagesCount': 0,
        }

        # 3. populate the result
        # Get the total number of added / updated books
        query = f'SELECT COUNT(*) AS books_count FROM "{schema}"."book_synchronization" '\
                f'WHERE "session"=%s'
        cursor.execute(query, (sync_session,))
        for record in cursor:
            result['pagesCount'] = ceil(record.books_count / BOOKS_PER_PAGE)

        # Get the deleted books
        cursor.execute(query_deleted_books)

        for record in cursor:
            result['deletedBooks'].append(record.local_id)

        return result


def handle_books_sync(connection, sync_session, page, schema):
    with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
        query = f'SELECT * FROM "{schema}"."book_synchronization" B WHERE "session"=%s ' \
                f'ORDER BY B."title", B."id" ' \
                f'LIMIT {BOOKS_PER_PAGE} OFFSET {(page-1) * BOOKS_PER_PAGE}'
        cursor.execute(query, (sync_session,))
        result = {
            'page': page,
            'addedBooks': [],
            'updatedBooks': []
        }

        for record in cursor:
            book = {
                'id': record.id,
                'libraryId': record.library_id,
                'title': record.title,
                'description': record.description,
                'isbn10': record.isbn10,
                'isbn13': record.isbn13,
                'thumbnail': record.thumbnail,
                'tags': record.tags if record.tags is not None else [],
                'authors': record.authors if record.authors is not None else [],
                'hash': record.hash,
                'language': record.language,
                'bookSet': record.book_set,
                'bookSetOrder': record.book_set_order
            }

            if (record.local_id is None):
                # That means the book has been added in the server database
                result['addedBooks'].append(book)
            else:
                # That means the book has been updated in the server database
                result['updatedBooks'].append(book)

        return result


def handle_books_end_sync(connection, sync_session, schema):
    with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
        query = f'DELETE FROM "{schema}"."book_synchronization" WHERE "session"=%s'
        cursor.execute(query, (sync_session,))
