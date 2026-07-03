from flask import Flask, jsonify, request
import sqlite3 
import json


app = Flask(__name__) #creates the web app

# helper function to connect to the database
def get_db():
    conn = sqlite3.connect("studies.db")
    conn.row_factory = sqlite3.Row  # allows access to columns by name instead of index
    return conn


# returns all studies in the database as a JSON 
@app.route("/studies", methods=["GET"])
def get_studies():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM studies")
    rows = cursor.fetchall()
    conn.close()

    # convert each row into a dictionary
    studies = []
    for row in rows:
        studies.append({
            "id": row["id"],
            "title": row["title"],
            "date": row["date"],
            "description": row["description"],
            "eligibility": json.loads(row["eligibility"]) if row["eligibility"] else [],
            "compensation": row["compensation"],
            "contact": row["contact"]
        })

    return jsonify(studies)

# run the app and server restarts automatically when code is changed
if __name__ == "__main__":
    app.run(debug=True)