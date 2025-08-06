import asyncio
import random
import sys
import discord
import os
from discord.ext import tasks, commands
import json
import datetime
from datetime import time
import calendar
from dotenv import load_dotenv

bdayfile = '/home/ubuntu/discordbot/bdays.json'
logfile = '/home/ubuntu/discordbot/Bot.log'

birthdays = []
if os.path.isfile(bdayfile):
    with open(bdayfile, 'r') as file:
        birthdays = json.load(file)

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



bot = commands.Bot(command_prefix='/',Intents=discord.Intents.all())

roleWhitelist = ["Green","Keksritter", "bonk", "Gamer Gremlins", "Phasmocrew", "four clowns walk into a bank ...", "Gunfire Reborn", "Space Rock Junkies", "Robokiller", "Free-for-all", "Zivilisation 6", "7Tagesadventisten", "geo Rätseler"]

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
    timestamp = datetime.datetime.now()
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
async def on_ready():
    await log('Bot started!')
    checkBirthday.start()
    checkAlive.start()

# USES TIMEZONE UTC! -1 hour compared to GMT+1/Berlin
@tasks.loop(hours=1)
async def checkAlive():
    if datetime.datetime.now().hour != 0:
        return

    channel = bot.get_channel(bot_log)
    await channel.send("I am alive.")

@tasks.loop(time=time(hour=23, minute=3, second=0), reconnect=True)
async def checkBirthday():
    today = datetime.datetime.now().strftime("%d.%m")
    day, _, month = today.partition('.')
    month = int(month)
    channel = bot.get_channel(keksrunde_hauptchat)
    for item in birthdays:
        if item['day'] == day and item['month'] == calendar.month_name[month]:
            await channel.send("Happy Birthday <@"+item['id']+">!")

@bot.slash_command(guild_ids=[bot_hoehle])
async def hello(ctx):
    name = ctx.author.name
    await ctx.respond(f"Hello {name}, you miserable creature.")

@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Add your birthday as a reminder for your senile friends. Format: dd.mm')
async def add_birthday(ctx, birthday: str):

    for item in birthdays:
        if str(ctx.author.id) in item:
            await ctx.respond("You already added yourself, dummy.")
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
                    id = str(ctx.author.id)
                    data = {
                        "id": id,
                        "day": str(day),
                        "month": calendar.month_name[month]
                    }
                    birthdays.append(data)

                    json.dump(birthdays, file)
                    await ctx.respond("Birthday saved for "+ctx.author.name)
        else:
            await ctx.respond("Nice job, you broke it. Try again. Format: dd.mm")
            return
    except ValueError:
        await ctx.respond('Bad formatting. Format: dd.mm')

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

@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Prints available roles for self-enroll.')
async def availableroles(ctx):
    await ctx.respond('Available roles for self-enroll:\n\n'+'\n'.join(r for r in roleWhitelist))

@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Gives you a role.')
async def iam(ctx, role: str):
    if "admin" in role.lower():
        await ctx.respond("Hahahahaha... No.")
        return

    user = ctx.author
    userRoles = user.roles
    roleObj = discord.utils.get(ctx.guild.roles,name=role)
    if roleObj is None:
        await ctx.respond('I am case sensitive. Available roles:\n\n'+'\n'.join(r for r in roleWhitelist))
        return
    elif roleObj in userRoles:
        await ctx.respond('You already have this role. Dummy.')
        return
    
    if role in roleWhitelist:
        await user.add_roles(roleObj)
        await ctx.respond(user.name + " was given the role '"+role+"'.")
        await log(user.name + " was given the role '"+role+"'.")
    else:
        await ctx.respond('Not an available role for self-enrolling. Available roles:\n\n'+'\n'.join(r for r in roleWhitelist))

@bot.slash_command(guild_ids=[bot_hoehle, keksrunde], description='Removes selected role.')
async def iamnot(ctx, role: str):
    user = ctx.author
    userRoles = user.roles
    roleObj = discord.utils.get(userRoles,name=role)
    if roleObj is None:
        await ctx.respond('I am case sensitive. User has following roles:\n\n'+'\n'.join(r.name for r in ctx.author.roles[1:]))
        return
    
    if roleObj in userRoles:
        await user.remove_roles(roleObj)
        await ctx.respond("Role '" + role + "' was removed from "+ctx.author.name+".")
        await log("Role '" + role + "' was removed from "+ctx.author.name+".")
    else:
        await ctx.respond(f'You do not have this role. Your roles:\n'+'\n'.join(r.name for r in ctx.author.roles[1:]))

@bot.slash_command(description='Trefferzone würfeln.')
async def roll_trefferzone(ctx):
    await ctx.respond(f'{ctx.author.name} wurde am {random.choice(trefferzonen)} getroffen.')

@bot.slash_command(description='Did I hear a Rock and Stone?')
async def rock_and_stone(ctx):
    await ctx.respond(f'{random.choice(salutes)}')

@bot.slash_command(description='Crash test. Admin only.')
@commands.has_any_role("Endless Admin")
async def crash_test(ctx):
    await ctx.respond('Oh no, I crashed!')
    await log('Bot was crashed on purpose.')
    sys.exit(1)

@bot.slash_command(description='Shutdown Bot. Admin only, nice try :)')
@commands.has_any_role("Endless Admin")
async def shutdown(ctx):
    await ctx.respond('Shutting down...')
    await log('Bot was shut down.')
    await bot.close()
    sys.exit(0)

try:
    bot.run(os.environ.get('BOTBAKA'))
except KeyboardInterrupt:
    sys.exit(0)
