import sqlite3 

# connect to database(creates file if it doesn't exist)
conn = sqlite3.connect("studies.db")
cursor = conn.cursor()

# get all the studies from the database (SELECT is a SQL query/command used to retrieve data from a database)
cursor.execute("SELECT id, title, compensation FROM studies")
rows = cursor.fetchall()

for row in rows:
    print(f"ID: {row[0]} | TITLE: {row[1][:50]} | COMPENSATION: {row[2][:30]}")

conn.close()