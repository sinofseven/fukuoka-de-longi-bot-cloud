import os
from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import BaseClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("TARGET_TOPIC_ARN")
def handler(event, context):
    main()


def main(sns_client: BaseClient = boto3.client("sns")) -> None:
    pre_month = get_pre_month()
    topic_arn = get_topic_arn()
    publish(pre_month, topic_arn, sns_client)


def get_pre_month() -> str:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = (datetime.now(jst) - timedelta(days=5)).strftime("%Y年%m月")
    return now


def get_topic_arn() -> str:
    return os.environ["TARGET_TOPIC_ARN"]


def publish(pre_month: str, topic_arn: str, sns_client: BaseClient) -> None:
    option = {"TopicArn": topic_arn, "Message": pre_month}
    resp = sns_client.publish(**option)
    logger.info("publish result", option=option, response=resp)
