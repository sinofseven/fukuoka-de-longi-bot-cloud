from logger.decorator import lambda_auto_logging


@lambda_auto_logging()
def handler(event, context):
    return event
