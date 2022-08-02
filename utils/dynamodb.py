import boto3

from boto3.dynamodb.conditions import Key

PKEY_NAME = "pk"
# GENERAL_TABLE = "lost-ark-guild-bot"

dynamodb_client = boto3.resource("dynamodb")


def query_index(
    table_name: str,
    index: str,
    key_condition: dict,
    filterExpression: str = "",
    expressionAttributeValues: dict = {},
):
    table = dynamodb_client.Table(table_name)
    if filterExpression:
        response = table.query(
            IndexName=index,
            KeyConditionExpression=Key(list(key_condition.keys())[0]).eq(
                list(key_condition.values())[0]
            ),
            FilterExpression=filterExpression,
            ExpressionAttributeValues=expressionAttributeValues,
        )
    else:
        response = table.query(
            IndexName=index,
            KeyConditionExpression=Key(list(key_condition.keys())[0]).eq(
                list(key_condition.values())[0]
            ),
        )
    return response["Items"]


def get_rows(
    table_name: str,
    pkey_value: str = None,
    filterExpression: str = "",
    expressionAttributeValues: dict = {},
):
    table = dynamodb_client.Table(table_name)

    if pkey_value:
        if filterExpression:
            response = table.query(
                KeyConditionExpression=Key(PKEY_NAME).eq(pkey_value),
                FilterExpression=filterExpression,
                ExpressionAttributeValues=expressionAttributeValues,
            )
            return response["Items"]
        else:
            response = table.get_item(Key={PKEY_NAME: pkey_value})
            if response and "Item" in response:
                return [response["Item"]]
            else:
                return []

    return table.scan()["Items"]


def set_rows(table_name: str, pkey_value: str, new_column: dict):
    table = dynamodb_client.Table(table_name)
    existing_rows = get_rows(table_name, pkey_value)
    if not existing_rows:
        new_column[PKEY_NAME] = pkey_value
        table.put_item(Item=new_column)
    else:
        for k, v in new_column.items():
            for _ in existing_rows:
                table.update_item(
                    Key={PKEY_NAME: pkey_value},
                    UpdateExpression=f"set {k}=:s",
                    ExpressionAttributeValues={":s": v},
                )


def increment_counter(table_name: str, pkey_value: str, column_name: str):
    table = dynamodb_client.Table(table_name)
    existing_rows = get_rows(table_name, pkey_value)
    if not existing_rows:
        new_column = {PKEY_NAME: pkey_value, column_name: 1}
        table.put_item(Item=new_column)
    else:
        table.update_item(
            Key={PKEY_NAME: pkey_value},
            UpdateExpression=f"ADD {column_name} :inc",
            ExpressionAttributeValues={":inc": 1},
        )
