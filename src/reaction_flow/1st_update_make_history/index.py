import json
import os
from datetime import datetime, timezone
from typing import Tuple

import boto3
from boto3.dynamodb.conditions import Key
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from botocore.exceptions import ClientError
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


class NotTargetError(Exception):
    pass


@lambda_auto_logging("DATA_STORE_TABLE_NAME", alert_unexpected_exception=False)
def handler(event, context):
    return main(event)


def main(
    event: dict,
    ssm_client: BaseClient = boto3.client("ssm"),
    dynamodb_resource: ServiceResource = boto3.resource("dynamodb"),
) -> dict:
    try:
        reaction, user_id, ts = parse_event(event)
        slack_config = get_slack_config(ssm_client)
        check_target_reaction(reaction, slack_config)
        slack_client = get_slack_client(slack_config)
        user_name = get_username(user_id, slack_client)
        table_name = get_table_name()
        times, amount = update_make_history(user_id, user_name, ts, table_name, dynamodb_resource)
        return create_result(user_id, ts, user_name, times, amount)
    except NotTargetError:
        raise
    except Exception as e:
        logger.error(f"Exception occurred: {e}")
        raise


def parse_event(event: dict) -> Tuple[str, str, str]:
    data = json.loads(event["Records"][0]["Sns"]["Message"])
    user_id = data["event"]["user"]
    reaction = data["event"]["reaction"]
    ts = data["event"]["item"]["ts"]
    return reaction, user_id, ts


def get_slack_config(ssm_client: BaseClient) -> dict:
    prefix = "/FukuokaDeLongiBot/Slack/"
    option = {"Path": prefix, "WithDecryption": True}
    resp = ssm_client.get_parameters_by_path(**option)
    return {x["Name"][len(prefix) :]: x["Value"] for x in resp.get("Parameters", [])}


def get_slack_client(slack_config: dict) -> WebClient:
    return WebClient(token=slack_config["SlackBotToken"])


def check_target_reaction(reaction: str, slack_config: dict) -> None:
    if reaction != slack_config["TargetReaction"]:
        raise NotTargetError()


def get_username(user_id: str, client: WebClient) -> str:
    option = {"user": user_id}
    resp = client.users_profile_get(**option)
    logger.info("get username result", option=option, respponse=resp)

    return resp.data["profile"]["real_name"]


def get_table_name() -> str:
    return os.environ["DATA_STORE_TABLE_NAME"]


def update_make_history(
    user_id: str, user_name: str, ts: str, table_name: str, dynamodb_resource: ServiceResource
) -> Tuple[int, int]:
    table = dynamodb_resource.Table(table_name)
    partition_id = "makeHistory"
    option = {
        "Key": {"partitionId": partition_id, "sortId": ts},
        "ConditionExpression": Key("partitionId").eq(partition_id) & Key("sortId").eq(ts),
        "UpdateExpression": "set #updatedAt = :updatedAt, #userName = :userName",
        "ExpressionAttributeNames": {"#updatedAt": "updatedAt", "#userName": f"{user_id}_name"},
        "ExpressionAttributeValues": {
            ":updatedAt": int(datetime.now(timezone.utc).timestamp() * 1000),
            ":userName": user_name,
        },
        "ReturnValues": "ALL_NEW",
    }

    try:
        resp = table.update_item(**option)
        logger.info("update make history result", option=option, response=resp)

        times = resp["Attributes"]["times"]
        amount = resp["Attributes"]["amount"]

        return times, amount
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            raise NotTargetError()
        raise


def create_result(user_id: str, ts: str, user_name: str, times: int, amount: int) -> dict:
    return {"user_id": user_id, "ts": ts, "user_name": user_name, "times": times, "amount": amount}
