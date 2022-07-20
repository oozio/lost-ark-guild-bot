import json
import boto3
import requests

from constants import interactions
from utils import discord, aws_lambda

from commands.visibility import SHOULD_HIDE_COMMAND_OUTPUT


def lambda_handler(event, context):
    # handle discord's integrity check
    pong = discord.check_input(event)
    if pong:
        return pong

    # pass event to processor
    aws_lambda.invoke_processor(event)

    interaction_type = event["body-json"]["type"] 

    if interaction_type == interactions.InteractionsType.MESSAGE_COMPONENT:
        return discord.initial_response("DEFERRED_UPDATE_MESSAGE")
    elif interaction_type == interactions.InteractionsType.APPLICATION_COMMAND:
        command = event["body-json"]["data"]["name"]
        
        # return :thinking:
        return discord.initial_response('ACK_WITH_SOURCE',
                                        ephemeral=SHOULD_HIDE_COMMAND_OUTPUT.get(
                                            command, True))
