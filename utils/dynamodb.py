import boto3

from boto3.dynamodb.conditions import Key

PKEY_NAME = "pk"
GENERAL_TABLE = "lost-ark-guild-bot"

dynamodb_client = boto3.resource("dynamodb")


def get_rows(table_name, pkey_value=None):
    table = dynamodb_client.Table(table_name)
    if pkey_value:
        response = table.get_item(Key={PKEY_NAME: str(pkey_value)})
        if response and "Item" in response:
            return [response["Item"]]
        else:
            return []
    else:
        return table.scan()["Items"]


def set_rows(table_name, pkey_value, new_column):
    table = dynamodb_client.Table(table_name)
    existing_rows = get_rows(table_name, pkey_value)
    if not existing_rows:
        new_column[PKEY_NAME] = str(pkey_value)
        table.put_item(Item=new_column)
    else:
        for k, v in new_column.items():
            for row in existing_rows:
                table.update_item(Key={PKEY_NAME: pkey_value},
                                  UpdateExpression=f"set {k}=:s",
                                  ExpressionAttributeValues={":s": v})

    if table_name != GENERAL_TABLE:
        set_rows(GENERAL_TABLE, pkey_value, new_column)
