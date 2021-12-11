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
## Run in docker
```	
docker-compose build
docker run --env THE_COUNT_DISCORD_TOKEN=<YOUR_VERY_OWN_DISCORDTOKEN> discord-counting-bot_countingbot:latest
```

## Note: We speak german!
Because of our german-speaking main-channel we switched to german. A multilanguage-option won't be available anytime soon. Fell free to implement it and make a pull request.

<img alt="Sprich Deutsch, du..." src="https://img.ifunny.co/images/e8b909c4e2fb3d2681465d7eaebb9c76ed686fb49bca693ed6e111dd9112663a_1.jpg" height="300" >

## How to start
You need admin rights to set up the bot:

This bot reacts to the Prefix `!count`

In the channel you want to start counting, type `!count counting_channel aktueller_kanal`

Alternatively, you can use `!count counting_channel your_favorite_channel`

Same goes for the logging_channel, which also reacts to any user-commands (`!count log_channel aktueller_kanal`)

### And thats it!

## NEW: PROFI-Counter
For the users who counted right more than a given threshold, the user can access the profi_channel


## Implemented Commands
### Admin-Commands
`!count counting_channel aktueller_kanal` um den Zählfortschritt in diesem Kanal einzusehen

`!count counting_channel @anderer_kanal` um den Kanal in dem gezählt wird zu ändern

`!count log_channel aktueller_kanal` um den Kanal mit Log Nachrichten zu ändern

`!count log_channel @anderer_kanal` um den Kanal mit Log Nachrichten zu ändern

`!count pro_channel aktueller_kanal` um den Kanal für Profis zu ändern

`!count pro_channel @anderer_kanal` um den Kanal für Profis zu ändern

`!count pro_role @rolle` um die Rolle für Profis zu ändern

`!count pro_threshold anzahl` um den Threshold zur Profi-Berechtigung zu ändern 

### User-Commands
`!count server` - Zeige die Statistiken für den ganzen Server

`!count highscore` - Zeige die 10 Nutzer, die am häufigsten richtig gezählt haben

`!count highcount` - Zeige die 10 Nutzer, welche die höchsten Zahlen getippt haben

`!count user` - Zeige deine eigenen Statistiken

`!count user @user` - Zeige Statistiken für einen anderen Zählenden

`!count drink_count` - Zeige die aktuelle Bierschuldentabelle für den Server

`!count drink_count me` - Zeigt dir alle Bierschuldentabelleneinträge bei denen du dabei bist

`!count spend_drink @user` - Sag dem Bot Bescheid, dass dir dein zustehendes Bier endlich ausgegeben wurde

`!count set_drink`- Wenn dein Lieblingsgetränk komischerweise kein Bier sein sollte kannst du das hier ändern (aber kein Radler)!

`!count copy_data message_id` - Kopiert die Daten vom originalen Bot

`!count delete_me` Löscht deine Daten aus dem Metaverse (tschüss)
