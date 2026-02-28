# bot.py
# Author: Michael DeVito
# Purpose: Main file for BCP bot

# Import necessary libraries
import discord
import logging
import os
import database as db
from discord.ext import commands, tasks
from discord import option
from datetime import datetime
from dotenv import load_dotenv

# Initialize db
print(f"Starting bcp-bot at {datetime.now().strftime("%H:%M")}")
db.init_db()

# Load .env file variables
load_dotenv()
token = os.getenv('DISCORD_TOKEN')
if not token:
    raise ValueError("DISCORD_TOKEN not set in .env file.")

# Basic Logging
logging.basicConfig(filename='discord.log', level=logging.INFO, filemode='w')

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
bot = discord.Bot(command_prefix=get_prefix, intents=intents)

''' All Events '''
# Handling Bot Start
@bot.event
async def on_ready():
    # await bot.sync_commands() # only used for dev
    for guild in bot.guilds:
        db.ensureGuildExists(guild.id)
    daily_message_timer.start()
    print("Bot is ready to go!")

# Handles guild join
@bot.event
async def on_guild_join(guild):
    try:
        db.addServer(int(guild.id))
    except:
        print(f'Something went wrong adding server: {guild.id}')

@bot.event
async def on_guild_remove(guild):
    try:
        db.removeServer(int(guild.id))
    except:
        print(f'Something went wrong removing server: {guild.id}')

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
                feast = db.getTodaysFeast()
                color = db.getTodaysColor().lower()   
                match color:
                    case "pink":
                        color = discord.Color.nitro_pink()
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

                collect = db.getTodaysCollect()
                if "*and*" in collect:
                    collect = collect.split('*and*')

                    for text in collect:
                        embed.add_field(name = '', value=text, inline = False)
                else:
                    embed.add_field(name = '', value=collect, inline = False)

                if (db.getTodaysImage()):
                    image = db.getTodaysImage()
                    caption = db.getTodaysCaption()
                    embed.set_image(url=image)
                    embed.set_footer(text=f"{caption}")
                
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
# /help
@bot.slash_command(name="help", description="Shows Information and Commands")
async def help(ctx):
    embed = discord.Embed(    
        title = "List of Commands",
        color = discord.Color.blue()
    )
    embed.add_field(name = "/config prefix <prefix>", value = "Configure the default prefix for the server (if slash commands are disabled).", inline = False)
    embed.add_field(name = "/config dailycollect <option>", value = "Configure daily collect information such as channel, time sent, view the current settings, enable, or disable.", inline = False)
    embed.add_field(name = "/dailycollect", value = "Today's daily collect.", inline = False)
    embed.add_field(name = "/creed <creed>", value = "Print a specific creed.", inline = False)

    await ctx.response.send_message(embed=embed)

# /configure command group
config = discord.SlashCommandGroup(name="configure", description="Edit bot configuration")
dailycollectconfig = config.create_subgroup(name="daily-collect", description="Configure daily collect")

@config.command(name="prefix", description="Change the server prefix")
@commands.has_permissions(administrator=True)
async def prefix(ctx, prefix):

    db.setPrefix(ctx.guild.id, prefix)
    embed = discord.Embed(
        title = "Changed Prefix",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Prefix has been changed to {prefix}")

    await ctx.respond(embed=embed)

@dailycollectconfig.command(name="channel", description="Change daily collect channel")
@commands.has_permissions(administrator=True)
async def channel(ctx):

    db.setChannel(ctx.guild.id,ctx.channel.id)
    embed = discord.Embed(
        title = "Changed Channel",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Channel for daily messages has been changed to #{ctx.channel.name}.")

    await ctx.respond(embed=embed)

@dailycollectconfig.command(name="time", description="Change daily collect time")
@commands.has_permissions(administrator=True)
async def time(ctx, time):
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

            await ctx.respond(embed=embed)
        else:
            await ctx.respond("`!settime` Error: Please format time in 24-hour EST\n*Example: 7:00 for 7AM*")
    except:
        await ctx.respond("`!settime` Error: Please format time in 24-hour EST\n*Example: 7:00 for 7AM*")

@dailycollectconfig.command(name="status", description="See daily collect status")
@commands.has_permissions(administrator=True)
async def status(ctx):
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

    await ctx.respond(embed=embed)

@dailycollectconfig.command(name="enable", description="Enables Daily collects")
@commands.has_permissions(administrator=True)
async def enable(ctx):
    db.setStatus(ctx.guild.id,True)
    embed = discord.Embed(
        title = "Enabled Daily Collects",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Daily collects have now been enabled.")

    await ctx.respond(embed=embed)

@dailycollectconfig.command(name="disable", description="Disables Daily collects")
@commands.has_permissions(administrator=True)
async def disable(ctx):
    db.setStatus(ctx.guild.id,False)
    embed = discord.Embed(
        title = "Disabled Daily Collects",
        color = discord.Color.blue()
    )
    embed.add_field(name = "", value = f"Daily collects have now been disabled.")

    await ctx.respond(embed=embed)

# /dailycollect <enable/disable/status>
@bot.slash_command()
@commands.has_permissions(administrator=True)
async def dailycollect(ctx): 
    await send_daily_collect(ctx.channel.id)

# /creed command 
@bot.slash_command(name="creed", description="Get a specific creed")
@option("creed", description="Choose a Creed", choices=["The Nicene Creed", "The Apostle's Creed", "The Athanasian Creed"])
async def creed(ctx, creed:str):

    response = db.getCreed(creed)
    if response:
        version = response[0]
        text = response[1]
                
        embed = discord.Embed(    
            title = creed,
            color = discord.Color.blue()
        )
        if "*/n*" in text:
            text = text.split('*/n*')

            for t in text:
                embed.add_field(name = '', value=t, inline = False)
        else:
            embed.add_field(name = '', value=text, inline = False)

        embed.set_footer(text=version)
        await ctx.respond(embed=embed)
    else:
        await ctx.respond("Creed was not found.")
    

''' Run the bot '''
bot.run(token)