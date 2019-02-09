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
        response = handler.begin_synchronize(mock_event, None)
        status_code = response['statusCode']
        assert status_code == 201

        body = json.loads(response['body'])

        session = body['session']
        assert len(session) != 0

        pages_count = body['pagesCount']
        assert pages_count != 0

        deleted_libraries = body['deletedLibraries']
        assert len(deleted_libraries) == 0

        libraries = body['libraries']
        assert len(libraries) == 2
        libraries_id = map(lambda l: l['id'], libraries)
        assert 'af9da085-4562-475f-baa5-38c3e5115c09' in libraries_id

        mock_event = make_mock_event('user1', '')
        mock_event['pathParameters'] = {'session': session}
        response = handler.end_synchronize(mock_event, None)

        status_code = response['statusCode']
        assert status_code == 204

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

        response = handler.begin_synchronize(mock_event, None)
        status_code = response['statusCode']
        assert status_code == 201

        body = json.loads(response['body'])

        session = body['session']
        assert len(session) != 0

        pages_count = body['pagesCount']
        assert pages_count != 0

        deleted_libraries = body['deletedLibraries']
        assert 'ebbf31f3-13cd-484b-b93d-a076cc060c7a' in deleted_libraries

        libraries = body['libraries']
        assert len(libraries) == 2
        libraries_id = map(lambda l: l['id'], libraries)
        assert 'af9da085-4562-475f-baa5-38c3e5115c09' in libraries_id
        assert '18a10d9d-4328-4404-8a65-ec1077113bea' in libraries_id

        mock_event = make_mock_event('user1', '')
        mock_event['pathParameters'] = {'session': session}
        response = handler.end_synchronize(mock_event, None)

        status_code = response['statusCode']
        assert status_code == 204
