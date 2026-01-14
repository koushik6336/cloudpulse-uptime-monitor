# ============================================================
# CloudPulse – Serverless Uptime & Latency Monitoring Lambda
# ------------------------------------------------------------
# This Lambda function performs:
# - Website uptime checks
# - Latency measurement
# - Data storage in DynamoDB
# - CloudWatch custom metrics
# - Latency trend detection
# - Uptime SLA calculation
# - Smart alerting using SNS
# - Auto-recovery using CloudFront invalidation
# ============================================================

import urllib.request
import time
import boto3
from datetime import datetime
from decimal import Decimal
from boto3.dynamodb.conditions import Key

# -----------------------------
# AWS CLIENTS
# -----------------------------
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("cloudpulse-uptime-records")

cloudwatch = boto3.client("cloudwatch")
sns = boto3.client("sns")
cloudfront = boto3.client("cloudfront")

# -----------------------------
# CONFIGURATION
# -----------------------------
WEBSITE_URL = "https://d2d5jorlqa7djd.cloudfront.net"
SNS_TOPIC_ARN = "arn:aws:sns:ap-south-2:703890345539:cloudpulse-alerts"
DISTRIBUTION_ID = "E2D64ZX7IV0TKB"

AUTO_RECOVERY_THRESHOLD = 7     # Auto-recovery after 7 continuous DOWNs
ALERT_THRESHOLD = 3             # Alert after 3 continuous DOWNs
HIGH_LATENCY_THRESHOLD = 300    # ms

# -----------------------------
# LAMBDA HANDLER
# -----------------------------
def lambda_handler(event, context):

    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()

    status = "DOWN"
    status_code = None
    error_message = None

    # -----------------------------
    # STEP 1: WEBSITE UPTIME CHECK
    # -----------------------------
    try:
        response = urllib.request.urlopen(WEBSITE_URL, timeout=10)
        status_code = response.getcode()
        status = "UP"
    except Exception as e:
        error_message = str(e)

    # -----------------------------
    # STEP 2: LATENCY CALCULATION
    # -----------------------------
    latency = Decimal(str(round((time.time() - start_time) * 1000, 2)))

    # -----------------------------
    # STEP 3: STORE RESULT IN DYNAMODB
    # -----------------------------
    item = {
        "pk": "SITE#cloudpulse",
        "sk": f"TIME#{timestamp}",
        "status": status,
        "latency_ms": latency
    }

    if status == "UP":
        item["status_code"] = status_code
        print(f"STORED | UP | {latency} ms")
    else:
        item["error"] = error_message
        print(f"STORED | DOWN | {latency} ms")

    table.put_item(Item=item)

    # -----------------------------
    # STEP 4: PUSH LATENCY METRIC TO CLOUDWATCH
    # -----------------------------
    cloudwatch.put_metric_data(
        Namespace="CloudPulse",
        MetricData=[
            {
                "MetricName": "WebsiteLatency",
                "Dimensions": [{"Name": "Website", "Value": "cloudpulse"}],
                "Unit": "Milliseconds",
                "Value": float(latency)
            }
        ]
    )

    # =========================================================
    # DAY 5: LATENCY TREND DETECTION
    # =========================================================
    trend_response = table.query(
        KeyConditionExpression=Key("pk").eq("SITE#cloudpulse"),
        ScanIndexForward=False,
        Limit=10
    )

    items = trend_response.get("Items", [])
    latency_trend = "INSUFFICIENT_DATA"

    if len(items) >= 10:
        latencies = [float(i["latency_ms"]) for i in items]

        recent_avg = sum(latencies[:2]) / 2
        older_avg = sum(latencies[2:]) / (len(latencies) - 2)

        latency_trend = "DEGRADING" if recent_avg > older_avg else "NORMAL"

        print("----- DAY 5 LATENCY TREND -----")
        print(f"Recent Avg: {recent_avg:.2f} ms")
        print(f"Older Avg: {older_avg:.2f} ms")
        print(f"Latency Trend: {latency_trend}")

    # =========================================================
    # DAY 6: UPTIME SLA CALCULATION
    # =========================================================
    sla_response = table.query(
        KeyConditionExpression=Key("pk").eq("SITE#cloudpulse"),
        ScanIndexForward=False,
        Limit=50
    )

    records = sla_response.get("Items", [])
    uptime_sla = None

    if records:
        total_checks = len(records)
        up_checks = sum(1 for r in records if r["status"] == "UP")
        uptime_sla = (up_checks / total_checks) * 100

        print("----- DAY 6 SLA REPORT -----")
        print(f"Total Checks: {total_checks}")
        print(f"UP Checks: {up_checks}")
        print(f"Uptime SLA: {uptime_sla:.2f}%")

        cloudwatch.put_metric_data(
            Namespace="CloudPulse",
            MetricData=[
                {
                    "MetricName": "UptimeSLA",
                    "Dimensions": [{"Name": "Website", "Value": "cloudpulse"}],
                    "Unit": "Percent",
                    "Value": float(uptime_sla)
                }
            ]
        )

    # =========================================================
    # DAY 7: SMART ALERTING (SNS)
    # =========================================================
    alert_response = table.query(
        KeyConditionExpression=Key("pk").eq("SITE#cloudpulse"),
        ScanIndexForward=False,
        Limit=10
    )

    recent_records = alert_response.get("Items", [])

    # 🔴 Continuous DOWN detection
    down_count = 0
    for r in recent_records:
        if r["status"] == "DOWN":
            down_count += 1
        else:
            break

    if down_count >= ALERT_THRESHOLD:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="🚨 CloudPulse ALERT: Website DOWN",
            Message="Website is DOWN for 3 consecutive checks."
        )
        print("ALERT SENT: Website DOWN")

    # 🟠 High latency detection
    high_latency_count = 0
    for r in recent_records:
        if float(r["latency_ms"]) > HIGH_LATENCY_THRESHOLD:
            high_latency_count += 1
        else:
            break

    if high_latency_count >= ALERT_THRESHOLD:
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="⚠️ CloudPulse ALERT: High Latency",
            Message="Website latency exceeded 300 ms for 3 consecutive checks."
        )
        print("ALERT SENT: High Latency")

    # =========================================================
    # DAY 8: AUTO-RECOVERY (CloudFront Invalidation)
    # =========================================================
    if down_count >= AUTO_RECOVERY_THRESHOLD:
        cloudfront.create_invalidation(
            DistributionId=DISTRIBUTION_ID,
            InvalidationBatch={
                "Paths": {
                    "Quantity": 1,
                    "Items": ["/*"]
                },
                "CallerReference": str(time.time())
            }
        )

        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Subject="🔄 CloudPulse AUTO-RECOVERY TRIGGERED",
            Message=(
                "Website was DOWN for 7 consecutive checks.\n"
                "CloudFront cache invalidation executed automatically."
            )
        )

        print("AUTO-RECOVERY TRIGGERED")

    # -----------------------------
    # FINAL RESPONSE
    # -----------------------------
    return {
        "message": "CloudPulse monitoring completed",
        "timestamp": timestamp,
        "status": status,
        "latency_ms": float(latency),
        "latency_trend": latency_trend,
        "uptime_sla": uptime_sla
    }
