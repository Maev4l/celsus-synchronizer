from contextlib import closing
from psycopg2.extras import execute_values, NamedTupleCursor

from synchronizer.utils import get_attribute


def handle_books_sync(connection, user_id, payload, schema):
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
        query_updated_books = f'SELECT B.*, T."id" as "local_id" FROM ({sub_query}) B ' \
            f'LEFT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE B."hash" <> T."hash"'

        # Query to return the added books on the server
        query_added_books = f'SELECT B.*, T."id" as "local_id" FROM ({sub_query}) B ' \
            f'LEFT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE T."id" IS NULL'

        # Query to return the deleted books on the server
        query_deleted_books = f'SELECT B.*, T."id" as "local_id" FROM ({sub_query}) B ' \
            f'RIGHT OUTER JOIN {tmp_table_name} T ON B."id" = T."id" WHERE B."id" IS NULL'

        # 3. populate the result
        query = f'{query_updated_books} UNION {query_added_books} UNION {query_deleted_books}'
        cursor.execute(query)

        result = {
            'deletedBooks': [],
            'addedBooks': [],
            'updatedBooks': []
        }

        for record in cursor:
            if record.id is None:
                # That means the book has been removed in the server database
                result['deletedBooks'].append(record.local_id)
            else:
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
                    'bookSet': record.book_set
                }

                if (record.local_id is None):
                    # That means the book has been added in the server database
                    result['addedBooks'].append(book)
                else:
                    # That means the book has been updated in the server database
                    result['updatedBooks'].append(book)

        return result
