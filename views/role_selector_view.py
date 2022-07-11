# from utils import discord
# import discord.ext.commands as commands
# from discord_ui import Button, Components, SlashInteraction, UI

#currently in testing to see if bot will display buttons
class RoleSelectorView:

    COMPONENTS = [
        {
            "type": 1,
            "components": [
                {
                    "type": 2,
                    "label": "Vykas",
                    "style": 1,
                    "custom_id": "click_one"
                }
            ]

        }
    ]
    # guild_id = ''
    # BOT_TOKEN = discord.BOT_TOKEN

    # def __init__(self, server_id):
    #     role_buttons.guild_id = server_id

    # #main discord bot client
    # client = commands.Bot(" ")
    # #guild_id = client.get_guild
    # #initialize extension
    # ui = UI(client)

    # #Currently playing around with this. I do NOT expect this to work with this setup
    # @ui.slash.command(name="role_buttons", description="testing", guild_ids=[guild_id])
    # async def display(ctx: SlashInteraction):

    #     #component list for all role buttons
    #     button_list = [
    #         [Button("Vykas", color="purple")]
    #     ]

    #     msg = await ctx.send("vykas", components = button_list)
