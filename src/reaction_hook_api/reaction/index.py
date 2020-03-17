import json
from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger
from botocore.client import BaseClient
import os
import boto3

logger = MyLogger(__name__)


@lambda_auto_logging('SNS_TOPIC_ARN')
def handler(event, context):
    try:
        main(event)
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
    return create_result(event)


def create_result(event: dict) -> dict:
    return {
        'statusCode': 200,
        'header': {
            'Content-Type': 'application/json'
        },
        'body': json.dumps({
            'challenge': json.loads(event['body']).get('challenge')
        })
    }


def main(event: dict, ssm_client: BaseClient = boto3.client('ssm'), sns_client: BaseClient = boto3.client('sns')) -> None:
    target_channel_id = get_target_channel_id(ssm_client)
    if has_target_id(event, target_channel_id):
        topic_arn = get_sqs_url()
        send_message(event, topic_arn, sns_client)


def get_target_channel_id(ssm_client: BaseClient) -> str:
    option = {
        'Name': '/FukuokaDeLongiBot/Application/TargetChannelId'
    }
    resp = ssm_client.get_parameter(**option)

    logger.info('get target channel id result', option=option, response=resp)

    return resp['Parameter']['Value']


def has_target_id(event: dict, target_channel_id: str) -> bool:
    return event['body'].find(f'"channel":"{target_channel_id}"') > 0


def get_sqs_url() -> str:
    return os.environ['SQS_URL']


def send_message(event: dict, sns_topic_arn: str, sns_client: BaseClient) -> None:
    option = {
        'TopicArn': sns_topic_arn,
        'Message': event['body']
    }
    resp = sns_client.publish(**option)
    logger.info('send message result', option=option, response=resp)
