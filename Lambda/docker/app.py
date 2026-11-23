import json
import logging
import os

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))


def lambda_handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    name = event.get("name", "World")
    message = f"Hello {name} from a Lambda container!"
    print(message)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": message}),
    }
