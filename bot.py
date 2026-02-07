# bot.py
# Author: Michael DeVito
# Purpose: Main file for BCP bot

# Import necessary libraries
import discord
import logging
import os
import database as db
from discord.ext import commands 
from discord.ext import tasks
from dotenv import load_dotenv
from datetime import time
from datetime import datetime

# Initialize db
db.init_db()

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
    print("Bot is ready to go!")
    for guild in bot.guilds:
        db.ensureGuildExists(guild.id)
    daily_message.start()
    print("done!")

@bot.event
async def on_guild_join(guild):
    try:
        db.addServer(int(guild.id))
    except:
        print(f'Something went wrong adding server: {guild.id}')


# Main Loop for daily collect time time=time(hour=7, minute=0)
# Note: Time is in GMT (EST + 5 hours)
@tasks.loop(time=time(hour=12, minute=0)) 
async def daily_message():

    # Load server config from DB (implement later)
    CHANNEL_ID = 964543319290036224

    channel = bot.get_channel(CHANNEL_ID) # channel_id = channel message is sent to
    if isinstance(channel, discord.TextChannel):
        
        date = datetime.today().strftime('%m/%d')
        collect = db.getTodaysCollect()
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
        await channel.send(embed=embed)



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

# Run the bot
bot.run(token, log_handler=handler, log_level=logging.DEBUG)