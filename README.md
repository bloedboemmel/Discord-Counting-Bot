# Discord Counting Bot with Beer-Counter
### Heavily inspired by [AlexVerricos Counting_bot](https://github.com/AlexVerrico/Discord-Counting-Bot), but adjusted a lot for the beer drinking habits of students.

## How to install and run
1. Make sure you’re logged on to the [Discord website](https://discord.com/).
2. Navigate to the [application page](https://discordapp.com/developers/applications/)
3. Click on the “New Application” button.
4. Fill out the form and click on “Create Application”.
5. Go to the “Bot” tab and then click “Add Bot”. You will have to confirm by clicking "Yes, do it!"
6. Copy the token and paste it into the `token` variable below.
7. Activate OAuth2 to invite the bot to your server.
8. Install with:
```	
pip install -r requirements.txt
export THE_COUNT_DISCORD_TOKEN=<your_discord_bot_token>
python3 main.py
```

## How to start
You need admin rights to set up the bot:

This bot reacts to the Prefix `!count`

In the channel you want to start counting, type `!count counting_channel this_channel`

Alternatively, you can use `!count counting_channel your_favorite_channel`

Same goes for the logging_channel, which also reacts to any user-commands (`!count log_channel this_channel`)

### And thats it!

## Implemented Bot_Commands
`!count server` - Shows stats for the server

`!count highscore` - Shows the top 10 users with the most correctly counted numbers

`!count highcount` - Shows the top 10 users with the highest counted numbers

`!count set_drink` - Sets your favorite drink

`!count user` - Shows stats for you

`!count user @user` - Shows stats for mentioned user


`!count beer_count` - Gets the current beer-debt-table for this guild

`!count beer_count me` - Gets the current beer-debt-table for this user

`!count spend_beer @user` - Notify the bot that the other user has paid for your beer and updates the debts

`!count delete_me` - Deletes your account from the server stats, but not from the beer-debts

`!count copy_info` - Copies your stats from the the Counting Bot to this bot

## To be implemented

Bot should react to edited messages.

A little more insults, when somebody tries to trick the bot!

# Run in docker
```	
docker-compose build
docker run --env THE_COUNT_DISCORD_TOKEN=<YOUR_VERY_OWN_DISCORDTOKEN> discord-counting-bot_countingbot:latest
```

