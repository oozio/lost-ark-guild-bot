# lost-ark-guild-bot


## adding a new command:
- request to be a repo collaborator
- add command to commands/commands.json
    - how to format input/description/etc: https://discord.com/developers/docs/interactions/slash-commands#applicationcommandoption
- add preferred command output visibility in commands/visibility.py
- add handling in command_handler.py
- all pushes are automatically deployed (checks Actions tab for progress)
- (shameless self plug) details for how ^ works: 
    - https://oozio.medium.com/serverless-discord-bot-55f95f26f743
    - https://oozio.medium.com/serverless-discord-bot-github-based-cicd-e2a9e9a7bc4d
