# database.py
# Author: Michael DeVito

import csv
import sqlite3
from pathlib import Path
from datetime import date

DB_PATH = Path("database/main.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
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
    c.executemany('INSERT INTO collects (date, collect, feast, color) VALUES (?, ?, ?, ?)', rows)
    conn.commit()
    conn.close()
    print(f"Inserted {len(rows)} rows into database")

def ensureGuildExists(server_id: int):
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

def addServer(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO servers (server_id, prefix, enabled) VALUES (?, ?, ?)", (server_id, "!", 0)) # insert default values
    conn.commit()
    conn.close()
    print(f"Added new server: {server_id}")

async def getPrefix(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix FROM servers WHERE server_id = ?", (server_id,))
    prefix = c.fetchone()
    conn.close()
    return prefix[0]

def setPrefix(server_id, prefix):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET prefix = ? WHERE server_id = ?", (prefix,server_id))
    conn.commit()
    conn.close()
    print(f"Set prefix to {prefix} for server {server_id}")

async def getTime(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT time FROM servers WHERE server_id = ?", (server_id,))
    time = c.fetchone()
    time = time[0].split(":")
    conn.close()
    return time

def setTime(server_id, hour, minute):
    time = f"{hour}:{minute}"
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET time = ? WHERE server_id = ?", (time,server_id))
    conn.commit()
    conn.close()
    print(f"Set time to {time} EST for server {server_id}")

async def getChannels():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT server_id, channel FROM servers")
    channels = c.fetchall()
    conn.close()
    return channels

async def getChannel(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel FROM servers WHERE server_id = ?", (server_id,))
    channel = c.fetchone()
    conn.close()
    return channel[0]

def setChannel(server_id, channel_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("UPDATE servers SET channel = ? WHERE server_id = ?", (channel_id,server_id))
    conn.commit()
    conn.close()
    print(f"Set channel to {channel_id} for server {server_id}")

async def getStatus(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT enabled FROM servers WHERE server_id = ?", (server_id,))
    status = c.fetchone()
    if status[0] == 1:
        return True
    else:
        return False

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
    

# Functions for daily collect
def getTodaysCollect():
    today = str(date.today())[-5:] # gets today in MM-DD format
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT collect FROM collects WHERE date = ?", (today,))
    collect = c.fetchone()
    conn.close()
    return collect[0]

def getTodaysFeast():
    today = str(date.today())[-5:] # gets today in MM-DD format
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT feast FROM collects WHERE date = ?", (today,))
    feast = c.fetchone()
    conn.close()
    return feast[0]

def getTodaysColor():
    today = str(date.today())[-5:] # gets today in MM-DD format
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT color FROM collects WHERE date = ?", (today,))
    color = c.fetchone()
    conn.close()
    return color[0]