import boto3
import datetime
import json
from constants.common import SELF_ARN, SCHEDULE_GROUP

EVENTBRIDGE_ROLE = "arn:aws:iam::391107963258:role/eventbridge_reminders_role"
TIMEZONE = "America/Los_Angeles"
eventbridge_client = boto3.client('scheduler')

INFO_TEMPLATE = {
    "source": "aws.events",
    "resources": SCHEDULE_GROUP
}

def _timestamp_to_schedule_expression(timestamp: datetime.date):
    return f"at({timestamp.strftime('%Y-%m-%dT%H:%M:%S')})"

def create_reminder(id: str, timestamp: datetime.date):
    info = INFO_TEMPLATE.copy()
    info["thread_id"] = id

    eventbridge_client.create_schedule(
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        GroupName=SCHEDULE_GROUP,
        Name=id,
        ScheduleExpression=_timestamp_to_schedule_expression(timestamp),
        ScheduleExpressionTimezone=TIMEZONE,
        Target={
            "Arn": SELF_ARN,
            "Input": json.dumps(info),
            "RoleArn": EVENTBRIDGE_ROLE
        },
    )

def change_reminder(id: str, timestamp: datetime.date):
    info = INFO_TEMPLATE.copy()
    info["thread_id"] = id

    eventbridge_client.create_schedule(
        FlexibleTimeWindow={
            "Mode": "OFF"
        },
        GroupName=SCHEDULE_GROUP,
        Name=id,
        ScheduleExpression=_timestamp_to_schedule_expression(timestamp),
        ScheduleExpressionTimezone=TIMEZONE,
        Target={
            "Arn": SELF_ARN,
            "Input": json.dumps(info),
            "RoleArn": EVENTBRIDGE_ROLE
        },
    )