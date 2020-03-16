import os
from datetime import datetime, timedelta, timezone

import boto3
from boto3.resources.base import ServiceResource

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    return main(event)


def main(event: dict, dynamodb_resource: ServiceResource = boto3.resource("dynamodb")) -> None:
    times = get_times(event)
    table_name = get_table_name()
    insert_sack_history(times, table_name, dynamodb_resource)


def get_table_name():
    return os.environ["DATA_STORE_TABLE_NAME"]


def get_times(event: dict) -> int:
    return event["responsePayload"]["times"]


def insert_sack_history(times: int, table_name: str, dynamodb_resouce: ServiceResource) -> None:
    table = dynamodb_resouce.Table(table_name)

    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = str(datetime.now(jst))

    option = {"Item": {"partitionId": "sackHistory", "sortId": now, "times": times}}

    resp = table.put_item(**option)
    logger.info("insert sack history result", option=option, resp=resp)
