import sqlite3 #python built in library for working with databases
import json #just reads our json file

# connect to database (creates the file if it doesn't exist)
conn = sqlite3.connect("studies.db")
cursor = conn.cursor() #conn is the connextion to the database and cursur is the toll used to actually run commands on it


# load studies from JSON file
with open("studies.json", "r") as f:
    studies = json.load(f)

cursor.execute("DELETE FROM studies")  # clear existing studies, re-insert with categories

# insert each study(as a row) into the database
for study in studies:
    cursor.execute("""
        INSERT INTO studies (title, date, description, eligibility, compensation, contact, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        study["title"],
        study["date"],
        study["description"],
        json.dumps(study["eligibility"]),
        study["compensation"],
        study["contact"],
        study["category"]
    ))

conn.commit()
conn.close()

print(f"Loaded {len(studies)} studies into database")