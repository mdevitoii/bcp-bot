# database.py
# Author: Michael DeVito

from asyncio import open_connection
import os
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
                (server_id INTEGER PRIMARY KEY, prefix TEXT, time TEXT, channel TEXT)''')
    conn.commit()
    conn.close()

def ensureGuildExists(server_id: int):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO servers (server_id) VALUES (?) ON CONFLICT(server_id) DO NOTHING;", (server_id,))
    conn.commit()
    conn.close()
    print(f"Server added: {server_id}")

def addServer(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO servers (server_id) VALUES (?)", (server_id))
    conn.commit()
    conn.close()

def getPrefix(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT prefix FROM servers WHERE server_id = ?", (server_id))
    prefix = c.fetchone()
    conn.close()
    return prefix

def getTime(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT time FROM servers WHERE server_id = ?", (server_id))
    time = c.fetchone()
    conn.close()
    return time

def getChannel(server_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT channel FROM servers WHERE server_id = ?", (server_id))
    channel = c.fetchone()
    conn.close()
    return channel

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