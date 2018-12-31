from contextlib import closing
from psycopg2.extras import execute_values, NamedTupleCursor

from synchronizer.utils import get_attribute


def handle_libraries_sync(connection, user_id, payload, schema):
    with closing(connection.cursor(cursor_factory=NamedTupleCursor)) as cursor:
        # 1. Insert all libraries identifiers into a temporary table
        tmp_table_name = 'libraries_identifiers_tmp'
        cursor.execute(
            f'CREATE TEMPORARY TABLE "{tmp_table_name}" '
            '("id" VARCHAR(36) NOT NULL)'
        )

        # Change the list of libraries identifiers into a list of
        # tuples with one element, the library id
        libraries_identifiers = list(
            map(lambda l: (l,), get_attribute(payload, 'libraries', [])))
        execute_values(cursor,
                       f'INSERT INTO "{tmp_table_name}" ("id") VALUES %s',
                       libraries_identifiers,
                       template=None,
                       page_size=1000
                       )
        # 2. Execute the diff query
        query = 'SELECT L."id", L."user_id", L."name", L."description",' \
            f'"{tmp_table_name}"."id" AS "remote_library_id" FROM "{tmp_table_name}" ' \
            f'LEFT OUTER JOIN "{schema}"."library" L ON L."id"="{tmp_table_name}"."id" ' \
            f'AND L."user_id"=%s ' \
            'UNION ' \
            f'SELECT L."id", L."user_id", L."name", L."description", ' \
            f'"{tmp_table_name}"."id" AS "remote_library_id" FROM "{schema}"."library" L ' \
            f'LEFT OUTER JOIN "{tmp_table_name}" ON L."id"= "{tmp_table_name}"."id" ' \
            f'WHERE "{tmp_table_name}"."id" IS NULL AND L."user_id"=%s'

        # 3. populate the result
        result = {
            'deletedLibraries': [],
            'libraries': []
        }
        cursor.execute(query, [user_id, user_id])
        for record in cursor:
            if record.id is None:
                # That means the library has been removed in the server database
                result['deletedLibraries'].append(
                    record.remote_library_id)
            else:
                result['libraries'].append({
                    'id': record.id,
                    'userId': record.user_id,
                    'name': record.name,
                    'description': record.description
                })

        return result
