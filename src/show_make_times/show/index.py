import os
from datetime import datetime, timedelta, timezone
from typing import List, Tuple

import boto3
from boto3.resources.base import ServiceResource
from botocore.client import BaseClient
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging("DATA_STORE_TABLE_NAME")
def handler(event, context):
    main(event)


def main(
    event: dict,
    dynamodb_resource: ServiceResource = boto3.resource("dynamodb"),
    ssm_client: BaseClient = boto3.client("ssm"),
):
    year, month = parse_event(event)
    table_name = get_table_name()
    user_make_history = get_user_make_history(year, month, table_name, dynamodb_resource)
    slack_config = get_slack_config(ssm_client)
    slack_client = get_slack_client(slack_config)
    option_post_message = (
        create_user_make_history_message(user_make_history, slack_config)
        if user_make_history is not None
        else create_no_data_message_option(year, month, slack_config)
    )
    post_message(option_post_message, slack_client)


def parse_event(event: dict) -> Tuple[int, int]:
    message = event["Records"][0]["Sns"]["Message"]
    year, month = [int(x) for x in message.split("-")]
    return year, month


def get_table_name() -> str:
    return os.environ["DATA_STORE_TABLE_NAME"]


def get_user_make_history(year: int, month: int, table_name: str, dynamodb_resource: ServiceResource) -> dict:
    table = dynamodb_resource.Table(table_name)
    option = {"Key": {"partitionId": "userMakeHistory", "sortId": f"{year}年{month:02}月"}}
    resp = table.get_item(**option)
    logger.info("get user make history result", option=option, response=resp)
    return resp.get("Item")


def get_slack_config(ssm_client: BaseClient, token=None) -> dict:
    prefix = "/FukuokaDeLongiBot/Slack/"
    option = {"Path": prefix, "WithDecryption": True}
    if token is not None:
        option["NextToken"] = token
    resp = ssm_client.get_parameters_by_path(**option)
    result = {x["Name"][len(prefix) :]: x["Value"] for x in resp.get("Parameters", [])}
    if "NextToken" in resp:
        result.update(get_slack_config(ssm_client, token=resp["NextToken"]))
    return result


def get_slack_client(slack_config: dict) -> WebClient:
    return WebClient(token=slack_config["SlackBotToken"])


def create_no_data_message_option(year: int, month: int, slack_config: dict) -> dict:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")
    return {
        "channel": slack_config["Channel"],
        "username": slack_config["ShowUserMakeHistoryUserName"].format(now),
        "icon_emoji": slack_config["IconEmoji"],
        "text": "\n".join([f"{year}年{month:02}月", "```", "no data", "```"]),
    }


def create_make_spread_sheet(user_make_history: dict) -> List[str]:
    data = {}
    for k, v in user_make_history.items():
        if k in ["partitionId", "sortId", "updatedAt"]:
            continue
        user_id, type_name = k.split("_")
        item = data.get(user_id)
        if item is None:
            item = {}
        item[type_name] = v
        data[user_id] = item
    lines = []
    for k, v in data.items():
        name = v["name"] if "name" in v else "名前無し"
        times = v["times"] if "times" in v else 0
        lines.append(f"{name} (id={k}): {times}杯")
    return lines


def create_user_make_history_message(user_make_history: dict, slack_config: dict) -> dict:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")
    data_user_make = create_make_spread_sheet(user_make_history)
    return {
        "channel": slack_config["Channel"],
        "username": slack_config["ShowUserMakeHistoryUserName"].format(now),
        "icon_emoji": slack_config["IconEmoji"],
        "text": "\n".join([f'{user_make_history["sortId"]}', "```"] + data_user_make + ["```"]),
    }


def post_message(option: dict, client: WebClient) -> None:
    resp = client.chat_postMessage(**option)
    logger.info("post message result", option=option, response=resp)
