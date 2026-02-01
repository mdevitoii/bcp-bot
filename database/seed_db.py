# seed.db
# Author: Michael DeVito

import csv
from pathlib import Path
import sqlite3

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
        print(row)
        date = row.get("Date","").strip()
        collect = row.get("Collect","").strip()
        feast = row.get("Feast","").strip()
        color = row.get("Color","").strip()

        print(f'{date} {collect} {feast} {color}')

        rows.append((date, collect, feast, color))

# Add rows to DB
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.executemany('INSERT INTO collects (date, collect, feast, color) VALUES (?, ?, ?, ?)', rows)
conn.commit()
conn.close()
print(f"Inserted {len(rows)} rows into database")