import sqlite3 #python built in library for working with databases
import json #just reads our json file

# connect to database (creates the file if it doesn't exist)
conn = sqlite3.connect("studies.db")
cursor = conn.cursor() #conn is the connextion to the database and cursur is the toll used to actually run commands on it

# create the studies table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS studies (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        date TEXT,
        description TEXT,
        eligibility TEXT,
        compensation TEXT,
        contact TEXT
    )
""")

# load studies from JSON file
with open("studies.json", "r") as f:
    studies = json.load(f)

# insert each study(as a row) into the database
for study in studies:
    cursor.execute("""
        INSERT INTO studies (title, date, description, eligibility, compensation, contact)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        study["title"],
        study["date"],
        study["description"],
        json.dumps(study["eligibility"]),
        study["compensation"],
        study["contact"]
    ))

conn.commit()
conn.close()

print(f"Loaded {len(studies)} studies into database")