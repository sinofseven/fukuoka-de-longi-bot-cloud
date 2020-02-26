from logger.decorator import lambda_auto_logging


@lambda_auto_logging('OPEN_SACK_FLOW_SNS_TOPIC_ARN', 'MAKE_COFFEE_FLOW_SNS_TOPIC_ARN')
def handler(event, context):
    pass
