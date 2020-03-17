from datetime import datetime, timedelta, timezone

import boto3
from botocore.client import BaseClient
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging()
def handler(event, context):
    return main(event)


def main(event: dict, ssm_client: BaseClient = boto3.client("ssm")) -> dict:
    amount = get_amount(event)
    current_times = get_current_times(event)

    slack_config = get_slack_config(ssm_client)
    option_post_message = create_post_message_option(amount, current_times, slack_config)
    slack_client = get_slack_client(slack_config)

    ts = post_message(option_post_message, slack_client)
    logger.info("ts", ts=ts)

    result = create_result(ts, amount, current_times)
    return result


def get_amount(event: dict) -> int:
    return event["responsePayload"]["amount"]


def get_current_times(event: dict) -> int:
    return event["responsePayload"]["current_times"]


def get_slack_config(ssm_client: BaseClient) -> dict:
    prefix = "/FukuokaDeLongiBot/Slack/"
    option = {"Path": prefix, "WithDecryption": True}
    resp = ssm_client.get_parameters_by_path(**option)
    return {x["Name"][len(prefix) :]: x["Value"] for x in resp.get("Parameters", [])}


def get_slack_client(slack_config: dict) -> WebClient:
    return WebClient(token=slack_config["SlackBotToken"])


def create_post_message_option(amount: int, current_times: int, slack_config: dict) -> dict:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y/%m/%d %H:%M:%S")
    return {
        "text": slack_config["MakeMessage"].format(slack_config["CoffeeEmoji"] * amount, current_times),
        "username": slack_config["MakeUserName"].format(now),
        "channel": slack_config["Channel"],
        "icon_emoji": slack_config["IconEmoji"],
    }


def post_message(option: dict, client: WebClient) -> str:
    resp = client.chat_postMessage(**option)
    return resp.data["ts"]


def create_result(ts: str, amount: int, times: int) -> dict:
    return {"ts": ts, "amount": amount, "times": times}
