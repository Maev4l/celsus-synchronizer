import json

import pytest

import synchronizer.handler as handler
from fixtures import provision_database  # noqa: F401
from utils import make_mock_event


@pytest.mark.usefixtures('provision_database')
class TestSynchronizeLibraries(object):

    def test_synchronize_first_time(self):
        payload = {
            'libraries': [],
            'books': []
        }

        mock_event = make_mock_event('user1', payload)
        response = handler.synchronize(mock_event, None)
        status_code = response['statusCode']
        assert status_code == 200

        body = json.loads(response['body'])

        deleted_libraries = body['deletedLibraries']
        assert len(deleted_libraries) == 0

        libraries = body['libraries']
        assert len(libraries) == 2
        libraries_id = map(lambda l: l['id'], libraries)
        assert 'af9da085-4562-475f-baa5-38c3e5115c09' in libraries_id

        for library in libraries:
            assert library['userId'] == 'user1'

    def test_synchronize_libraries(self):
        payload = {
            'libraries': [
                # Exists in the database
                'af9da085-4562-475f-baa5-38c3e5115c09',
                # Was removed from the database
                'ebbf31f3-13cd-484b-b93d-a076cc060c7a'
            ],
            'books': []
        }
        mock_event = make_mock_event('user1', payload)
        response = handler.synchronize(mock_event, None)
        body = json.loads(response['body'])

        deleted_libraries = body['deletedLibraries']
        assert 'ebbf31f3-13cd-484b-b93d-a076cc060c7a' in deleted_libraries

        libraries = body['libraries']
        assert len(libraries) == 2
        libraries_id = map(lambda l: l['id'], libraries)
        assert 'af9da085-4562-475f-baa5-38c3e5115c09' in libraries_id

        for library in libraries:
            assert library['userId'] == 'user1'
