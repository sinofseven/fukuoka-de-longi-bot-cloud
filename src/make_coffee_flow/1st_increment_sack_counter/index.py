import os
from datetime import datetime, timezone

import boto3
from boto3.resources.base import ServiceResource

from logger.decorator import lambda_auto_logging


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    return main(event)


def main(event: dict, dynamodb_resource: ServiceResource = boto3.resource("dynamodb")) -> dict:
    table_name = get_table_name()
    amount = 2 if is_double(event) else 1
    current_times = update_sack_counter(amount, table_name, dynamodb_resource)
    return {"current_times": current_times, "amount": amount}


def is_double(event: dict) -> bool:
    return event["Records"][0]["Sns"]["Message"] == "DOUBLE"


def get_table_name():
    return os.environ["DATA_STORE_TABLE_NAME"]


def update_sack_counter(amount: int, table_name: str, dynamodb_resource: ServiceResource) -> int:
    table = dynamodb_resource.Table(table_name)
    option = {
        "Key": {"partitionId": "sackCounter", "sortId": "counter",},
        "UpdateExpression": "add #times :amount set #updatedAt = :updatedAt",
        "ExpressionAttributeNames": {"#times": "times", "#updatedAt": "updatedAt"},
        "ExpressionAttributeValues": {
            ":amount": amount,
            ":updatedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
        },
        "ReturnValues": "ALL_NEW",
    }
    resp = table.update_item(**option)
    return resp["Attributes"]["times"]
