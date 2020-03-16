import os
from datetime import datetime, timedelta, timezone

import boto3
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    return main()


def main(
    ssm_client: BaseClient = boto3.client("ssm"), dynamodb_resource: ServiceResource = boto3.resource("dynamodb")
) -> dict:
    table_name = get_table_name()
    current_times = get_current_times(table_name, dynamodb_resource)
    slack_config = get_slack_config(ssm_client)
    slack_client = get_slack_client(slack_config)
    post_message_option = create_post_message_option(current_times, slack_config)
    post_message(post_message_option, slack_client)
    return {"times": current_times}


def get_table_name():
    return os.environ["DATA_STORE_TABLE_NAME"]


def get_current_times(table_name: str, dynamodb_resource: ServiceResource) -> int:
    table = dynamodb_resource.Table(table_name)
    option = {
        "Key": {"partitionId": "sackCounter", "sortId": "counter"},
        "ProjectionExpression": "#times",
        "ExpressionAttributeNames": {"#times": "times"},
    }
    resp = table.get_item(**option)
    logger.info("get current times result", resp=resp)
    return int(resp["Item"]["times"]) if "Item" in resp else 0


def get_slack_config(ssm_client: BaseClient) -> dict:
    prefix = "/FukuokaDeLongiBot/Slack/"
    option = {"Path": prefix, "WithDecryption": True}
    resp = ssm_client.get_parameters_by_path(**option)
    return {x["Name"][len(prefix) :]: x["Value"] for x in resp.get("Parameters", [])}


def get_slack_client(slack_config: dict) -> WebClient:
    return WebClient(token=slack_config["SlackBotToken"])


def create_post_message_option(times: int, slack_config: dict) -> dict:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")

    return {
        "text": slack_config["OpenSackMessage"].format(times),
        "username": slack_config["OpenSackUserName"].format(now),
        "channel": slack_config["Channel"],
        "icon_emoji": slack_config["IconEmoji"],
    }


def post_message(option: dict, client: WebClient) -> None:
    resp = client.chat_postMessage(**option)
    logger.info("chat_postMessage result", data=resp.data)
