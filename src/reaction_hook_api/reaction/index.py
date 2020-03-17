import json


def handler(event, context):
    return {
        'statusCode': 200,
        'header': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'challenge': json.loads(event['body']).get('challenge')
        })
    }
