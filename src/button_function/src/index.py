import os

import boto3
from botocore.client import BaseClient

from logger.decorator import lambda_auto_logging


@lambda_auto_logging("OPEN_SACK_FLOW_SNS_TOPIC_ARN", "MAKE_COFFEE_FLOW_SNS_TOPIC_ARN")
def handler(event, context):
    main(event)


def main(event: dict, sns_client: BaseClient = boto3.client("sns")):
    click_event = get_click_type(event)
    topic_arn = (
        os.environ["OPEN_SACK_FLOW_SNS_TOPIC_ARN"]
        if is_long_click(click_event)
        else os.environ["MAKE_COFFEE_FLOW_SNS_TOPIC_ARN"]
    )
    publish(click_event, topic_arn, sns_client)


def get_click_type(event: dict) -> str:
    return event["deviceEvent"]["buttonClicked"]["clickType"]


def is_long_click(click_event: str) -> bool:
    return click_event == "LONG"


def publish(payload: str, topic_arn: str, sns_client: BaseClient):
    option = {"TopicArn": topic_arn, "Message": payload}
    sns_client.publish(**option)
