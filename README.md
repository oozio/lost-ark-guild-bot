# lost-ark-guild-bot

### short description
the actual code/etc lives in aws, and the general flow is 
1. someone interacts with the bot on discord
2. discord sends an interaction event to the bot's webhook, which is provided by APIGateway
3. API is fulfilled by a dispatcher lambda, which responds immediately to avoid discord's aggressive-ish initial timeout
4. dispatcher lambda calls actual processing lambda
5. actual code is run
6. actual results are returned to user, through editing the original message/sending a new message/whatever

(shameless self plug) details for how ^ works: 
- https://oozio.medium.com/serverless-discord-bot-55f95f26f743
- https://oozio.medium.com/serverless-discord-bot-github-based-cicd-e2a9e9a7bc4d




### how to make changes
1. request to be a repo collaborator/msg #bot-testing for aws permissions; alternatively, fork and make a pull request
2. make changes
3. push new code to git 
4. on-push git actions (check Actions tab for progress, https://github.com/oozio/lost-ark-guild-bot/actions):
    - publishes new code to aws 
    - refreshes all discord commands (delete and recreate)
5. try it out; look at cloudwatch for logs

notably there's no staging environment :yay:




### adding a new command:
- add command to commands/commands.json
    - how to format input/description/etc: https://discord.com/developers/docs/interactions/slash-commands#applicationcommandoption
- add preferred command output visibility in commands/visibility.py
- add handling in command_handler.py
