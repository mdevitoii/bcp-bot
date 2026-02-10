# database.py
# Author: Michael DeVito

import csv
import os
import sqlite3
from pathlib import Path
from datetime import date, datetime
from dotenv import load_dotenv

load_dotenv()
DB_PATH = Path((str) (os.getenv('DB_PATH')))
if not DB_PATH:
    raise ValueError("DB_PATH not set in .env file.")

# Initialize the DB if it doesn't exist
def init_db():
    conn = sqlite3.connect(DB_PATH)
    print("DB initialized")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS collects
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, collect TEXT, feast TEXT, color TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS servers
                (server_id INTEGER PRIMARY KEY, prefix TEXT, time TEXT, channel INTEGER, enabled INTEGER)''')
    conn.commit()
    c.execute("SELECT * FROM collects WHERE date = '01-01'")
    test = c.fetchone()
    if test:
        conn.close()
    else:
        print("Re-seeding DB")
        seed_db()
        conn.close()

# Seed the DB if it does not contain collects
def seed_db():
    CSV = Path("database/all_collects.csv")
    DB_PATH = Path("database/main.db")

    # if CSV file isn't found, throw an error
    if not CSV.exists():
        print(f"all_collects.csv not found.")

    # Get rows from .csv file
    with CSV.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        rows = []
        for row in reader:
            date = row.get("Date","").strip()
            collect = row.get("Collect","").strip()
            feast = row.get("Feast","").strip()
            color = row.get("Color","").strip()

            rows.append((date, collect, feast, color))

    # Add rows to DB
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("DROP TABLE IF EXISTS collects")
    c.execute('''CREATE TABLE IF NOT EXISTS collects
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, collect TEXT, feast TEXT, color TEXT)''')
    c.executemany('INSERT INTO collects (date, collect, feast, color) VALUES (?, ?, ?, ?)', rows)
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows)} rows into database")

# Ensure that a guild exists within the DB
def ensureGuildExists(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix FROM servers WHERE server_id = ?", (server_id,))
    conn.commit()
    test = c.fetchone()
    conn.close()
    if test:
        print(f"Server initialized: {server_id}")
    else:
        addServer(server_id)

# Bot is added to new server, add server to DB
def addServer(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO servers (server_id, prefix, enabled) VALUES (?, ?, ?)", (server_id, "!", 0)) # insert default values
    conn.commit()
    conn.close()
    print(f"Added new server: {server_id}")

# Get per-server prefix
async def getPrefix(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix FROM servers WHERE server_id = ?", (server_id,))
    prefix = c.fetchone()
    conn.close()
    return prefix[0]

# Set per-server prefix
def setPrefix(server_id, prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET prefix = ? WHERE server_id = ?", (prefix,server_id))
    conn.commit()
    conn.close()
    print(f"Set prefix to {prefix} for server {server_id}")

# Get all servers and respective times for daily collect
async def getTimes():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT server_id, time FROM servers")
    times = c.fetchall()
    conn.close()
    return times

# Get a specific server's time for daily collect
async def getTime(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT time FROM servers WHERE server_id = ?", (server_id,))
    time = c.fetchone()
    conn.close()
    if time[0]:
        return time[0]
    else:
        return None

# Set a specific server's time for daily collect
def setTime(server_id, hour, minute):
    time = f"{hour}:{minute}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET time = ? WHERE server_id = ?", (time,server_id))
    conn.commit()
    conn.close()
    print(f"Set time to {time} EST for server {server_id}")

# Get all servers and respective channels for daily collect
async def getChannels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT server_id, channel FROM servers")
    channels = c.fetchall()
    conn.close()
    return channels

# Get a specific server's channel for daily collect
async def getChannel(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel FROM servers WHERE server_id = ?", (server_id,))
    channel = c.fetchone()
    conn.close()
    if channel[0]:
        return (int) (channel[0])
    else:
        return None

# Set a specific server's channel for daily collect
def setChannel(server_id, channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET channel = ? WHERE server_id = ?", (channel_id,server_id))
    conn.commit()
    conn.close()
    print(f"Set channel to {channel_id} for server {server_id}")

# Get a specific server's status for daily collect
async def getStatus(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT enabled FROM servers WHERE server_id = ?", (server_id,))
    status = c.fetchone()
    if status[0] == 1:
        return True
    else:
        return False

# Set a specific server's status for daily collect
def setStatus(server_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    enabled = 0
    if status:
        enabled = 1
    c.execute("UPDATE servers SET enabled = ? WHERE server_id = ?", (enabled,server_id))
    conn.commit()
    conn.close()
    print(f"Set status to {enabled} for server {server_id}")
    

''' Functions used for compiling daily collect '''
# Get today's collect
def getTodaysCollect():
    print("GETTING TODAY COLLECT")
    today = datetime.today().strftime('%m-%d') # gets today in MM-DD format
    print(today)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT collect FROM collects WHERE date = ?", (today,))
    collect = c.fetchone()
    conn.close()
    print(collect)
    print("DID THE SQL STUFF")
    return collect[0]
    

# Get today's feast day
def getTodaysFeast():
    today = datetime.today().strftime('%m-%d') # gets today in MM-DD format    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT feast FROM collects WHERE date = ?", (today,))
    feast = c.fetchone()
    conn.close()
    return feast[0]

# Get today's season color
def getTodaysColor():
    today = datetime.today().strftime('%m-%d') # gets today in MM-DD format
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT color FROM collects WHERE date = ?", (today,))
    color = c.fetchone()
    conn.close()
    return color[0]