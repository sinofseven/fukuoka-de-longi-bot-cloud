import os
from datetime import datetime, timezone

import boto3
from boto3.resources.base import ServiceResource

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    return main(event)


def main(event: dict, dynamodb_resource: ServiceResource = boto3.resource("dynamodb")) -> dict:
    table_name = get_table_name()
    reset_sack_counter(table_name, dynamodb_resource)
    return create_result(event)


def get_table_name():
    return os.environ["DATA_STORE_TABLE_NAME"]


def reset_sack_counter(table_name: str, dynamodb_resource: ServiceResource) -> None:
    table = dynamodb_resource.Table(table_name)
    option = {
        "Key": {"partitionId": "sackCounter", "sortId": "counter"},
        "UpdateExpression": "set #times = :times, #updatedAt = :updatedAt",
        "ExpressionAttributeNames": {"#times": "times", "#updatedAt": "updatedAt"},
        "ExpressionAttributeValues": {":times": 0, ":updatedAt": int(datetime.now(timezone.utc).timestamp() * 1000)},
    }
    resp = table.update_item(**option)
    logger.info("reset sack counter result", resp=resp)


def create_result(event: dict) -> dict:
    return event["responsePayload"]
