import sqlite3
import os
from discord.client import Client
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Embed, Color, guild, message, ext
from discord.utils import get

from datetime import datetime

intents = Intents.default()
intents.guild_messages = True
load_dotenv()
TOKEN = os.getenv('THE_COUNT_DISCORD_TOKEN')
if TOKEN is None:
    print("Please set the TOKEN variable in the Environment")
    exit()

# PREFIX = "".join((os.getenv('THE_COUNT_PREFIX'), ' '))
PREFIX = "!count "
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

DbName = 'count.sqlite'
count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'message', 'channel_id',
                      'log_channel_id', 'greedy_message', 'record', 'record_user', 'record_timestamp']
stat_headers = ['guild_id', 'user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity', 'drink']
beer_headers = ['guild_id', 'user', 'owed_user', 'count']
connection = sqlite3.connect(DbName)
cursor = connection.cursor()


# -- Begin SQL Helper Functions --
def create_table(dbname, tablename, tableheader):
    try:
        cursor.execute("CREATE TABLE %s%s" % (tablename, tuple(tableheader)))
        connection.commit()
        return
    except sqlite3.OperationalError:
        return


def time_since(strtime):
    now = datetime.now()
    then = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S.%f')
    duration = now - then
    days = duration.days
    hours = duration.seconds // 3600
    minutes = (duration.seconds // 60) % 60
    if days > 0:
        return f'vor {days} Tagen'
    elif hours > 0:
        return f'vor {hours} Stunden'
    elif minutes > 0:
        return f'vor {minutes} Minuten'
    else:
        return 'jetzt gerade'


def isrightchannel(ctx):
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        return
    guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
    if int(log_channel_id) != int(ctx.channel.id):
        return False
    return True


def insert_values_into_table(dbname, tablename, values):
    if os.path.exists(dbname) is True:
        cursor.execute("INSERT INTO %s VALUES %s" % (tablename, tuple(values)))
        connection.commit()


def check_if_table_exists(dbname, tablename, tableheaders):
    try:
        cursor.execute("SELECT * FROM %s" % tablename)
    except sqlite3.OperationalError:
        create_table(dbname, tablename, tableheaders)


def create_new_entry(guild_id,
                     count=str(0),
                     number_of_resets=str(0),
                     last_user=str(0),
                     guild_message=str("{{{user}}} hat die falsche Zahl geschrieben!"),
                     count_channel_id=str(''),
                     log_channel_id=str(''),
                     greedy_message=str("{{{user}}} war zu gierig")):
    # dbOperations.put(['create',
    temp1 = [
        str(guild_id), str(count),
        str(number_of_resets),
        str(last_user),
        str(guild_message),
        str(count_channel_id),
        str(log_channel_id),
        str(greedy_message),
        str(0),
        str(0),
        str(0)]
    # ])

    cursor.execute("INSERT INTO count_info %s VALUES %s" % (tuple(count_info_headers), tuple(temp1)))
    connection.commit()
    return


def update_beertable(guild_id, user, owed_user, count, second_try=False, spend_beer=False):
    cursor.execute(
        f"SELECT * FROM beers WHERE guild_id = '{guild_id}' AND user = '{user}' AND owed_user = '{owed_user}'")
    temp = cursor.fetchone()
    if temp is None and spend_beer is True:
        return False, 0
    if temp is None:
        if second_try is True:
            cursor.execute(
                f"INSERT INTO beers (guild_id, user, owed_user, count) VALUES ('{guild_id}', '{owed_user}','{user}', '1')")
            connection.commit()
            return True, 1
        else:
            return update_beertable(guild_id, owed_user, user, -count,
                                    second_try=True)  # Changed user and owed_user on purpose


    else:
        guild_id, user, owed_user, saved_count = temp
        if int(saved_count) + int(count) <= 0:
            cursor.execute(
                f"DELETE FROM beers WHERE  guild_id = '{guild_id}' AND user = '{user}' AND owed_user = '{owed_user}'")
            connection.commit()
            return True, 0
        cursor.execute(
            f"UPDATE beers SET count = count + {count} WHERE guild_id = '{guild_id}' AND user = '{user}' AND owed_user = '{owed_user}'")
        connection.commit()

        return True, int(saved_count) + int(count)


def update_stats(guild_id, user, correct_count=True, current_number=1, drink=""):
    # stat_headers = ['guild_id', 'user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity']

    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{guild_id}' AND user = '{user}'")
    temp = cursor.fetchone()
    last_activity = datetime.now()

    if temp is None:
        if drink == "":
            drink = "beer"
        if correct_count is True:
            cursor.execute(
                f"INSERT INTO stats (guild_id, user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{guild_id}', '{user}', '1', '0', '{current_number}', '{last_activity}', '{drink}')")
        else:
            cursor.execute(
                f"INSERT INTO stats (guild_id, user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{guild_id}', '{user}', '0', '1', '{current_number}', '{last_activity}', '{drink}')")
        connection.commit()
    else:
        highest_valid_count = temp[3]
        if current_number > int(highest_valid_count):
            highest_valid_count = str(current_number)
        if correct_count is True:
            cursor.execute(
                f"UPDATE stats SET count_correct = count_correct + 1, highest_valid_count = ?, last_activity = ? WHERE guild_id = '{guild_id}' AND user = '{user}'",
                (highest_valid_count, last_activity,))
        else:
            cursor.execute(
                f"UPDATE stats SET count_wrong = count_wrong + 1, last_activity = ? WHERE guild_id = '{guild_id}' AND user = '{user}'",
                (last_activity,))
        connection.commit()
        if drink != "":
            cursor.execute(f"UPDATE stats SET drink = '{drink}' WHERE guild_id = '{guild_id}' AND user = '{user}'")
            connection.commit()


def update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message,
                record, record_user, record_timestamp, table_name='count_info'):
    cursor.execute(
        f"UPDATE {table_name} SET guild_id = ?, current_count = ?, number_of_resets = ?, last_user = ?, message = ?, channel_id = ?, log_channel_id = ?, greedy_message = ?, record = ?, record_user = ?, record_timestamp = ? WHERE guild_id = '{guild_id}'",
        (
        guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record,
        record_user, record_timestamp,))
    connection.commit()


# -- End SQL Helper Functions --


# -- Begin Count Master Commands --
bot.remove_command('help')


@bot.command(name='help')
async def count_help(ctx):
    embed = Embed(title="Der Zählbierboter", url="https://github.com/bloedboemmel/Discord-Counting-Bot",
                  description="Alle Befehle",
                  color=Color.purple())
    embed.set_thumbnail(url="https://pbs.twimg.com/media/D9x2dXnWsAgrqN7.jpg")
    message = f"`{PREFIX}counting_channel aktueller_kanal` um den Zählfortschritt in diesem Kanal einzusehen\n"
    message += f"`{PREFIX}counting_channel @anderer_kanal` um den Kanal in dem gezählt wird zu ändern\n"
    message += f"`{PREFIX}log_channel aktueller_kanal` um den Kanal mit Log Nachrichten zu ändern\n"
    embed.add_field(name="Admin Befehle", value=message, inline=False)
    message = f"`{PREFIX}server` - Zeige die Statistiken für den ganzen Server\n"
    message += f"`{PREFIX}highscore` - Zeige die 10 Nutzer, die am häufigsten richtig gezählt haben\n"
    message += f"`{PREFIX}highcount` - Zeige die 10 Nutzer, welche die höchsten Zahlen getippt haben\n"
    message += f"`{PREFIX}user` - Zeige deine eigenen Statistiken\n"
    message += f"`{PREFIX}user @user` - Zeige Statistiken für einen anderen Zählenden\n"
    message += f"`{PREFIX}drink_count` - Zeige die aktuelle Bierschuldentabelle für den Server\n"
    message += f"`{PREFIX}drink_count me` - Zeigt dir alle Bierschuldentabelleneinträge bei denen du dabei bist\n"
    message += f"`{PREFIX}spend_drink @user` - Sag dem Bot Bescheid, dass dir dein zustehendes Bier endlich ausgegeben wurde\n"
    message += f"`{PREFIX}set_drink` - Wenn dein Lieblingsgetränk komischerweise kein Bier sein sollte kannst du das hier ändern (aber kein Radler)!\n"
    message += f"`{PREFIX}copy_data message_id` - Kopiert die Daten vom originalen Bot\n"
    message += f"`{PREFIX}delete_me` Löscht deine Daten aus dem Metaverse (tschüss)"
    embed.add_field(name="User-Commands", value=message, inline=False)
    embed.set_footer(text=f"{PREFIX} help")
    await ctx.send(embed=embed)
    return


@bot.command(name='wrong_message')
@commands.has_permissions(administrator=True)
async def wrong_message(ctx, *args):
    _message = " ".join(args)
    if _message == 'help':
        response = """
        Ändere die Nachricht für den Fall, dass es jemand verkackt hat
{{{user}}} wird ersetzt durch den Namen der Schande
        """
        await ctx.send(response)
        return
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()

    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=ctx.channel.id,
                         log_channel_id=ctx.channel.id,
                         guild_message=_message)
    else:
        guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, _message, channel_id, log_channel_id, greedy_message,
                    record, record_user, record_timestamp)
    return


@wrong_message.error
async def wrong_message_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Du hast leider nicht die erforderlichen Rechte um den Befehl auszuführen')
    else:
        raise error


@bot.command(name='greedy_message')
@commands.has_permissions(administrator=True)
async def greedy_message(ctx, *args):
    _message = " ".join(args)
    if _message == 'help':
        response = """
        Ändere die Nachricht für den Fall, dass jemand 2 mal nacheinander gezählt hat
{{{user}}} wird ersetzt durch den Namen der Schande
        """
        await ctx.send(response)
        return
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()
    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=ctx.channel.id,
                         log_channel_id=ctx.channel.id,
                         greedy_message=_message)

    else:
        guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, old_greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, _message,
                    record, record_user, record_timestamp)
    return


@wrong_message.error
async def wrong_message_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Du hast leider nicht die erforderlichen Rechte um den Befehl auszuführen')
    else:
        raise error


@bot.command(name='counting_channel')
@commands.has_permissions(administrator=True)
async def counting_channel(ctx, arg1):
    # print("counting_channel")
    channel_id = arg1
    if channel_id == 'help':
        response = f"""
            Ändere die ID des Kanals in dem gezählt wird
nutze `{PREFIX}counting_channel aktueller_kanal` um im aktuellen Kanal zu zählen
            """
        await ctx.send(response)
        return
    if channel_id == 'aktueller_kanal':
        channel_id = ctx.channel.id
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()

    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=channel_id,
                         log_channel_id=channel_id, )
    else:
        guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id,
                    greedy_message, record, record_user, record_timestamp)
    return


@counting_channel.error
async def counting_channel_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Du brauchst Admin Rechte für diesen Befehl')
    else:
        raise error


@bot.command(name='log_channel')
@commands.has_permissions(administrator=True)
async def log_channel(ctx, arg1):
    # print("log_channel")
    channel_id = arg1
    if channel_id == 'help':
        response = f"""
            Ändere den Kanal in dem Log Einträge gesendet werden
nutze `{PREFIX}log_channel aktueller_kanal` um im aktuellen Kanal zu loggern 
            """
        await ctx.send(response)
        return
    if channel_id == 'aktueller_kanal':
        channel_id = ctx.channel.id

    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()
    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=channel_id,
                         log_channel_id=channel_id, )
    else:
        guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, old_log_channel_id, greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, channel_id,
                    greedy_message, record, record_user, record_timestamp)
    return


@counting_channel.error
async def counting_channel_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('Leider immernoch nicht genug Rechte')
    else:
        raise error


# -- End Count Master Commands --
# -- Begin Beer Count Commands --
@bot.command(name='beer_count', aliases=['drink_count', 'drinks'])
async def beer_count(ctx, args1=""):
    if not isrightchannel(ctx):
        return
    # print("beer_count")
    if args1 == 'me':
        cursor.execute(
            f"SELECT * FROM beers WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.message.author.id}' ORDER BY count DESC")
        db_results = cursor.fetchall()
    else:
        cursor.execute(f"SELECT * FROM beers WHERE guild_id = '{ctx.guild.id}' ORDER BY count DESC")
        db_results = cursor.fetchall()
    if db_results == [] and args1 == 'me':
        await ctx.send(f"{ctx.message.author.mention} hat noch nichts gewonnen")
        return
    if db_results == []:
        await ctx.send("Bisher hat noch niemand was gewonnen")
        return

    str = ""
    for result in db_results:
        guild_id, user1, user2, count = result
        if user1 == '' or user2 == '':
            continue
        cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{user1}'")
        temp = cursor.fetchone()
        if temp is None:
            drink = "beer"
        else:
            guild_id, user, count_correct, count_wrong, highest_valid_count, last_activity, drink = temp

        str += f"<@{user2}> schuldet <@{user1}> {count} {drink}\n"

    if str != "":
        embed = Embed(title=f"Schuldentabelle {ctx.guild.name}", description=str, color=Color.dark_gold())
        embed.set_footer(text=f"{PREFIX}help")
        await ctx.send(embed=embed)


@bot.command(name='spend_beer')
async def spend_beer(ctx, args1=""):
    if not isrightchannel(ctx):
        return
    owing_user = args1[args1.find("<@&") + 3:args1.find(">")]
    owing_user = int(owing_user.replace("!", ""))
    if args1 == 'help' or args1 == "" or owing_user == "":
        await ctx.send(f"""
        `{PREFIX}spend_beer @user` um Bescheid zu sagen, dass dir dein zustehendes Getränk bezahlt wurde 
        """)
        return
    if args1 == 'me':
        await ctx.send("Nana deinen eigenen Alkoholkonsum kannst du hier nicht abrechnen")
        return
    user = ctx.message.author.id
    # update_beertable(guild_id, user, owed_user, count, second_try=False, spend_beer=False):

    Changed, new_count = update_beertable(ctx.guild.id, user, owing_user, -1, second_try=False, spend_beer=True)
    if Changed == False:
        await ctx.send(f"<@{owing_user}> hat dir zwar nichts geschuldet, aber er lässt Dank ausrichten")
        return
    if new_count == 0:
        await ctx.send(f"<@{owing_user}> und du sind jetzt quitt!")
        return
    await ctx.send(f"Danke für die Info!, <@{owing_user}> schuldet <@{user}> jetzt {new_count} Getränk" + ("e" if new_count > 1 else ""))


@bot.command(name='server')
async def server(ctx):
    if not isrightchannel(ctx):
        return
    # print("server")
    # count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'message', 'channel_id', 'log_channel_id', 'greedy_message', 'record', 'record_user', 'record_timestamp']
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        return

    guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
    timestr = time_since(record_timestamp)
    if last_user == '':
        last_user = 'None'
    else:
        last_user = f"<@{last_user}>"
    message = f"`Aktueller Stand:` {count}\n"
    message += f"`Zuletzt gezählt:` {last_user}\n"
    message += f"`High Score:` {record} ({timestr})\n"
    message += f"`Erreicht von:` <@{record_user}>\n"
    embed = Embed(title=f"Statistiken für {ctx.guild.name}",
                  description=message)
    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)


@bot.command(name='user')
async def user(ctx, arg1=""):
    if not isrightchannel(ctx):
        return
    if arg1 == "":
        user = ctx.message.author.id
        username = ctx.message.author.name
        message = ""
        title = f"Statistiken für {username}"
    else:
        user = arg1[arg1.find("<@&") + 3:arg1.find(">")]
        user = int(user.replace("!", ""))
        title = "Nutzer Statistiken"
        message = f"Ist da jemand? <@{user}>\n"
    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{user}'")
    temp = cursor.fetchone()
    if temp is None:
        if arg1 == "":
            await ctx.send(
                f"<@{user}>, du musst erstmal zählen bevor du deine Statistik anschauen kannst!")
        else:
            await ctx.send(
                f"<@{user}> hat anscheinend noch nie gezählt!")
        return
    else:
        # stat_headers = ['user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity']
        guild_id, user, count_correct, count_wrong, highest_valid_count, last_activity, drink = temp
        percent_correct = round(int(count_correct) / (int(count_correct) + int(count_wrong)) * 100, 2)
        message += f"`Richtig gezählt:` {count_correct}\n"
        message += f"`Verzählt:` {count_wrong}\n"
        message += f"`Prozentual richtig:` {percent_correct} %\n"
        message += f"`Höchste richtige Zahl:` {highest_valid_count}\n"
        message += f"`Zuletzt online:` {time_since(last_activity)}\n"
        message += f"`Lieblingsgetränk:` {drink}\n"
        embed = Embed(title=title,
                      description=message)
        embed.set_footer(text=f"{PREFIX}help")
        await ctx.send(embed=embed)


@bot.command(name='highscore')
async def highscore(ctx):
    if not isrightchannel(ctx):
        return
    # print("highscore")
    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}'  ORDER BY count_correct DESC")
    db_results = cursor.fetchall()
    i = 1
    message = ""
    for result in db_results:
        guild_id, user1, count_correct, count_wrong, highest_valid_count, last_activity, drink = result
        if user1 == '':
            continue
        message += f"<@{user1}>: {count_correct}\n"
        if i == 10:
            break
        i += 1
    if i > 1:
        embed = Embed(title=f"Die Top 10 Zählenden auf {ctx.guild.name} nach Gesamtpunktzahl",
                      description=message, color=Color.green())
        embed.set_footer(text=f"{PREFIX}help")
        await ctx.send(embed=embed)


@bot.command(name='highcount')
async def highcount(ctx):
    if not isrightchannel(ctx):
        return
    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}'  ORDER BY highest_valid_count DESC")
    db_results = cursor.fetchall()
    i = 1
    message = ""
    for result in db_results:
        guild_id, user1, count_correct, count_wrong, highest_valid_count, last_activity, drink = result
        if user1 == '':
            continue
        message += f"<@{user1}>: {highest_valid_count}\n"
        if i == 10:
            break
        i += 1
    if i > 1:
        embed = Embed(title=f"Die Top 10 Zählenden auf {ctx.guild.name} nach höchster gezählter Zahl",
                      description=message, color=Color.green())
        embed.set_footer(text=f"{PREFIX}help")
        await ctx.send(embed=embed)


@bot.command(name='set_drink')
async def set_drink(ctx, arg1=""):
    if not isrightchannel(ctx):
        return
    if arg1 == "":
        await ctx.send("Was ist dein Lieblingsgetränk?")
        return
    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.author.id}'")
    temp = cursor.fetchone()
    if temp is None:
        await ctx.send("Erstmal musst du ein bisschen zählen!")
        return
    else:
        cursor.execute(
            f"UPDATE stats SET drink = '{arg1}' WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.author.id}'")
        connection.commit()
        await ctx.send(f"{ctx.author.name}s Lieblingsgetränk ist jetzt {arg1} PROST!")


@bot.command(name='delete_me')
async def delete_me(ctx):
    if not isrightchannel(ctx):
        return
    cursor.execute(f"DELETE FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.author.id}'")
    connection.commit()
    await ctx.message.add_reaction("😞")
    await ctx.send(f"{ctx.author.name} wurde aus der Datenbank gelöscht")


@bot.command(name='copy_data')
async def copy_data(ctx, arg1=""):
    if not isrightchannel(ctx):
        return
    if arg1 == "":
        await ctx.send("Bitte gib die Nachrichten ID an")
        return
    cursor.execute(f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.author.id}'")
    temp = cursor.fetchone()
    if temp is not None:
        await ctx.send(f"Dafür musst du erst mit `{PREFIX}delete_me` deine Statistik löschen (tut auch gar nicht weh) ")
        return
    counting_bot_mssg = await ctx.channel.fetch_message(int(arg1))
    
    counting_bot_mssg_content = counting_bot_mssg.content
    username = counting_bot_mssg.embeds[0].title
    if username != ctx.author.name + "#" + ctx.author.discriminator:
        await ctx.send("Sneaky you! These stats aren't yours!")
        return
    value = counting_bot_mssg.embeds[0].fields[1].value.split("\n")
    # get number from "Total correct: **2**"
    total_correct = int(value[1].split("**")[1].replace("**", ""))
    # get number from "Total wrong: **1**"
    total_wrong = int(value[2].split("**")[1].replace("**", ""))
    # get number from 'Highest Valid Count: **1 (24s ago)**'
    highest_valid_count = int(value[4].split("**")[1].split(" ")[0])

    # Insert data into database
    last_activity = datetime.now()
    cursor.execute(
        f"INSERT INTO stats (guild_id, user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{ctx.guild.id}', '{ctx.author.id}', '{total_correct}', '{total_wrong}', '{highest_valid_count}', '{last_activity}', 'beer')")
    connection.commit()
    await ctx.send(
        f"{ctx.author.name}, willkommen zur Party\n<@{counting_bot_mssg.author.id}> hat dein Lieblingsgetränk leider akkustisch nicht mitbekommen. Probiers nochmal mit `{PREFIX}set_drink`")

        


# -- Begin Edit Detection --
## doesn't work yet...........
@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        cursor.execute(f"SELECT * FROM count_info WHERE guild_id = '{after.guild.id}'")
        temp = cursor.fetchone()
        if temp == None:
            return
        try:
            changed_count, trash = before.content.split(' ', 1)
        except ValueError:
            changed_count = before.content
        try:
            changed_count = int(changed_count)
        except ValueError:
            return

        guild_id, old_count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
        if int(last_user) != int(after.author.id) or changed_count != int(old_count):
            return
        await after.add_reaction('😡')
        await after.reply(
            f"HALT STOP, <@{after.author.id}> hat die Nachricht bearbeitet. Die nächste Zahl ist eigentlich {str(int(old_count) + 1)}")


@bot.event
async def on_message_delete(message):
    cursor.execute(f"SELECT * FROM count_info WHERE guild_id = '{message.guild.id}'")
    temp = cursor.fetchone()
    if temp == None:
        return
    try:
        changed_count, trash = message.content.split(' ', 1)
    except ValueError:
        changed_count = message.content
    try:
        changed_count = int(changed_count)
    except ValueError:
        return

    guild_id, old_count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
    if int(last_user) != int(message.author.id) or changed_count != int(old_count):
        return
    await message.channel.send(
        f"HALT STOP, <@{message.author.id}> hat eine Zahl gelöscht. Weiter geht's mit {int(old_count) + 1}")


# -- Send error to bloedboemmel- server --
@bot.event
async def on_message_error(ctx, error):
    if isinstance(error, ext.commands.errors.CommandNotFound):
        return
    embed = Embed(title=f"Please help", url="https://github.com/bloedboemmel/Discord-Counting-Bot",
                      description="Äh ja, jetzt ist hier etwas ziemlich schief gelaufen... Im Idealfall sitzt schon ein Nerd dran. Falls du auch manchmal so genannt wirst (warum auch immer) schau doch mal auf GitHub ob du helfen kannst!",
                      color=Color.red())
    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)
    channel = bot.get_channel(910230898115506226)
    await channel.send(ctx.command) # I am trying to send the command with error here
    await channel.send(error)
    raise error

    
# -- Begin counting detection --


# temp: Hardcode solution bis Datenbank es unterstuetzt
# TODO: Admin-only Command um PRO_ROLE_ID zu setzen
PRO_ROLE_ID = 909158530039300126
# TODO: Admin-only Command um PRO_ROLE_THRESHOLD zu setzen
PRO_ROLE_THRESHOLD = 50

@bot.event
async def on_message(_message):
    ctx = await bot.get_context(_message)
    if ctx.message.author.bot:
        return
    if str(_message.content).startswith(str(PREFIX)):
        await bot.invoke(ctx)
        return
    try:
        current_count, trash = _message.content.split(' ', 1)
    except ValueError:
        current_count = _message.content
    try:
        current_count = int(current_count)
    except ValueError:
        return
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % _message.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        return
    else:
        # print(temp[5])
        # print(_message.channel.id)
        if str(temp[5]) != str(ctx.channel.id):
            return
        else:
            old_count = int(temp[1])
            if str(ctx.message.author.id) == str(temp[3]):
                # print("greedy")
                guild_id, old_count, old_number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
                count = str(0)
                number_of_resets = str(int(old_number_of_resets) + 1)
                last_user = str('')
                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id,
                            greedy_message, record, record_user, record_timestamp)

                await ctx.send(str(greedy_message).replace("{{{user}}}", '<@%s>' % str(ctx.message.author.id)))

                await ctx.message.add_reaction('🇸')
                await ctx.message.add_reaction('🇭')
                await ctx.message.add_reaction('🇦')
                await ctx.message.add_reaction('🇲')
                await ctx.message.add_reaction('🇪')
                channel = bot.get_channel(int(log_channel_id))
                await channel.send('<@%s> hat bei %s zwei hintereinander gezählt' % (ctx.message.author.id, old_count))

                return
            if old_count + 1 != current_count:
                # FALSCHE GEZÄHLT
                guild_id, old_count, old_number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
                count = str(0)
                number_of_resets = str(int(old_number_of_resets) + 1)
                last_user = str('')
                beers_last_user = str(ctx.message.author.id)
                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id,
                            greedy_message, record, record_user, record_timestamp)

                await ctx.send(str(temp[4]).replace("{{{user}}}", '<@%s>' % str(ctx.message.author.id)))

                channel = bot.get_channel(int(temp[6]))

                await ctx.message.add_reaction('❌')
                if old_count != 0 and old_last_user != '':
                    await channel.send(
                        '<@%s> hat es bei %s verkackt und schuldet <@%s> jetzt ein Getränk!' % (
                        ctx.message.author.id, str(old_count + 1), old_last_user))
                    update_beertable(guild_id, old_last_user, beers_last_user, +1)

                update_stats(guild_id, beers_last_user, correct_count=False)
                
                return
            if old_count + 1 == current_count:
                # RICHTIG GEZÄHLT
                guild_id, old_count, number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp

                count = str(current_count)
                last_user = str(ctx.message.author.id)
                if int(record) < current_count:
                    record = count
                    record_user = str(ctx.message.author.id)
                    record_timestamp = datetime.now()
                    await ctx.message.add_reaction('☑️')
                else:
                    await ctx.message.add_reaction('✅')

                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id,
                            greedy_message, record, record_user, record_timestamp)
                update_stats(guild_id, ctx.message.author.id, current_number=current_count)
                
                # auf PRO_ROLE prüfen
                cursor.execute(
                    f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.message.author.id}'")
                temp = cursor.fetchone()
                if temp is None:
                    # hat wohl noch nie gezaehlt
                    return
                else:
                    guild_id, msg_user, count_correct, count_wrong, highest_valid_count, last_activity, drink = temp
                    if count_correct >= PRO_ROLE_THRESHOLD:
                        role = get(bot.get_guild(ctx.guild.id).roles, id=PRO_ROLE_ID)
                        await msg_user.add_roles(role)
                return
            return


# -- Begin Initialization code --
check_if_table_exists(DbName, 'count_info', count_info_headers)
check_if_table_exists(DbName, f'stats', stat_headers)
check_if_table_exists(DbName, f'beers', beer_headers)
bot.run(TOKEN)
# -- End Initialization code --
