"""
DynamoDB Stream handler: for each new/updated record, write JSON to S3 and send SMS via SNS.
"""
import json
import os
import uuid
from datetime import datetime

import boto3

RESULTS_BUCKET = os.environ["RESULTS_BUCKET"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]
s3 = boto3.client("s3")
sns = boto3.client("sns")


def lambda_handler(event, context):
    """
    Process DynamoDB stream events. Each record (NEW_AND_OLD_IMAGES) is written
    as a JSON object to S3; then an SMS is sent with the write status.
    """
    for record in event.get("Records", []):
        if record.get("eventName") not in ("INSERT", "MODIFY"):
            continue
        # Use the new image (current state of the item)
        payload = record.get("dynamodb", {}).get("NewImage") or {}
        # Unmarshal DynamoDB format to plain dict
        item = unmarshall(payload)
        key = item.get("id") or str(uuid.uuid4())
        object_key = f"results/{datetime.utcnow().strftime('%Y/%m/%d')}/{key}.json"
        try:
            s3.put_object(
                Bucket=RESULTS_BUCKET,
                Key=object_key,
                Body=json.dumps(item, default=str),
                ContentType="application/json",
            )
            status = f"OK: s3://{RESULTS_BUCKET}/{object_key}"
        except Exception as e:
            status = f"ERROR writing to S3: {e!s}"
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=status,
            Subject="Pipeline result",
        )
    return {"processed": len(event.get("Records", []))}


def unmarshall(ddb_item: dict) -> dict:
    """Convert DynamoDB item (with type keys S, N, M, etc.) to plain Python dict."""
    if not ddb_item:
        return {}
    out = {}
    for k, v in ddb_item.items():
        if "S" in v:
            out[k] = v["S"]
        elif "N" in v:
            try:
                out[k] = int(v["N"])
            except ValueError:
                out[k] = float(v["N"])
        elif "M" in v:
            out[k] = unmarshall(v["M"])
        elif "L" in v:
            out[k] = [unmarshall_item(x) for x in v["L"]]
        elif "BOOL" in v:
            out[k] = v["BOOL"]
        elif "NULL" in v:
            out[k] = None
        else:
            out[k] = v
    return out


def unmarshall_item(v):
    """Unmarshall a single DynamoDB value (for lists)."""
    if "S" in v:
        return v["S"]
    if "N" in v:
        try:
            return int(v["N"])
        except ValueError:
            return float(v["N"])
    if "M" in v:
        return unmarshall(v["M"])
    if "L" in v:
        return [unmarshall_item(x) for x in v["L"]]
    if "BOOL" in v:
        return v["BOOL"]
    if "NULL" in v:
        return None
    return v
