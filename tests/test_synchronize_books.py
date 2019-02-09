import json

import pytest

import synchronizer.handler as handler
from fixtures import provision_database  # noqa: F401
from utils import make_mock_event


@pytest.mark.usefixtures('provision_database')
class TestSynchronizeBooks(object):

    def test_synchronize_books(self):
        payload = {
            'libraries': [
                # Exists in the database
                'af9da085-4562-475f-baa5-38c3e5115c09',
            ],
            'books': [
                # unchanged book
                {
                    'id': '1',
                    'hash': 'hash-1.0'
                },
                # book was changed on server
                {
                    'id': '2',
                    'hash': 'hash-2.0'
                },
                # book was removed on server
                {
                    'id': '999',
                    'hash': 'hash-999.0'
                },
            ]
        }

        mock_event = make_mock_event('user1', payload)
        response = handler.begin_synchronize(mock_event, None)

        status_code = response['statusCode']
        assert status_code == 201

        body = json.loads(response['body'])

        session = body['session']
        assert len(session) != 0

        pages_count = body['pagesCount']
        assert pages_count == 1

        deleted_books = body['deletedBooks']
        assert len(deleted_books) == 1
        deleted_book = deleted_books[0]
        assert deleted_book == '999'

        mock_event = make_mock_event('user1', payload)
        mock_event['pathParameters'] = {'session': session}
        mock_event['queryStringParameters'] = {'page': 1}
        response = handler.synchronize(mock_event, None)

        status_code = response['statusCode']
        assert status_code == 200

        body = json.loads(response['body'])

        added_books = body['addedBooks']
        assert len(added_books) == 1
        added_book = added_books[0]
        assert added_book['id'] == '3'

        updated_books = body['updatedBooks']
        assert len(updated_books) == 1
        updated_book = updated_books[0]
        assert updated_book['id'] == '2'

        mock_event = make_mock_event('user1', '')
        mock_event['pathParameters'] = {'session': session}
        response = handler.end_synchronize(mock_event, None)
        status_code = response['statusCode']
        assert status_code == 204
