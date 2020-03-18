from typing import Optional, Tuple

import boto3
from botocore.client import BaseClient
from slack import WebClient

from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging()
def handler(event, context):
    main(event)


def main(event: dict, ssm_client: BaseClient = boto3.client("ssm")):
    user_name, ts, amount, sack_times, _ = parse_event(event)
    slack_config = get_slack_config(ssm_client)
    slack_client = get_slack_client(slack_config)
    option_update_message = create_update_message_option(user_name, ts, amount, sack_times, slack_config)
    update_message(option_update_message, slack_client)


def parse_event(event: dict) -> Tuple[str, str, int, int, int]:
    data = event["responsePayload"]
    return data["user_name"], data["ts"], data["amount"], data["sack_times"], data["user_times"]


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


def create_update_message_option(user_name: str, ts: str, amount: int, sack_times: int, slack_config: dict) -> dict:
    return {
        "channel": slack_config["Channel"],
        "ts": ts,
        "text": slack_config["ReactionMessage"].format(slack_config["CoffeeEmoji"] * amount, sack_times, user_name),
    }


def update_message(option: dict, client: WebClient) -> None:
    resp = client.chat_update(**option)
    logger.info("update message result", option=option, response=resp)
