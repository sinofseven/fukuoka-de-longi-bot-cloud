from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger
from boto3.resources.base import ServiceResource
import boto3
from datetime import datetime, timezone, timedelta
from typing import Tuple
import os

logger = MyLogger(__name__)


@lambda_auto_logging('DATA_STORE_TABLE_NAME')
def handler(event, context):
    return main(event)


def main(event: dict, dynamodb_resource: ServiceResource = boto3.resource('dynamodb')) -> dict:
    user_id, ts, user_name, sack_times, amount = parse_event(event)
    table_name = get_table_name()
    user_times = upsert_user_make_history(user_id, user_name, amount, table_name, dynamodb_resource)
    return create_result(user_name, ts, amount, sack_times, user_times)


def parse_event(event: dict) -> Tuple[str, str, str, int, int]:
    data = event['responsePayload']
    return data['user_id'], data['ts'], data['user_name'], data['times'], data['amount']


def get_table_name():
    return os.environ['DATA_STORE_TABLE_NAME']


def upsert_user_make_history(user_id: str, user_name: str, amount: int, table_name: str, dynamodb_resource: ServiceResource) -> int:
    jst = timezone(offset=timedelta(hours=+9), name="jst")
    now = datetime.now(jst).strftime("%Y年%m月")

    table = dynamodb_resource.Table(table_name)
    key_user_times = f'{user_id}_times'
    option = {
        'Key': {
            'partitionId': 'userMakeHistory',
            'sortId': now
        },
        'UpdateExpression': 'add #user_times :user_times set #user_name = :user_name, #updatedAt = :updatedAt',
        'ExpressionAttributeNames': {
            '#user_times': key_user_times,
            '#user_name': f'{user_id}_name',
            '#updatedAt': 'updatedAt'
        },
        'ExpressionAttributeValues': {
            ':user_times': amount,
            ':user_name': user_name,
            ':updatedAt': int(datetime.now(timezone.utc).timestamp() * 1000)
        },
        'ReturnValues': 'ALL_NEW'
    }
    resp = table.update_item(**option)
    return int(resp['Attributes'][key_user_times])


def create_result(user_name: str, ts: str, amount: int, sack_times: int, user_times: int) -> dict:
    return {
        'user_name': user_name,
        'ts': ts,
        'amount': amount,
        'sack_times': sack_times,
        'user_times': user_times
    }