import asyncio
import random
import sys
from zoneinfo import ZoneInfo
import discord
import os
from discord.ext import tasks, commands
import json
from datetime import datetime
from datetime import time
import calendar
from discord import Option
from dotenv import load_dotenv
import sqlite3

bdayfile = '/home/ubuntu/discordbot/bdays.json'
role_message_file = '/home/ubuntu/discordbot/rolemessage.json'
logfile = '/home/ubuntu/discordbot/Bot.log'
# DB_PATH = '/home/ubuntu/discordbot/data.db'
DB_PATH = 'data.db'

role_message_id = None

birthdays = []
if os.path.isfile(bdayfile):
    with open(bdayfile, 'r') as file:
        birthdays = json.load(file)

role_message = []
if os.path.isfile(role_message_file):
    with open(role_message_file, 'r') as file:
        try:
            role_json = json.load(file)
            role_message_id = role_json[0]['role_message_id']
        except:
            pass

if not os.path.isfile(logfile):
    f = open(logfile, "x")

load_dotenv(dotenv_path='.env')

# Servers
keksrunde = int(os.environ.get('KEKSRUNDE'))
bot_hoehle = int(os.environ.get('BOTHOEHLE'))

# Channels
keksrunde_hauptchat = int(os.environ.get('KEKSRUNDE_HAUPTCHAT'))
bot_hoehle_channel = int(os.environ.get('BOTHOEHLE_CMD_CHANNEL'))
bot_log = int(os.environ.get('BOTLOG'))

LOCAL_TZ = ZoneInfo("Europe/Berlin")

bot = commands.Bot(command_prefix='/',Intents=discord.Intents.all())

roleWhitelist = {
    "💚": "Green",
    "🍪": "Keksritter",
    "🧟‍♂️": "7Tagesadventisten",
    "🤡": "four clowns walk into a bank ...",
    "⛏️": "Space Rock Junkies",
    "👻": "Phasmocrew",
    "🤖": "Robokiller",
    "👺": "Gamer Gremlins",
    "🏰": "Zivilisation 6",
    "📍": "geo Rätseler",
    "💣": "Gegenschlag 2",
    "<:catft:685124473476743215>": "Gunfire Reborn",
    "🦽": "Free-for-all",
    "🔫": "guntastbar",
    "<:baddragon:863485520721870898>": "bonk"
}

trefferzonen = ["linken Bein", "linken Bein", "linken Bein",
                "rechten Bein", "rechten Bein","rechten Bein",
                "Bauch", "Bauch",
                "linken Arm", "linken Arm", "linken Arm",
                "rechten Arm", "rechten Arm", "rechten Arm",
                "Oberkörper", "Oberkörper", "Oberkörper", "Oberkörper",
                "Kopf", "Kopf"]

salutes = ["Rock on!", "Rock! (burp) And! (burp) Stone! (burp)", "Stone and Rock! Oh, wait?", "For Teamwork!", "Rock and Stone! It never gets old.", "Let's Rock and Stone!",
           "Rock and Stone... Yeeaaahhh!", "", "ROCK! AND! STONE!", "Rock... Solid!", "Galaxy's finest!", "For those about to Rock and Stone, we salute you!",
           "Rock and Stone you beautiful dwarf!", "Rockitty Rock and Stone!", "Gimmie an R! Gimmie an S! Gimmie a Rock. And. Stone!", "We're the best!",
           "If I had a credit for every Rock and Stone.", "Rock and Stone like there's no tomorrow!", "Rock and Stone, the pretty sound of teamwork!", "Gimmie a Rock... and Stone!", 
           "Rock me like a Stone!", "By the Beard!",  "Leave No Dwarf Behind!", "Rock solid!", "Rock and Stone, Brother!", "Rock and Stone to the Bone!", "Rock and Stone everyone!",
           "Come on guys! Rock and Stone!", "None can stand before us!", "Yeaahhh! Rock and Stone!", "Rock and Stone forever!", "Rock and Stone!", "For Rock and Stone!",
           "If you don't Rock and Stone, you ain't comin' home!", "Rock and Stone in the Heart!", "For Karl!", "Did I hear a Rock and Stone?", "We fight for Rock and Stone!",
           "We are unbreakable!", "Rock and roll!", "Rock and roll and stone!", "That's it lads! Rock and Stone!", "Like that! Rock and Stone!"]


async def log(log_message):
    timestamp = datetime.now()
    message = str(timestamp)+" - "+log_message+"\n\n"
    channel = bot.get_channel(bot_log)

    await channel.send(message)
    with open(logfile, 'a') as file:
        file.write(message)


async def on_raw_member_remove(payload):
    guild = bot.get_guild(payload.guild_id)
    leaveMessage = payload.user.name+" just left the server "+guild.name
    await log(leaveMessage)


@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return  # Ignore bot's own reactions
    if payload.message_id != role_message_id:
        return  # Ignore other messages

    guild = bot.get_guild(payload.guild_id)
    member = payload.member
    emoji = str(payload.emoji)

    if emoji in roleWhitelist:
        role = discord.utils.get(guild.roles, name=roleWhitelist[emoji])
        if role:
            await member.add_roles(role)


@bot.event
async def on_raw_reaction_remove(payload: discord.RawReactionActionEvent):
    if payload.user_id == bot.user.id:
        return
    if payload.message_id != role_message_id:
        return

    guild = bot.get_guild(payload.guild_id)
    member = await guild.fetch_member(payload.user_id)
    emoji = str(payload.emoji)

    if emoji in roleWhitelist:
        role = discord.utils.get(guild.roles, name=roleWhitelist[emoji])
        if role:
            await member.remove_roles(role)


@bot.event
async def on_ready():
    await log('Bot started!')
    if not checkBirthday.is_running():
        checkBirthday.start()
    if not checkReminders.is_running():
       checkReminders.start()
    if not checkAlive.is_running():
        checkAlive.start()


# USES TIMEZONE UTC! -1 hour compared to GMT+1/Berlin
@tasks.loop(hours=1)
async def checkAlive():
    if datetime.now().hour != 0:
        return

    channel = bot.get_channel(bot_log)
    await channel.send("I am alive.")


@tasks.loop(time=time(hour=23, minute=3, second=0), reconnect=True)
async def checkBirthday():
    today = datetime.now()
    day = today.day
    month = today.month
    # special handling for "LayDay"
    if day == 8 and month == 8:  
        await channel.send(f"Happy LayDay <@{int(os.environ.get('LAY'))}>!")
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()
    cursor.execute("""
        SELECT id, day, month FROM birthdays
        WHERE day=? AND month=?
    """, (day, month))
    rows = cursor.fetchall()
    connection.close()
    if not rows:
        return
    channel = bot.get_channel(keksrunde_hauptchat)   
    for user_id, _, _ in rows:
        await channel.send(f"Happy Birthday <@{user_id}>!")


@tasks.loop(minutes=1, reconnect=True)
async def checkReminders():
    """Check the database for due reminders and send them."""
    now = datetime.now(LOCAL_TZ)
    connection = sqlite3.connect(DB_PATH)
    cursor = connection.cursor()

    cursor.execute("SELECT id, user_id, channel_id, remind_at, message FROM reminders WHERE remind_at <= ?", (now.isoformat(),))
    rows = cursor.fetchall()
    due_reminders = []
    for reminder_id, user_id, channel_id, remind_at_str, message in rows:
        remind_at = datetime.fromisoformat(remind_at_str)

        if remind_at <= now:  # time reached
            channel = bot.get_channel(channel_id)
            user = await bot.fetch_user(user_id)
            if channel and user:
                await channel.send(f"Reminder by {user.mention}: {message}")

            due_reminders.append(reminder_id)

    if due_reminders:
        cursor.executemany("DELETE FROM reminders WHERE id=?", [(reminder,) for reminder in due_reminders])
        connection.commit()

    connection.close()

@bot.slash_command(guild_ids=[bot_hoehle])
async def hello(ctx):
    name = ctx.author.name
    await ctx.respond(f"Hello {name}, you miserable creature.")


@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Add your birthday as a reminder for your senile friends. Format: dd.mm')
async def add_birthday(
    ctx,
    birthday: Option(str, "Format: dd.mm"),  # type: ignore
    user: Option(discord.User, "Format: dd.mm", required=False)  # type: ignore
):
    if user is None:
        user = ctx.author

    for item in birthdays:
        if user.id in item:
            await ctx.respond("You already added yourself.")
            return

    try:
        if "." in birthday:
            day, _, month = birthday.partition('.')

            if not day.isnumeric() and not month.isnumeric():
                await ctx.respond('Bad formatting. Format: dd.mm')
                return
            
            day = int(day)
            month = int(month)

            if day == 69 or month == 69:
                await ctx.respond("Oh look, we got ourselves a comedian here.")
                return
            elif month > 12 or month < 1:
                await ctx.respond("The year doesn't have " +str(month)+" months.")
                return
            elif month in (1, 3, 5, 7, 8, 10, 12):
                if not 1 <= day <= 31:
                    await ctx.respond(calendar.month_name[month]+" doesn't have "+str(day)+" days." )
                    return
            elif month in (4, 6, 9, 11):
                if not 1 <= day <= 30:
                    await ctx.respond(calendar.month_name[month]+" doesn't have "+str(day)+" days." )
                    return
                else:
                    pass
            elif month == 2:
                if day > 28 or day < 1:
                    await ctx.respond("February doesn't have "+str(day)+" days.")
                    return
                else:
                    pass
            
            if day == 1 and month == 4:
                await ctx.respond("How unfortunate.")

            lock = asyncio.Lock()
            async with lock:
                with open(bdayfile, 'w') as file:
                    birthdays.append({
                        "id": str(user.id),
                        "day": str(day),
                        "month": calendar.month_name[month]
                    })
                    json.dump(birthdays, file)
                    await ctx.respond("Birthday saved for "+user.name)
        else:
            await ctx.respond("Nice job, you broke it. Try again. Format: dd.mm")
            return
    except ValueError:
        await ctx.respond('Bad formatting. Format: dd.mm')


@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Add a reminder for yourself or others.')
async def add_reminder(
    ctx,
    reminder_message: Option(str, "Your reminder message"), # type: ignore
    date: Option(str, "Date in format dd.mm.yyyy", required = False), # type: ignore
    time: Option(str, "Time in format hh:mm", required = False) # type: ignore
):
    try:
        if date is None and time is None:
            await ctx.respond("Either time or date must be set.", ephemeral=True)
            return
        if date is None:
            date = datetime.now(LOCAL_TZ).strftime("%d.%m.%Y")
        if time is None:
            time = datetime.now(LOCAL_TZ).strftime("%H:%M")

        combined_timestamp = f"{date} {time}"
        local_dt = datetime.strptime(combined_timestamp, "%d.%m.%Y %H:%M").replace(tzinfo=LOCAL_TZ)

        # Check if the datetime is in the future
        if local_dt <= datetime.now(LOCAL_TZ):
            await ctx.respond("The specified date and time must be in the future.", ephemeral=True)
            return

        lock = asyncio.Lock()
        async with lock:
            connection = sqlite3.connect(DB_PATH)
            cursor = connection.cursor()
            cursor.execute("""
                INSERT INTO reminders (user_id, channel_id, remind_at, message)
                VALUES (?, ?, ?, ?)
                """, (ctx.author.id, ctx.channel.id, local_dt.astimezone(ZoneInfo("UTC")).isoformat(), reminder_message))
            connection.commit()
            connection.close()

        await ctx.respond(f"Reminder saved for {ctx.author.name}", ephemeral=True)

    except ValueError:
        await ctx.respond('Bad formatting. Parameters: dd.mm.yyyy, MM:HH, <reminder_message>')


@bot.slash_command(description='Roll dices, duh!')
async def roll(ctx, diceroll: str):
    given_command = diceroll
    try:
        if '+' in diceroll:
            count, _, diceroll = diceroll.partition('d')
            size, _, modifier = diceroll.partition('+')

            if not count.isnumeric() and not size.isnumeric() and not modifier.isnumeric():
                await ctx.respond('Rolling '+given_command+':\n'+'Bad formatting. Format: NdN[+N]')
                return
        else:
            count, _, size = diceroll.partition('d')
    
        count = int(count)
        size = int(size)

        if count > 100:
            await ctx.respond('Rolling '+given_command+':\n'+"I don't have that many dices. Max number is 100.")
            return
        if size > 1000:
            await ctx.respond('Rolling '+given_command+':\n'+"There is no such thing as a d"+str(size)+". Max size is 1000.")
            return

        nums = []
        for i in range(count):
            num = random.randint(1,size)
            nums.append(num)
        
        sum_nums = sum(nums)
        nums_str =  [str(x) for x in nums]

        if '+' in given_command:
            mod_sum = str(sum_nums+int(modifier))
            await ctx.respond('Rolling '+given_command+':\n'+' '.join(nums_str) + ' = '+str(sum_nums)+' + mod('+modifier+') = ' + mod_sum)
        else:
            await ctx.respond('Rolling '+given_command+':\n'+' '.join(nums_str) + ' = '+str(sum_nums))
    except ValueError:
        await ctx.respond('Rolling '+diceroll+':\n'+'Bad formatting. Format: NdN[+N]')


@bot.slash_command(description='Roll dices for shadowrun, including exploding 6.')
async def sr_roll(ctx, count: int, ex: bool):
    if not str(count).isnumeric():
        await ctx.respond('Bad formatting. Format: N [ex]')
        return
    if count > 150:
        await ctx.respond("I don't have that many dice. Max number is 150.")
        return

    countstr = str(count)
    succ = 0
    ones = 0
    nums = []

    i = 0
    while i < count:
        rollvalue = random.randint(1,6)
        nums.append(rollvalue)
        if rollvalue == 5:
            succ+=1
        if rollvalue == 6:
            succ+=1
            if ex is True:
                count+=1
        if rollvalue == 1:
            ones+=1
        
        i+=1
    
    nums_str = [str(x) for x in nums]
    exstr = ""
    if ex: 
       exstr = ' exploding (' + str(count) + ' dices total)'
    await ctx.respond('Rolling ' + countstr + 'd6 '+ exstr + '\n' + ' '.join(nums_str) + '\nSuccesses (5 and 6): '+str(succ)+', Misses (1): '+str(ones))


@bot.slash_command(guild_ids=[keksrunde], description='Print role message to react to.')
@commands.has_any_role("Obaka")
async def printrolemessage(ctx):
    role_list = "Available roles for self-enroll:\n\n"
    if ctx.guild_id == keksrunde:
        # Ignore test role "Green"
        role_list += "\n".join(f"{emoji} — {role}" for emoji, role in roleWhitelist.items() if role != "Green")
    else:
        role_list += "\n".join(f"{emoji} — {role}" for emoji, role in roleWhitelist.items())

    # Send the message
    await ctx.respond("Yeet", ephemeral=True)
    message_obj = await ctx.send(role_list)

    for emoji, role in roleWhitelist.items():
        if ctx.guild_id != keksrunde or role != "Green":
            await message_obj.add_reaction(emoji)

    role_message_id = message_obj.id
    with open(role_message_file, 'w') as file:
        role_message.append({
            "role_message_id": role_message_id,
        })
        json.dump(role_message, file)


@bot.slash_command(description='Trefferzone würfeln.')
async def roll_trefferzone(ctx):
    await ctx.respond(f'{ctx.author.name} wurde am {random.choice(trefferzonen)} getroffen.')


@bot.slash_command(description='Did I hear a Rock and Stone?')
async def rock_and_stone(ctx):
    await ctx.respond(f'{random.choice(salutes)}')


@bot.slash_command(guild_ids=[bot_hoehle], description='Crash test :)')
@commands.has_any_role("Wise Wolf", "Obaka")
async def crash_test(ctx):
    await ctx.respond('Oh no, I crashed!')
    await log('Bot was crashed on purpose.')
    sys.exit(1)


@bot.slash_command(guild_ids=[bot_hoehle], description='Shutdown Bot.')
@commands.has_any_role("Wise Wolf", "Obaka")
async def shutdown(ctx):
    await ctx.respond('Shutting down...')
    await log('Bot was shut down.')
    await bot.close()
    sys.exit(0)


try:
    bot.run(os.environ.get('BOTBAKA'))
except KeyboardInterrupt:
    sys.exit(0)
