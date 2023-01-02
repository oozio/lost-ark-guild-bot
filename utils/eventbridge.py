import boto3
import datetime
import json
from constants.common import SELF_ARN

EVENTBRIDGE_ROLE = "arn:aws:iam::391107963258:role/aws-service-role/apidestinations.events.amazonaws.com/AWSServiceRoleForAmazonEventBridgeApiDestinations"
SCHEDULE_GROUP = "lost_ark_thread_reminders"

eventbridge_client = boto3.client('scheduler')

def _timestamp_to_schedule_expression(timestamp: datetime.date):
    return f"at({timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')})"

def create_reminder(id: str, timestamp: datetime.date):
    info = {
        "thread_id": id
    }

    eventbridge_client.create_schedule(
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        GroupName=SCHEDULE_GROUP,
        Name=id,
        ScheduleExpression=_timestamp_to_schedule_expression(timestamp),
        Target={
            "ARN": SELF_ARN
        },
        Input=json.dumps(info),
        RoleARN=EVENTBRIDGE_ROLE,
    )

def change_reminder(id: str, new_time: datetime.date):
    info = {
        "thread_id": id
    }
    
    eventbridge_client.create_schedule(
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        GroupName=SCHEDULE_GROUP,
        Name=id,
        ScheduleExpression=_timestamp_to_schedule_expression(new_time),
        Target={
            "ARN": SELF_ARN
        },
        Input=json.dumps(info),
        RoleARN=EVENTBRIDGE_ROLE,
    )