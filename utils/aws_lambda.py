import boto3
import json

LAMBDA = boto3.client('lambda')

API_CALLER = "robotrader"


def invoke_processor(body):
    response = LAMBDA.invoke(FunctionName=API_CALLER,
                             InvocationType='Event',
                             Payload=bytes(json.dumps(body), 'utf-8'))

def enable_rule(name):
    LAMBDA.enable_rule(Name=name)

def disable_rule(name):
    LAMBDA.disable_rule(Name=name)
