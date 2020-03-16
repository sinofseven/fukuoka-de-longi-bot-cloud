from logger.decorator import lambda_auto_logging
from logger.my_logger import MyLogger

logger = MyLogger(__name__)


@lambda_auto_logging()
def handler(event, context):
    return main(event)


def main(event: dict) -> dict:
    return event
