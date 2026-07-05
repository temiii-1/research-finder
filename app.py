from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date
import sqlite3 
import json


app = Flask(__name__) #creates the web app
CORS(app) #allows the app to be accessed from other domains

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
            "contact": row["contact"],
            "category": row["category"]
        })

    return jsonify(studies)

# new route that acceots form submissions
@app.route("/submit", methods=["POST"])
def submit_study():
    data = request.get_json()
    today = date.today().strftime("%m/%d/%Y")

    title = data.get("title")
    description = data.get("description")
    eligibility = data.get("eligibility")
    compensation = data.get("compensation")
    contact = data.get("contact")
    category = data.get("category", "Uncategorized") 

    # make sure required fields are filled
    if not title or not description or not contact:
        return jsonify({"error": "Title, description, and contact are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO studies (title, date, description, eligibility, compensation, contact, category)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        title,
        today,
        description,
        json.dumps([eligibility]),
        compensation,
        contact,
        category
    ))
    conn.commit()
    conn.close()

    return jsonify({"message": "Study submitted successfully"}), 201

# run the app and server restarts automatically when code is changed
if __name__ == "__main__":
    app.run(debug=True)