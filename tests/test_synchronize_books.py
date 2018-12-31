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
        response = handler.synchronize(mock_event, None)

        status_code = response['statusCode']
        assert status_code == 200

        body = json.loads(response['body'])

        added_books = body['addedBooks']
        assert len(added_books) == 1
        added_book = added_books[0]
        assert added_book['id'] == '3'

        deleted_books = body['deletedBooks']
        assert len(deleted_books) == 1
        deleted_book = deleted_books[0]
        assert deleted_book == '999'

        updated_books = body['updatedBooks']
        assert len(updated_books) == 1
        updated_book = updated_books[0]
        assert updated_book['id'] == '2'
