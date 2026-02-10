# bot.py
# Author: Michael DeVito
# Purpose: Main file for BCP bot

# Import necessary libraries
import discord
import logging
import os
import database as db
from discord.ext import commands, tasks
from datetime import time, datetime
from dotenv import load_dotenv

# Initialize db
print(f"Starting bcp-bot at {datetime.now().strftime("%H:%M")}")

# Insert arguments for initializing DB into function
db.init_db()
db.seed_db() # one-time

# Load .env file variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("DISCORD_TOKEN not set in .env file.")

# Basic Logging
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

# Set up permissions
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
# if something is broken, may need to add an intent

# Function to get command prefix
async def get_prefix(bot, message):

    if not message.guild:
        return commands.when_mentioned_or('!')(bot, message) # Default prefix for DMs

    p = await db.getPrefix(message.guild.id)
    if not p:
        p = '!'
    
    return commands.when_mentioned_or(p)(bot, message)

# Set up bot with command prefix
bot = commands.Bot(command_prefix=get_prefix, intents=intents)
bot.remove_command('help')

''' All Events '''
# Handling Events
@bot.event
async def on_ready():
    for guild in bot.guilds:
        db.ensureGuildExists(guild.id)
    daily_message_timer.start()
    print("Bot is ready to go!")

@bot.event
async def on_guild_join(guild):
    try:
        db.addServer(int(guild.id))
    except:
        print(f'Something went wrong adding server: {guild.id}')


# Main Loop for daily collect time time=time(hour=7, minute=0)
async def send_daily_collect(channel_id):
    # Ensure channel exists
    if channel_id:
        channel = bot.get_channel(channel_id)

        # Double-check bot can send messages in this channel
        if isinstance(channel, discord.TextChannel): 

            try:
                # Building embed     
                date = datetime.today().strftime('%m/%d')
                collect = db.getTodaysCollect() # error is getting thrown here
                feast = db.getTodaysFeast()
                color = db.getTodaysColor().lower()     
                match color:
                    case "pink":
                        color = discord.Color.pink()
                    case "red":
                        color = discord.Color.red()
                    case "white":
                        color = discord.Color.from_rgb(255,255,255)
                    case "purple":
                        color = discord.Color.purple()
                    case _:
                        color = discord.Color.green()
                embed = discord.Embed(
                    title = f'{date} - {feast}',
                    color = color
                )
                embed.add_field(name = '', value = f'{collect}', inline = False)
                
                # Send message
                await channel.send(embed=embed)
            except:
                user = await bot.fetch_user(614461308850405389) # ping @mr_minechael
                await channel.send(f"Error: Today's collect could not be found. Blame <@{user.id}>!")

@tasks.loop(minutes=1)
async def daily_message_timer():
    now = datetime.now().strftime("%H:%M") # HH:MM format

    times = await db.getTimes()
    for server_id, time in times:
        if time and now == time:
            status = await db.getStatus(server_id)
            if status:
                channel_id = await db.getChannel(server_id)
                print(f"Sending daily collect in server {server_id} at {now} EST.")
                await send_daily_collect(channel_id)


''' Commands '''
# !help
@bot.command()
async def help(ctx):
    embed = discord.Embed(    
        title = "List of Commands",
        color = discord.Color.blue()
    )
    embed.add_field(name = "enableCollects", value = "Enables the daily collects feature.", inline = False)
    embed.add_field(name = "setchannel", value = "Sets the channel to post in.", inline = False)
    embed.add_field(name = "settime", value = "Sets the time for daily messages.", inline = False)
    embed.add_field(name = "prefix <prefix>", value = "Sets the bot's prefix for commands.", inline = False)

    await ctx.send(embed=embed)

# !prefix <prefix>
@bot.command()
@commands.has_permissions(administrator=True) # only admin can use this
async def prefix(ctx, prefix):

    db.setPrefix(ctx.guild.id, prefix)
    embed = discord.Embed(
        title = "Changed Prefix",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Prefix has been changed to {prefix}")

    await ctx.send(embed=embed)

# !setchannel
@bot.command()
@commands.has_permissions(administrator=True)
async def setchannel(ctx):

    db.setChannel(ctx.guild.id,ctx.channel.id)
    embed = discord.Embed(
        title = "Changed Channel",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Channel for daily messages has been changed to #{ctx.channel.name}.")

    await ctx.send(embed=embed)

# !settime <time>
@bot.command()
@commands.has_permissions(administrator=True)
async def settime(ctx, time):
    try:
        time = time.split(":")
        hr = time[0]
        min = time[1]
        if (int) (hr) < 25 and (int) (hr) > -1 and (int) (min) > -1 and (int) (min) < 60:

            if (int) (hr) < 10 and hr[0] != "0":
                hr = "0" + time[0]
            if (int) (min) < 10 and min[0] != "0":
                min = "0" + time[1]

            db.setTime(ctx.guild.id, hr, min)

            embed = discord.Embed(
                title = "Changed Time",
                color = discord.Color.blue()
            )
            embed.add_field(name = "", value = f"Time for daily messages has been changed to {hr}:{min} EST.")

            await ctx.send(embed=embed)
        else:
            await ctx.send("`!settime` Error: Please format time in 24-hour EST\n*Example: 7:00 for 7AM*")
    except:
        await ctx.send("`!settime` Error: Please format time in 24-hour EST\n*Example: 7:00 for 7AM*")
    
    


# !dailycollect <enable/disable/status>
@bot.command()
@commands.has_permissions(administrator=True)
async def dailycollect(ctx, msg: str | None = None): # makes msg optional
    if msg:
        if msg.lower() == 'enable':
            db.setStatus(ctx.guild.id,True)
            embed = discord.Embed(
                title = "Enabled Daily Collects",
                color = discord.Color.blue()
            )
            embed.add_field(name = "", value = f"Daily collects have now been enabled.")

            await ctx.send(embed=embed)
        elif msg.lower() == 'disable':
            db.setStatus(ctx.guild.id,False)
            embed = discord.Embed(
                title = "Disabled Daily Collects",
                color = discord.Color.blue()
            )
            embed.add_field(name = "", value = f"Daily collects have now been disabled.")

            await ctx.send(embed=embed)
        elif msg.lower() == 'status':
            enabled = await db.getStatus(ctx.guild.id)
            status = "Disabled"
            channel_name = "None"
            time = "None"
            if enabled:
                status = "Enabled"
                channel_id = await db.getChannel(ctx.guild.id)
                if channel_id:
                    channel = bot.get_channel(channel_id)
                    if channel and isinstance(channel, discord.TextChannel):
                        channel_name = channel.name
                    set_time = await db.getTime(ctx.guild.id)
                    if set_time:
                        time = f'{set_time} EST'
            

            embed = discord.Embed(
                title = "Daily Collects Configuration",
                color = discord.Color.blue()
            )
            embed.add_field(name = "Status", value = f"{status}", inline=False)
            embed.add_field(name = "Channel", value = f"#{channel_name}", inline=False)
            embed.add_field(name = "Time", value = f"{time}", inline=False)

            await ctx.send(embed=embed)

        else:
            embed = discord.Embed(
                title = "Error",
                color = discord.Color.red()
            )
            embed.add_field(name = "", value = f"Incorrect Syntax.", inline=False)
            embed.add_field(name = "", value = f"Proper Syntax: !dailycollect <enable/disable>.", inline=False)

            await ctx.send(embed=embed)
    elif msg == None:
        await send_daily_collect(ctx.channel.id)


    
# Run the bot
bot.run(token, log_handler=handler, log_level=logging.DEBUG)