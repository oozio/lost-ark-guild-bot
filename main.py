import json
import boto3
import requests

from commands.visibility import SHOULD_HIDE_COMMAND_OUTPUT
from utils import discord, aws_lambda


def lambda_handler(event, context):
    # handle discord's integrity check
    pong = discord.check_input(event)
    if pong:
        return pong

    # pass event to processor
    aws_lambda.invoke_processor(event)

    # get interaction metadata
    command = event["body-json"]["data"]["name"]

    # return :thinking:
    return discord.initial_response('ACK_WITH_SOURCE',
                                    ephemeral=SHOULD_HIDE_COMMAND_OUTPUT.get(
                                        command, True))
