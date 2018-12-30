import json


def make_mock_event(subject, body):
    mock_event = {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': subject
                }
            }
        },
        'body': json.dumps(body)
    }

    return mock_event
