import json


def makeResponse(statusCode, body):
    return {
        'statusCode': statusCode,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Credentials': 'true',
        },
        'body': json.dumps(body)
    }


def get_attribute(data, attribute, default_value):
    return data.get(attribute) or default_value
