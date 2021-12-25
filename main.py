import asyncio
import sqlite3
import os
import random
from discord.client import Client
from discord.enums import Enum
from dotenv import load_dotenv
from discord.ext import commands, tasks
from discord import Intents, Embed, Color, guild, message, ext, Activity, Game, ActivityType
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
count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'channel_id', 'log_channel_id',
                      'record', 'record_user', 'record_timestamp',
                      'pro_role_threshold', 'pro_role_id', 'pro_channel_id', 'pro_current_count',
                      'pro_number_of_resets', 'pro_last_user', 'pro_record', 'pro_record_user', 'pro_record_timestamp']
stat_headers = ['guild_id', 'user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity', 'drink']
beer_headers = ['guild_id', 'user', 'owed_user', 'count']
connection = sqlite3.connect(DbName)
cursor = connection.cursor()


class count_type(Enum):
    NOTHING = 0
    RIGHT = 1
    WRONG = 2
    GREEDY = 3


class COUNT_INFO():
    exists = False
    guild_id = None

    current_count = 0
    number_of_resets = 0
    last_user = None
    channel_id = None
    log_channel_id = None
    record = 0
    record_user = None
    record_timestamp = None
    pro_role_threshold = 100000000000000000
    pro_role_id = None
    pro_channel_id = None
    pro_current_count = 0
    pro_number_of_resets = 0
    pro_last_user = None
    pro_record = 0
    pro_record_user = None
    pro_record_timestamp = None

    def __init__(self, guild_id):
        self.guild_id = guild_id
        temp = self.get_count_info(guild_id)
        if temp is None:
            return
        self.exists = True
        self.current_count = temp[1]
        self.number_of_resets = temp[2]
        self.last_user = temp[3]
        self.channel_id = temp[4]
        self.log_channel_id = temp[5]
        self.record = temp[6]
        self.record_user = temp[7]
        self.record_timestamp = temp[8]
        self.pro_role_threshold = temp[9]
        self.pro_role_id = temp[10]
        self.pro_channel_id = temp[11]
        self.pro_current_count = temp[12]
        self.pro_number_of_resets = temp[13]
        self.pro_last_user = temp[14]
        self.pro_record = temp[15]
        self.pro_record_user = temp[16]
        self.pro_record_timestamp = temp[17]

    def get_count_info(self, guild_id):
        cursor.execute(f"SELECT * FROM count_info WHERE guild_id = {guild_id}")
        temp = cursor.fetchone()
        if temp is None:
            return None
        return temp

    def is_log_channel(self, ctx):
        if self.log_channel_id is None:
            return False
        if int(self.log_channel_id) != int(ctx.channel.id):
            return False
        return True

    def is_count_channel(self, ctx):
        if self.channel_id is None:
            return False
        if int(self.channel_id) != int(ctx.channel.id):
            return False
        return True

    def is_pro_channel(self, ctx):
        if self.pro_channel_id is None:
            return False
        if int(self.pro_channel_id) != int(ctx.channel.id):
            return False
        return True

    def create_new_entry(self, ctx):

        temp1 = [
            ctx.guild.id,  # guild_id
            0,  # current_count
            0,  # number_of_resets
            None,  # last_user
            ctx.channel.id,  # channel_id
            ctx.channel.id,  # log_channel_id
            0,  # record
            None,  # record_user
            None,  # record_timestamp
            100000000000000000,  # pro_role_threshold
            None,  # pro_role_id
            None,  # pro_channel_id
            0,  # pro_current_count
            0,  # pro_number_of_resets
            None,  # pro_last_user
            0,  # pro_record
            None,  # pro_record_user
            None  # pro_record_timestamp
        ]
        cursor.execute("INSERT INTO count_info VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", temp1)
        connection.commit()
        return True

    # info = [guild_id, current_count, number_of_resets, last_user, channel_id, log_channel_id, record, record_user, record_timestamp, pro_role_id, pro_channel_id, pro_current_count, pro_number_of_resets, pro_last_user, pro_record, pro_record_user, pro_record_timestamp]
    def update_info(self, count=-1, number_of_resets=-1, last_user=None, channel_id=None, log_channel_id=None,
                    record=-1, record_user=None, record_timestamp=None, pro_role_threshold=-1, pro_role_id=None,
                    pro_channel_id=None, pro_current_count=-1, pro_number_of_resets=-1, pro_last_user=None,
                    pro_record=-1, pro_record_user=None, pro_record_timestamp=None):
        temp = [
            self.guild_id,  # guild_id
            self.current_count if count == -1 else count,  # current_count
            self.number_of_resets if number_of_resets == -1 else number_of_resets,  # number_of_resets
            self.last_user if last_user is None else last_user,  # last_user
            self.channel_id if channel_id is None else channel_id,  # channel_id
            self.log_channel_id if log_channel_id is None else log_channel_id,  # log_channel_id
            self.record if record == -1 else record,  # record
            self.record_user if record_user is None else record_user,  # record_user
            self.record_timestamp if record_timestamp is None else record_timestamp,  # record_timestamp
            self.pro_role_threshold if pro_role_threshold == -1 else pro_role_threshold,  # pro_role_threshold
            self.pro_role_id if pro_role_id is None else pro_role_id,  # pro_role_id
            self.pro_channel_id if pro_channel_id is None else pro_channel_id,  # pro_channel_id
            self.pro_current_count if pro_current_count == -1 else pro_current_count,  # pro_current_count
            self.pro_number_of_resets if pro_number_of_resets == -1 else pro_number_of_resets,  # pro_number_of_resets
            self.pro_last_user if pro_last_user is None else pro_last_user,  # pro_last_user
            self.pro_record if pro_record == -1 else pro_record,  # pro_record
            self.pro_record_user if pro_record_user is None else pro_record_user,  # pro_record_user
            self.pro_record_timestamp if pro_record_timestamp is None else pro_record_timestamp  # pro_record_timestamp
        ]
        cursor.execute(
            f"UPDATE count_info SET guild_id = ?,current_count = ?, number_of_resets = ?, last_user = ?, channel_id = ?, log_channel_id = ?, record = ?, record_user = ?, record_timestamp = ?, pro_role_threshold = ?, pro_role_id = ?, pro_channel_id = ?, pro_current_count = ?, pro_number_of_resets = ?, pro_last_user = ?, pro_record = ?, pro_record_user = ?, pro_record_timestamp = ? WHERE guild_id = {self.guild_id}",
            temp)
        connection.commit()
        return True


# -- Begin SQL Helper Functions --
def create_table(dbname, tablename, tableheader):
    try:
        cursor.execute("CREATE TABLE %s%s" % (tablename, tuple(tableheader)))
        connection.commit()
        return
    except sqlite3.OperationalError:
        return


def insert_values_into_table(dbname, tablename, values):
    if os.path.exists(dbname) is True:
        cursor.execute("INSERT INTO %s VALUES %s" % (tablename, tuple(values)))
        connection.commit()


def check_if_table_exists(dbname, tablename, tableheaders):
    try:
        cursor.execute("SELECT * FROM %s" % tablename)
    except sqlite3.OperationalError:
        create_table(dbname, tablename, tableheaders)


def time_since(strtime):
    now = datetime.now()
    try:
        then = datetime.strptime(strtime, '%Y-%m-%d %H:%M:%S.%f')
    except:
        return ""
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


def update_stats(ctx, guild_id, user, correct_count=True, current_number=1, drink=""):
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
        highest_valid_count = temp[4]
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


# -- End SQL Helper Functions --


# -- Begin Count Master Commands --
bot.remove_command('help')


@bot.command(name='help')
async def count_help(ctx):
    embed = Embed(title="Der Zählbierboter", url="https://github.com/bloedboemmel/Discord-Counting-Bot",
                  description="Alle Befehle",
                  color=Color.purple())
    embed.set_thumbnail(url="https://pbs.twimg.com/media/D9x2dXnWsAgrqN7.jpg")
    if ctx.author.guild_permissions.administrator is True:
        message = f"`{PREFIX}counting_channel aktueller_kanal` um den Zählfortschritt in diesem Kanal zu kontrollieren\n"
        message += f"`{PREFIX}counting_channel @anderer_kanal` um den Kanal in dem gezählt wird zu ändern\n"
        message += f"`{PREFIX}log_channel aktueller_kanal` um den Kanal mit Log Nachrichten zu ändern\n"
        message += f"`{PREFIX}log_channel @anderer_kanal` um den Kanal mit Log Nachrichten zu ändern\n"
        message += f"`{PREFIX}pro_channel aktueller_kanal` um den Kanal für Profis zu ändern\n"
        message += f"`{PREFIX}pro_channel @anderer_kanal` um den Kanal für Profis zu ändern\n"
        message += f"`{PREFIX}pro_role @rolle` um die Rolle für Profis zu ändern\n"
        message += f"`{PREFIX}pro_threshold anzahl` um den Threshold zur Profi-Berechtigung zu ändern\n"
        message += f"`{PREFIX}admin_info` zeigt dir die aktuellen Werte der obigen Variablen an\n"
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
    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)
    return


@bot.command(name='admin_info')
@commands.has_permissions(administrator=True)
async def admin_info(ctx):
    try:
        info = COUNT_INFO(ctx.guild.id)
        message = f"counting_channel: <#{info.channel_id}>\n"
        message += f"log_channel: <#{info.log_channel_id}>\n"
        message += f"pro_channel: <#{info.pro_channel_id}>\n"
        message += f"pro_role: <@&{info.pro_role_id}>\n"
        message += f"pro_threshold: {info.pro_role_threshold}"
        embed = Embed(title="Aktuelle Konfiguration",
                      description=message,
                      color=Color.purple())
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
    return


@bot.command(name='counting_channel')
@commands.has_permissions(administrator=True)
async def counting_channel(ctx, arg1):
    # print("counting_channel")
    try:
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

        info = COUNT_INFO(ctx.guild.id)

        if info.exists is False:
            info.create_new_entry(ctx)
        else:
            info.update_info(channel_id=channel_id)
        await ctx.message.add_reaction('✔')
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
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
    try:
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
        else:
            channel_id = channel_id.split("<#")[1].split(">")[0]

        info = COUNT_INFO(ctx.guild.id)
        if info.exists is False:
            info.create_new_entry(ctx)
            info.update_info(log_channel_id=channel_id)
        else:
            info.update_info(log_channel_id=channel_id)
        await ctx.message.add_reaction('✔')
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
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
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
    await ctx.send(f"Danke für die Info!, <@{owing_user}> schuldet <@{user}> jetzt {new_count} Getränk" + (
        "e" if new_count > 1 else ""))


@bot.command(name='server')
async def server(ctx):
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
        return

    info = COUNT_INFO(ctx.guild.id)
    if info.exists == False:
        await ctx.send("Dieser Server hat noch keine Stats")
        return
    timestr = time_since(info.record_timestamp)
    if info.last_user is None:
        last_user = 'None'
    else:
        last_user = f"<@{info.last_user}>"
    embed = Embed(title=f"Statistiken für {ctx.guild.name}")
    message = f"`Aktueller Stand:` {info.current_count}\n"
    message += f"`Zuletzt gezählt:` {last_user}\n"
    message += f"`High Score:` {info.record} ({timestr})\n"
    message += f"`Erreicht von:` <@{info.record_user}>\n"
    if info.pro_channel_id is None:
        embed.add_field(name="Server Stats", value=message, inline=False)
    else:
        embed.add_field(name="Die Normalos", value=message, inline=False)
        message = f"`Aktueller Stand:` {info.pro_current_count}\n"
        timestr = time_since(info.pro_record_timestamp)
        if info.pro_last_user is None:
            last_user = 'None'
        else:
            last_user = f"<@{info.pro_last_user}>"
        message += f"`Zuletzt gezählt:` {last_user}\n"
        message += f"`High Score:` {info.pro_record} ({timestr})\n"
        message += f"`Erreicht von:` <@{info.pro_record_user}>\n"
        embed.add_field(name="Die Profis", value=message, inline=False)

    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)


@bot.command(name='user')
async def user(ctx, arg1=""):
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
        await ctx.send(f"{ctx.author.name}s Lieblingsgetränk ist jetzt '{arg1}'. PROST!")


@bot.command(name='delete_me')
async def delete_me(ctx):
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
        return
    cursor.execute(f"DELETE FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.author.id}'")
    connection.commit()
    await ctx.message.add_reaction("😞")
    await ctx.send(f"{ctx.author.name} wurde aus der Datenbank gelöscht")


@bot.command(name='copy_data')
async def copy_data(ctx, arg1=""):
    if not COUNT_INFO(ctx.guild.id).is_log_channel(ctx):
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
        await ctx.send("Na, sag einmal. Geklaut wird hier nicht! Das sind nicht deine Daten!")
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


@bot.command(name='pro_channel')
@commands.has_permissions(administrator=True)
async def pro_channel(ctx, arg1):
    try:
        # print("log_channel")
        channel_id = arg1
        if channel_id == 'help':
            response = f"""
                Ändere den Kanal für den Pro Chanel gesendet werden
                nutze `{PREFIX}pro_channel aktueller_kanal` um im aktuellen Kanal die Bosse zählen zu lassen
                """
            await ctx.send(response)
            return
        if channel_id == 'aktueller_kanal':
            channel_id = ctx.channel.id
        else:
            channel_id = channel_id.split("<#")[1].split(">")[0]
        info = COUNT_INFO(ctx.guild.id)
        if info.exists is False:
            info.create_new_entry(ctx)
            info.update_info(pro_channel_id=channel_id)
        else:
            info.update_info(pro_channel_id=channel_id)
        await ctx.message.add_reaction('✔')
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
    return


@bot.command(name='pro_role')
@commands.has_permissions(administrator=True)
async def pro_role(ctx, args1):
    # print("log_channel")
    try:
        if args1 == 'help':
            response = f"""
                Ändere den Kanal für den Pro Chanel gesendet werden
                nutze `{PREFIX}pro_role @role` um die ProRole festzulegen
                """
            await ctx.send(response)
            return
        args1 = args1[args1.find("<@&") + 3:args1.find(">")]
        role_id = int(args1.replace("!", ""))

        info = COUNT_INFO(ctx.guild.id)
        if info.exists == False:
            COUNT_INFO(ctx.guild.id).create_new_entry(ctx)
            COUNT_INFO(ctx.guild.id).update_info(pro_role_id=role_id)
        else:
            COUNT_INFO(ctx.guild.id).update_info(pro_role_id=role_id)
        await ctx.message.add_reaction('✔')
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
    return


@bot.command(name='pro_threshold')
@commands.has_permissions(administrator=True)
async def pro_threshold(ctx, arg1):
    try:
        if arg1 == 'help':
            response = f" Setze die Zahl, ab der ein User als Pro ist"
            await ctx.send(response)
            return
        if arg1 == '':
            await ctx.send("Bitte gib eine Zahl an")
            return
        try:
            arg1 = int(arg1)
        except:
            await ctx.send("Bitte gib eine Zahl an")
            return
        info = COUNT_INFO(ctx.guild.id)
        if info.exists == False:
            COUNT_INFO(ctx.guild.id).create_new_entry(ctx)
            COUNT_INFO(ctx.guild.id).update_info(pro_role_threshold=arg1)
        else:
            COUNT_INFO(ctx.guild.id).update_info(pro_role_threshold=arg1)
        await ctx.message.add_reaction('✔')
    except Exception as e:
        await ctx.message.add_reaction('❌')
        raise e
    return


# -- Begin Edit Detection --
@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        info = COUNT_INFO(before.guild.id)

        if info.exists is False or (info.is_count_channel(after) or info.is_pro_channel(after)) is False:
            return
        try:
            changed_count, trash = before.content.split(' ', 1)
        except ValueError:
            changed_count = before.content
        try:
            changed_count = int(changed_count)
        except ValueError:
            return
        if info.is_count_channel(after):
            if int(info.last_user) != int(after.author.id) or changed_count != int(info.current_count):
                return
            old_count = int(info.current_count)
        if info.is_pro_channel(after):
            if int(info.pro_last_user) != int(after.author.id) or changed_count != int(info.pro_current_count):
                return
            old_count = int(info.pro_current_count)
        await after.add_reaction('😡')
        await after.reply(
            f"HALT STOP, <@{after.author.id}> hat die Nachricht bearbeitet. Die nächste Zahl ist eigentlich {str(int(old_count) + 1)}")


@bot.event
async def on_message_delete(message):
    info = COUNT_INFO(message.guild.id)
    if info.exists is False:
        return
    try:
        changed_count, trash = message.content.split(' ', 1)
    except ValueError:
        changed_count = message.content
    try:
        changed_count = int(changed_count)
    except ValueError:
        return

    if info.is_count_channel(message):
        if int(info.last_user) != int(message.author.id) or changed_count != int(info.current_count):
            return
        old_count = int(info.current_count)
    if info.is_pro_channel(message):
        if int(info.pro_last_user) != int(message.author.id) or changed_count != int(info.pro_current_count):
            return
        old_count = int(info.pro_current_count)
    await message.channel.send(
        f"HALT STOP, <@{message.author.id}> hat eine Zahl gelöscht. Weiter geht's mit {int(old_count) + 1}")


# -- Send error to bloedboemmel- server --
@bot.event
async def on_command_error(ctx, error):
    on_message_error(ctx, error)
@bot.event
async def on_message_error(ctx, error):
    if isinstance(error, ext.commands.errors.CommandNotFound):
        return
    embed = Embed(title=f"Please help", url="https://github.com/bloedboemmel/Discord-Counting-Bot",
                  description="Äh ja, jetzt ist hier etwas ziemlich schief gelaufen... Im Idealfall sitzt schon ein Nerd dran. Falls du auch manchmal so genannt wirst (warum auch immer) schau doch mal auf GitHub ob du helfen kannst!",
                  color=Color.red())
    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)
    try:
        channel = bot.get_channel(910230898115506226)
        await channel.send(ctx.command)  # I am trying to send the command with error here
        await channel.send(error)
    except:
        pass

    raise error


# -- Begin counting detection --

lock = asyncio.Lock()
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
    info = COUNT_INFO(_message.guild.id)
    if info.exists is False:
        return
    else:
        async with lock:
            if info.is_count_channel(_message):
                reaction = ['☑️'] if int(info.record) < current_count else ['✅']  # such enterprise code, much wow
            elif info.is_pro_channel(_message):
                reaction = ['☑️'] if int(info.pro_record) < current_count else ['✅']
            else:
                return
            # ein paar WiTzIgE reactions
            if current_count == 100:
                reaction = ['💯']
            elif current_count == 420:
                reaction = ['🍁']
            elif current_count == 333:
                reaction = ['🔺', '👁']
            elif current_count == 666:
                reaction = ['👹']
            elif current_count == 1234:
                reaction = ['🔢']
            # und ein paar SeLtEnE WiTziGe reactions
            elif current_count == 1:
                if random.random() > 0.9:
                    reaction = ['☝']
            elif current_count == 5:
                if random.random() > 0.9:
                    reaction = ['🖐️']
            elif current_count == 69:
                if random.random() > 0.75:
                    reaction = ['🇳', '🇮', '🇨', '🇪']

            count_option = count_type.NOTHING
            
            if info.is_count_channel(_message):
                old_count = int(info.current_count)
                if str(ctx.message.author.id) == str(info.last_user):
                    info.update_info(count=0, number_of_resets=info.number_of_resets + 1, last_user='')
                    count_option = count_type.GREEDY
                elif old_count + 1 != current_count:
                    # FALSCHE GEZÄHLT
                    last_user = info.last_user
                    info.update_info(count=0, number_of_resets=info.number_of_resets + 1, last_user='')
                    count_option = count_type.WRONG
                elif old_count + 1 == current_count:
                    # RICHTIG GEZÄHLT

                    count = str(current_count)
                    last_user = str(ctx.message.author.id)
                    if int(info.record) < current_count:
                        record = count
                        record_user = str(ctx.message.author.id)
                        record_timestamp = datetime.now()
                        for r in reaction:
                            await ctx.message.add_reaction(r)
                        info.update_info(count=current_count, last_user=last_user, record=record, record_user=record_user,
                                        record_timestamp=record_timestamp)
                    else:
                        for r in reaction:
                            await ctx.message.add_reaction(r)
                        info.update_info(count=current_count, last_user=last_user)

                    count_option = count_type.RIGHT
                    # auf PRO_ROLE prüfen
                    cursor.execute(
                        f"SELECT * FROM stats WHERE guild_id = '{ctx.guild.id}' AND user = '{ctx.message.author.id}'")
                    temp = cursor.fetchone()
                    if temp is not None and info.pro_role_id is not None:
                        guild_id, msg_user, count_correct, count_wrong, highest_valid_count, last_activity, drink = temp
                        if int(count_correct) >= int(info.pro_role_threshold):
                            role = get(bot.get_guild(ctx.guild.id).roles, id=info.pro_role_id)
                            if role is not None and get(ctx.message.author.roles, id=info.pro_role_id) is None:
                                member = ctx.message.author
                                await member.add_roles(role)
                                await ctx.message.add_reaction('🎉')
                                log_channel = bot.get_channel(int(info.log_channel_id))
                                log_channel = ctx if log_channel is None else log_channel
                                await log_channel.send(
                                    f"<@{ctx.message.author.id}> hat die PRO-Rolle erhalten und darf jetzt bei den Großen mitspielen!")
            elif info.is_pro_channel(_message):
                old_count = int(info.pro_current_count)
                if str(ctx.message.author.id) == str(info.pro_last_user):
                    info.update_info(pro_current_count=0, pro_number_of_resets=info.pro_number_of_resets + 1,
                                    pro_last_user='')
                    count_option = count_type.GREEDY
                elif old_count + 1 != current_count:
                    # FALSCHE GEZÄHLT
                    last_user = info.pro_last_user
                    info.update_info(pro_current_count=0, pro_number_of_resets=info.pro_number_of_resets + 1,
                                    pro_last_user='')
                    count_option = count_type.WRONG
                elif old_count + 1 == current_count:
                    # RICHTIG GEZÄHLT
                    count = str(current_count)
                    last_user = str(ctx.message.author.id)
                    if int(info.pro_record) < current_count:
                        record = count
                        record_user = str(ctx.message.author.id)
                        record_timestamp = datetime.now()
                        for r in reaction:
                            await ctx.message.add_reaction(r)
                        info.update_info(pro_current_count=current_count, pro_last_user=last_user, pro_record=record,
                                        pro_record_user=record_user, pro_record_timestamp=record_timestamp)
                    else:
                        for r in reaction:
                            await ctx.message.add_reaction(r)
                        info.update_info(pro_current_count=current_count, pro_last_user=last_user)
                    count_option = count_type.RIGHT

            if count_option == count_type.GREEDY:
                await ctx.send(f'Nanana, <@{ctx.message.author.id}> hat es etwas eilig. Dann starten wir halt von vorne')
                await ctx.message.add_reaction('🇸')
                await ctx.message.add_reaction('🇭')
                await ctx.message.add_reaction('🇦')
                await ctx.message.add_reaction('🇲')
                await ctx.message.add_reaction('🇪')
                channel = bot.get_channel(int(info.log_channel_id))
                await channel.send(
                    f'<@{ctx.message.author.id}> hat in {ctx.channel.mention} bei {old_count} zwei hintereinander gezählt')

                return
            elif count_option == count_type.WRONG:

                channel = bot.get_channel(info.log_channel_id)
                await ctx.message.add_reaction('❌')
                if old_count != 0 and info.last_user != '':
                    if old_count > 19:
                        await ctx.send(
                            f'Mööööp, <@{ctx.message.author.id}> hat falsch gezählt und schuldet <@{info.last_user}> jetzt ein Getränk!')
                        update_beertable(info.guild_id, info.last_user, ctx.message.author.id, +1)
                    else:
                        await ctx.send(
                            f'Mööööp, <@{ctx.message.author.id}> hat falsch gezählt, schuldet allerdings niemandem ein Getränk.')
                elif current_count == 0:
                    await ctx.send(
                        f'<@{ctx.message.author.id}>, du magst zwar Informatiker-Jokes witzig finden, aber wir beginnen immer noch bei 1')
                else:
                    await ctx.send(f'<@{ctx.message.author.id}>, Fun Fact: Wir starten bei 1')
                update_stats(ctx, info.guild_id, ctx.message.author.id, correct_count=False)
            elif count_option == count_type.RIGHT:
                update_stats(ctx, info.guild_id, ctx.message.author.id, current_number=current_count)


@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print('------')
    changepresence.start()


@tasks.loop(seconds=300)  # How often the bot should change status, mine is set on every 40 seconds
async def changepresence():
    game = [
        Game(name="Pferderennen"),
        Game(name="Busfahren"),
        Activity(type=ActivityType.listening, name="Radler ist kein Alkohol"),
        Activity(type=ActivityType.streaming, name="https://www.youtube.com/watch?v=dQw4w9WgXcQ", platform="YouTube"),
        Activity(type=ActivityType.watching, name="2 Girls, 1 Cup"),
        Game(name="Kingscup"),
        Activity(type=ActivityType.listening, name="Mallorca (Da bin ich daheim"),
        Activity(type=ActivityType.listening, name="Ham kummst!"),
        Activity(type=ActivityType.competing, name="Naked Mile"),
        Game(name=f"{PREFIX}help")
    ]

    x = game[random.randint(0, len(game) - 1)]

    await bot.change_presence(activity=x)


# -- Begin Initialization code --
check_if_table_exists(DbName, 'count_info', count_info_headers)
check_if_table_exists(DbName, f'stats', stat_headers)
check_if_table_exists(DbName, f'beers', beer_headers)
bot.run(TOKEN)
# -- End Initialization code --
