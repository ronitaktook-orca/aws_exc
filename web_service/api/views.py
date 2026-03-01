import json
import uuid
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import boto3


def health(request):
    """Health check for ALB and ECS."""
    return JsonResponse({"status": "ok"})


@csrf_exempt
@require_http_methods(["POST"])
def ingest(request):
    """
    Accept JSON body and write one item to DynamoDB. The table has hash key 'id'.
    Uses the task role (least privilege: PutItem on this table only).
    """
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    item_id = str(uuid.uuid4())
    # Build DynamoDB item: flatten body and ensure 'id'
    item = {"id": item_id, **{k: _to_dynamo(v) for k, v in body.items()}}
    table_name = settings.DYNAMODB_TABLE
    client = boto3.client("dynamodb", region_name=settings.AWS_REGION)
    try:
        client.put_item(TableName=table_name, Item=_to_dynamodb_item(item))
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    return JsonResponse({"id": item_id, "status": "written"})


def _to_dynamo(v):
    """Leave values as-is for PutItem; we'll convert in _to_dynamodb_item."""
    return v


def _to_dynamodb_item(d):
    """Convert Python dict to DynamoDB Item format (with S, N, M, etc.)."""
    out = {}
    for k, v in d.items():
        if v is None:
            out[k] = {"NULL": True}
        elif isinstance(v, bool):
            out[k] = {"BOOL": v}
        elif isinstance(v, str):
            out[k] = {"S": v}
        elif isinstance(v, (int, float)):
            out[k] = {"N": str(v)}
        elif isinstance(v, dict):
            out[k] = {"M": _to_dynamodb_item(v)}
        elif isinstance(v, list):
            out[k] = {"L": [_to_dynamodb_value(x) for x in v]}
        else:
            out[k] = {"S": str(v)}
    return out


def _to_dynamodb_value(v):
    if v is None:
        return {"NULL": True}
    if isinstance(v, bool):
        return {"BOOL": v}
    if isinstance(v, str):
        return {"S": v}
    if isinstance(v, (int, float)):
        return {"N": str(v)}
    if isinstance(v, dict):
        return {"M": _to_dynamodb_item(v)}
    if isinstance(v, list):
        return {"L": [_to_dynamodb_value(x) for x in v]}
    return {"S": str(v)}
