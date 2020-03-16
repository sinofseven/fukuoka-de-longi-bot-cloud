import os
from datetime import datetime, timezone
from typing import Tuple

import boto3
from boto3.resources.base import ServiceResource

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    return main(event)


def main(event: dict, dynamodb_resource: ServiceResource = boto3.resource("dynamodb")):
    amount, ts = parse_pre_function_result(event)
    table_name = get_table_name()
    item = create_make_history_item(amount, ts)
    put_make_history_item(item, table_name, dynamodb_resource)


def parse_pre_function_result(event: dict) -> Tuple[int, str]:
    response = event["responsePayload"]
    return response["amount"], response["ts"]


def create_make_history_item(amount: int, ts: str) -> dict:
    timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)
    return {
        "partitionId": "makeHistory",
        "sortId": ts,
        "isSingle": amount == 1,
        "createdAt": timestamp,
        "updatedAt": timestamp,
        "isDetected": False,
    }


def put_make_history_item(item: dict, table_name: str, dynamodb_resource: ServiceResource):
    table = dynamodb_resource.Table(table_name)
    option = {"Item": item}

    resp = table.put_item(**option)
    logger.info("put make history item", item=item, resp=resp)


def get_table_name() -> str:
    return os.environ["DATA_STORE_TABLE_NAME"]
