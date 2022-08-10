import requests
import threading
from bs4 import BeautifulSoup
import time
from utils import discord

SERVER = 'Bergstrom'
INTERVAL = 120

# Looks through all server statuses, looking for the SERVER keyword, then goes up
# a level and looks for MAINTENANCE_CLASS, which is the class assigned to the
# maintenance status icon.
#
# Would need to observe the CSS class of other statuses to handle them, but we
# don't actually care since all we want to know is if maintenance is over.
def check_maintenance():
    MAINTENANCE_CLASS = 'ags-ServerStatus-content-responses-response-server-status--maintenance'

    response = requests.get('https://www.playlostark.com/en-us/support/server-status')
    html = BeautifulSoup(response.text, 'html.parser')

    statuses = html.select('.ags-ServerStatus-content-responses > div.ags-ServerStatus-content-responses-response')

    server = None
    for region_statuses in statuses:
        servers = region_statuses.select('.ags-ServerStatus-content-responses-response-server-name')
        for s in servers:
            if s.text.strip() == SERVER:
                server = s
                break
        if server:
            break

    if server:
        status = server.parent.select('.ags-ServerStatus-content-responses-response-server-status')[0]
        if MAINTENANCE_CLASS in status.attrs['class']:
            return True
        else:
            return False
    else:
        return False

# This is a dumb loop that runs check_maintenance() every INTERVAL seconds
def wait_for_maintenance(user_id, channel_id):
    while True:
        time.sleep(INTERVAL)
        if not check_maintenance():
            message = f"{discord.mention_user(user_id)} The server is back up!"
            discord.post_message_in_channel(channel_id, message)
            break

def handle(command, user_id, channel_id):
    if check_maintenance():
        # Spawn a thread here so that it doesn't freeze up the whole bot
        # TODO: This spawns a new thread every time the command is sent.
        #   We in theory only need to have a single thread ever, but would
        #   need to think about where/how to store the list of users
        thread = threading.Thread(target=wait_for_maintenance, args=(user_id, channel_id), daemon=True)
        thread.start()
        return "You will be notified when maintenance is complete"
    else:
        return "Server is not in maintenance"
