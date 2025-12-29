import urllib.request
import time
import boto3
from datetime import datetime
from decimal import Decimal

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("cloudpulse-uptime-records")

def lambda_handler(event, context):
    url = "https://d2d5jorlqa7djd.cloudfront.net"
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()

    try:
        response = urllib.request.urlopen(url, timeout=10)
        status_code = response.getcode()
        latency = Decimal(str(round((time.time() - start_time) * 1000, 2)))

        item = {
            "pk": "SITE#cloudpulse",
            "sk": f"TIME#{timestamp}",
            "status": "UP",
            "status_code": status_code,
            "latency_ms": latency
        }

        table.put_item(Item=item)
        print(f"STORED | UP | {latency} ms")

        return item

    except Exception as e:
        latency = Decimal(str(round((time.time() - start_time) * 1000, 2)))

        item = {
            "pk": "SITE#cloudpulse",
            "sk": f"TIME#{timestamp}",
            "status": "DOWN",
            "error": str(e),
            "latency_ms": latency
        }

        table.put_item(Item=item)
        print(f"STORED | DOWN | {latency} ms")

        return item

