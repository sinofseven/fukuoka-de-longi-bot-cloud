import os
from datetime import datetime, timedelta, timezone
from typing import List

import boto3
from boto3.dynamodb.conditions import Key
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    main()


def main(
    dynamodb_resource: ServiceResource = boto3.resource("dynamodb"), ssm_client: BaseClient = boto3.client("ssm")
) -> None:
    table_name = get_table_name()
    history = get_open_sack_history(table_name, dynamodb_resource)
    slack_config = get_slack_config(ssm_client)
    slack_client = get_slack_client(slack_config)
    post_message_option = create_post_message_option(history, slack_config)
    post_message(post_message_option, slack_client)


def get_table_name():
    return os.environ["DATA_STORE_TABLE_NAME"]


def get_open_sack_history(table_name: str, dynamodb_resource: ServiceResource) -> List[dict]:
    table = dynamodb_resource.Table(table_name)
    option = {
        "KeyConditionExpression": Key("partitionId").eq("sackHistory"),
        "Limit": 5,
        "ScanIndexForward": False,
        "ProjectionExpression": "#sortId, #times",
        "ExpressionAttributeNames": {"#sortId": "sortId", "#times": "times"},
    }
    resp = table.query(**option)
    logger.info("get open sack history result", option=option, response=resp)
    return resp.get("Items", [])


def get_slack_config(ssm_client: BaseClient) -> dict:
    prefix = "/FukuokaDeLongiBot/Slack/"
    option = {"Path": prefix, "WithDecryption": True}
    resp = ssm_client.get_parameters_by_path(**option)
    return {x["Name"][len(prefix) :]: x["Value"] for x in resp.get("Parameters", [])}


def get_slack_client(slack_config: dict) -> WebClient:
    return WebClient(token=slack_config["SlackBotToken"])


def create_post_message_option(sack_history: List[dict], slack_config: dict) -> dict:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")
    return {
        "username": slack_config["SendHistoryUserName"].format(now),
        "text": "\n".join(["```"] + [f'{x["sortId"]}: {x["times"]}' for x in sack_history] + ["```"]),
        "channel": slack_config["Channel"],
        "icon_emoji": slack_config["IconEmoji"],
    }


def post_message(option: dict, client: WebClient) -> None:
    resp = client.chat_postMessage(**option)
    logger.info("chat_postMessage result", response=resp.data)
