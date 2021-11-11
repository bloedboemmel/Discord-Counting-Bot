import sqlite3
import os
from discord.client import Client
from dotenv import load_dotenv
from discord.ext import commands
from discord import Intents, Embed, Color, guild, message
from discord.utils import get
#from keys import discord_key

from datetime import datetime
intents = Intents(messages=True, guilds=True)
load_dotenv()
TOKEN = os.getenv('THE_COUNT_DISCORD_TOKEN')
#TOKEN = discord_key()
#PREFIX = "".join((os.getenv('THE_COUNT_PREFIX'), ' '))
PREFIX = "!count "
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

DbName = 'count.sqlite'
count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'message', 'channel_id', 'log_channel_id', 'greedy_message', 'record', 'record_user', 'record_timestamp']
stat_headers = ['user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity', 'drink']
beer_headers = ['user', 'owed_user', 'count']
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
        return f'{days}d ago'
    elif hours > 0:
        return f'{hours}h ago'
    elif minutes > 0:
        return f'{minutes}m ago'
    else:
        return 'just now'
    


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
                     guild_message=str("{{{user}}} typed the wrong number"),
                     count_channel_id=str(''),
                     log_channel_id=str(''),
                     greedy_message=str("{{{user}}} was too greedy")):
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
    check_if_table_exists(DbName, f'stats_{guild_id}', stat_headers)
    check_if_table_exists(DbName, f'beers_{guild_id}', beer_headers)
    cursor.execute("INSERT INTO count_info %s VALUES %s" % (tuple(count_info_headers), tuple(temp1)))
    connection.commit()
    return

def update_beertable(guild_id, user, owed_user, count, second_try=False, spend_beer=False):
    cursor.execute(f"SELECT * FROM beers_{guild_id} WHERE user = '{user}' AND owed_user = '{owed_user}'")
    temp = cursor.fetchone()
    if temp is None and spend_beer is True:
        return False
    if temp is None:
        if second_try is True:
            cursor.execute(f"INSERT INTO beers_{guild_id} (user, owed_user, count) VALUES ('{owed_user}','{user}', '1')")
            connection.commit()
            return True
        else:
            return update_beertable(guild_id, owed_user, user, -count, second_try=True) #Changed user and owed_user on purpose
        

    else:
        user, owed_user, saved_count = temp
        if saved_count + count <= 0:
            cursor.execute(f"DELETE FROM beers_{guild_id} WHERE user = '{user}' AND owed_user = '{owed_user}'")
            connection.commit()
            return True, 0
        cursor.execute(f"UPDATE beers_{guild_id} SET count = count + {count} WHERE user = '{user}' AND owed_user = '{owed_user}'")
        connection.commit()

        return True, saved_count + count

def update_stats(guild_id, user, correct_count = True, current_number = 1, drink = ""):
    # stat_headers = ['user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity']
    
    cursor.execute(f"SELECT * FROM stats_{guild_id} WHERE user = '{user}'")
    temp = cursor.fetchone()
    last_activity = datetime.now() 
    if drink != "":
        if temp is None:
            if correct_count is True:
                cursor.execute(f"INSERT INTO stats_{guild_id} (user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{user}', '1', '0', '{current_number}', '{last_activity}', 'beer')")
            else:
                cursor.execute(f"INSERT INTO stats_{guild_id} (user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{user}', '0', '1', '{current_number}', '{last_activity}', 'beer')")
            connection.commit()
        else:
            highest_valid_count = temp[3]
            if current_number > int(highest_valid_count):
                highest_valid_count = str(current_number)
            if correct_count is True:
                cursor.execute(f"UPDATE stats_{guild_id} SET count_correct = count_correct + 1, highest_valid_count = ?, last_activity = ? WHERE user = '{user}'", (highest_valid_count, last_activity,))
            else:
                cursor.execute(f"UPDATE stats_{guild_id} SET count_wrong = count_wrong + 1, last_activity = ? WHERE user = '{user}'", (last_activity,))
            connection.commit()
    else:
        if temp is None:
            cursor.execute(f"INSERT INTO stats_{guild_id} (user, count_correct, count_wrong, highest_valid_count, last_activity, drink) VALUES ('{user}', '0', '0', '0', '{last_activity}', '{drink}')")
            connection.commit()
        else:
            cursor.execute(f"UPDATE stats_{guild_id} SET drink = ? WHERE user = '{user}'", (drink,))
            connection.commit()

def update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp,  table_name='count_info'):
    cursor.execute(f"UPDATE {table_name} SET guild_id = ?, current_count = ?, number_of_resets = ?, last_user = ?, message = ?, channel_id = ?, log_channel_id = ?, greedy_message = ?, record = ?, record_user = ?, record_timestamp = ? WHERE guild_id = '{guild_id}'", (guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message,record, record_user, record_timestamp, )) 
    connection.commit()
# -- End SQL Helper Functions --


# -- Begin Count Master Commands --
bot.remove_command('help')


@bot.command(name='help')
async def count_help(ctx):
    response = """See https://github.com/bloedboemmel/Discord-Counting-Bot for detailed help info"""
    await ctx.send(response)
    return


@bot.command(name='wrong_message')
@commands.has_permissions(administrator=True)
async def wrong_message(ctx, *args):
    _message = " ".join(args)
    if _message == 'help':
        response = """
        Set the message to be sent when someone types the wrong number
{{{user}}} will be replaced by the name of whoever typed the wrong number
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
        update_info(guild_id, count, number_of_resets, last_user, _message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp)
    return


@wrong_message.error
async def wrong_message_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You need Admin Permissions to do that command')
    else:
        raise error



@bot.command(name='greedy_message')
@commands.has_permissions(administrator=True)
async def greedy_message(ctx, *args):
    _message = " ".join(args)
    if _message == 'help':
        response = """
        Set the message to be sent when someone types 2 messages in a row
{{{user}}} will be replaced by the name of whoever typed the 2 messages
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
        update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, _message, record, record_user, record_timestamp)
    return


@wrong_message.error
async def wrong_message_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You need Admin rights to run that command')
    else:
        raise error


@bot.command(name='counting_channel')
@commands.has_permissions(administrator=True)
async def counting_channel(ctx, arg1):
    #print("counting_channel")
    channel_id = arg1
    if channel_id == 'help':
        response = """
            Set the id of the channel that you want to count in
use `!count counting_channel this_channel` to use the channel that you are typing in
            """
        await ctx.send(response)
        return
    if channel_id == 'this_channel':
        channel_id = ctx.channel.id
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()
    
    
    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=channel_id,
                         log_channel_id=channel_id,)
    else:
        guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp)
    return


@counting_channel.error
async def counting_channel_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You need Admin rights to run that command')
    else:
        raise error


@bot.command(name='log_channel')
@commands.has_permissions(administrator=True)
async def log_channel(ctx, arg1):
    #print("log_channel")
    channel_id = arg1
    if channel_id == 'help':
        response = """
            Set the id of the channel that you want to log mistakes too
use `!count log_channel this_channel` to use the channel that you are typing in
            """
        await ctx.send(response)
        return
    if channel_id == 'this_channel':
        channel_id = ctx.channel.id
        
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    test = cursor.fetchone()
    if test is None:
        create_new_entry(ctx.guild.id,
                         count_channel_id=channel_id,
                         log_channel_id=channel_id,)
    else:
        guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, old_log_channel_id, greedy_message, record, record_user, record_timestamp = test
        update_info(guild_id, count, number_of_resets, last_user, guild_message, old_channel_id, channel_id, greedy_message, record, record_user, record_timestamp)
    return


@counting_channel.error
async def counting_channel_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send('You need the Admin rights to run that command')
    else:
        raise error

# -- End Count Master Commands --
# -- Begin Beer Count Commands --
@bot.command(name='beer_count')
async def beer_count(ctx, args1 = ""):
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        #print("No log_channel for beer_score")
        return
    elif temp[6] != ctx.channel.id:
        #print("Wrong channel for beer_score")
        return
    #print("beer_count")
    if args1 == 'me':
        cursor.execute(f"SELECT * FROM beers_{ctx.guild.id} WHERE user = '{ctx.message.author.id}' ORDER BY count DESC")
        db_restults = cursor.fetchall()
        str = ""
        for result in db_restults:
            user1, user2, count = result
            if user1 == '' or user2 == '':
                continue
            str +=  f"<@{user2}> ows <@{user1}> {count} beers\n"
        cursor.execute(f"SELECT * FROM beers_{ctx.guild.id} WHERE owed_user = '{ctx.message.author.id}' ORDER BY count DESC")
        db_restults = cursor.fetchall()
        for result in db_restults:
            user1, user2, count = result
            if user1 == '' or user2 == '':
                continue
            str += f"<@{user2}> ows <@{user1}> {count} beers\n"
        await ctx.send(str)
    else:
        cursor.execute(f"SELECT * FROM beers_{ctx.guild.id} ORDER BY count DESC")
        db_restults = cursor.fetchall()
        for result in db_restults:
            user1, user2, count = result
            if user1 == '' or user2 == '':
                continue
            await ctx.send(f"<@{user2}> ows <@{user1}> {count} beers")

@bot.command(name= 'spend_beer')
async def spend_beer(ctx, args1 = ""):
    owing_user = args1[args1.find("<@&")+3:args1.find(">")]
    owing_user = int(owing_user.replace("!", ""))
    if args1 == 'help' or args1 == "" or owing_user == "":
        await ctx.send("""
        `!count spend_beer @user` to register a done forfeit. Make sure to really tag the person
        """)
        return
    if args1 == 'me':
        await ctx.send("Funny you! I won't count your own drinkung habits")
        return
    user = ctx.message.author.id
    #update_beertable(guild_id, user, owed_user, count, second_try=False, spend_beer=False):
   
    Changed, new_count = update_beertable(ctx.guild.id, owing_user, user, -1, second_try=False, spend_beer=True)
    if Changed == False:
        await ctx.send(f"<@{owing_user}> didn't owe you a beer, but it's still great you met up")
        return
    if new_count == 0:
        await ctx.send(f"<@{owing_user}> and you are now all made up!")
        return
    await ctx.send(f"Thanks for the info!, <@{owing_user}> now owes <@{user}> {new_count} beers")

@bot.command(name='server')
async def server(ctx):
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        #print("No valid channel")
        return
    elif temp[6] != ctx.channel.id:
        #print("Wrong channel for server_stats")
        return
    #print("server")
    # count_info_headers = ['guild_id', 'current_count', 'number_of_resets', 'last_user', 'message', 'channel_id', 'log_channel_id', 'greedy_message', 'record', 'record_user', 'record_timestamp']
    guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
    timestr = time_since(record_timestamp)
    if last_user == '':
        last_user = 'None'
    else:
        last_user = f"<@{last_user}>"
    message = f"`Current count:` {count}\n"
    message += f"`Last counted by` {last_user}\n"
    message += f"`High Score:` {highscore} ({timestr})\n"
    message += f"`Counted by` <@{record_user}>\n"
    embed=Embed(title=f"Stats for {ctx.guild.name}", 
                description=message)    
    embed.set_footer(text=f"{PREFIX}help")
    await ctx.send(embed=embed)
    
@bot.command(name='user')
async def user(ctx, arg1 = ""):
    if arg1 == "":
        user = ctx.message.author.id
        username = ctx.message.author.name
        message =""
    else:
        user = arg1[arg1.find("<@&")+3:arg1.find(">")]
        user = int(user.replace("!", ""))
        message = f"Are you even there? <@{user}>\n"
    cursor.execute(f"SELECT * FROM stats_{ctx.guild.id} WHERE user = '{user}'")
    temp = cursor.fetchone()
    if temp is None:
        if arg1 == "":
            await ctx.send(f"<@{user}, you should try counting first!")
        else:
            await ctx.send(f"<@{user}> has to learn counting first and is revisiting school")
        return
    else:
     #stat_headers = ['user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity']
        user, count_correct, count_wrong, highest_valid_count, last_activity, drink = temp
        percent_correct = round(count_correct / (count_correct + count_wrong) * 100, 2)
        message += f"`Count Correct:` {count_correct}\n"
        message += f"`Count Wrong:` {count_wrong}\n"
        message += f"`Percentage Correct:` {percent_correct} %\n"
        message += f"`Highest Valid Count:` {highest_valid_count}\n"
        message += f"`Last Activity:` {time_since(last_activity)}\n"
        message += f"`Favorite Drink:` {drink}\n"
        embed = Embed(title=f"Stats for {username}", 
                      description=message)
        embed.set_footer(text=f"{PREFIX}help")
        await ctx.send(embed=embed)
       

    
@bot.command(name='highscore')
async def highscore(ctx):
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % ctx.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        #print("No log_channel for highscore")
        return
    elif temp[6] != ctx.channel.id:
        #print("Wrong channel for highscore")
        return
    #print("highscore")
    #stat_headers = ['user', 'count_correct', 'count_wrong', 'highest_valid_count', 'last_activity']
    cursor.execute(f"SELECT * FROM stats_{ctx.guild.id} ORDER BY count_correct DESC")
    db_restults = cursor.fetchall()
    i = 1
    for result in db_restults:
        user1, count_correct, count_wrong, highest_valid_count, last_activity, drink = result
        if user1 == '':
            continue
        await ctx.send(f"<@{user1}>: {count_correct}")
        if i == 10:
            break
        i += 1


# -- Begin Edit Detection --
## doesn't work yet...........
@bot.event
async def on_message_edit(before, after):
    if before.content != after.content:
        if 'substring' in after.content:
            print("Thats son of a bitch edited!")

# -- Begin counting detection --
@bot.event
async def on_message(_message):
    ctx = await bot.get_context(_message)
    if ctx.message.author.bot:
        return
    if str(_message.content).startswith(str(PREFIX)):
        await bot.invoke(ctx)
        return
    cursor.execute("SELECT * FROM count_info WHERE guild_id = '%s'" % _message.guild.id)
    temp = cursor.fetchone()
    if temp is None:
        return
    else:
        #print(temp[5])
        #print(_message.channel.id)
        if str(temp[5]) != str(ctx.channel.id):
            return
        else:
            try:
                current_count, trash = _message.content.split(' ', 1)
            except ValueError:
                current_count = _message.content
            current_count = int(current_count)
            old_count = int(temp[1])
            if str(ctx.message.author.id) == str(temp[3] +"test"): #"test" is only for test-purposes
                #print("greedy")
                guild_id, old_count, old_number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
                count = str(0)
                number_of_resets = str(int(old_number_of_resets) + 1)
                last_user = str('')
                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp)

                await ctx.send(str(temp[7]).replace("{{{user}}}", '<@%s>' % str(ctx.message.author.id)))
                channel = bot.get_channel(int(temp[6]))
                await channel.send('<@%s> lost the count when it was at %s' % (ctx.message.author.id, old_count))
                
                await ctx.message.add_reaction('🇸')
                await ctx.message.add_reaction('🇭')
                await ctx.message.add_reaction('🇦')
                await ctx.message.add_reaction('🇲')
                await ctx.message.add_reaction('🇪')
                return
            if old_count + 1 != current_count:
                guild_id, old_count, old_number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
                count = str(0)
                number_of_resets = str(int(old_number_of_resets) + 1)
                last_user = str('')
                beers_last_user = str(ctx.message.author.id)
                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp)

                await ctx.send(str(temp[4]).replace("{{{user}}}", '<@%s>' % str(ctx.message.author.id)))
                
                channel = bot.get_channel(int(temp[6]))
                
                await ctx.message.add_reaction('❌')
                if old_count != 0:
                    await channel.send('<@%s> lost the count when it was at %s and has to give <@%s> a beer!' % (ctx.message.author.id, old_count, old_last_user))
                #if beers_last_user == old_last_user:
                #    return
                    update_beertable(guild_id, beers_last_user, old_last_user, +1)
                update_stats(guild_id, beers_last_user, correct_count=False)
                return
            if old_count + 1 == current_count:
                guild_id, old_count, number_of_resets, old_last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp = temp
                
                count = str(current_count)
                last_user = str(ctx.message.author.id)
                if int(record) < current_count:
                    record = count
                    record_user = str(ctx.message.author.id)
                    record_timestamp = datetime.now()
                update_info(guild_id, count, number_of_resets, last_user, guild_message, channel_id, log_channel_id, greedy_message, record, record_user, record_timestamp)
                update_stats(guild_id, ctx.message.author.id, current_number= current_count)
                await ctx.message.add_reaction('✅')
                return
            return


# -- Begin Initialization code --
check_if_table_exists(DbName, 'count_info', count_info_headers)
bot.run(TOKEN)
# -- End Initialization code --
