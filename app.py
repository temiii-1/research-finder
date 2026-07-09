from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date, datetime, timedelta
import sqlite3 
import json
import os
import bcrypt
import jwt
import urllib.request


SECRET_KEY = "ut-research-finder-secret-key-2026-make-it-long"  # Replace with a secure key in production


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

# new route for form submissions
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

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    # Hash the password
    password_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    conn = get_db()
    cursor = conn.cursor()

    # Check if email already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return jsonify({"error": "Email already registered"}), 400

    # Insert new user
    cursor.execute("""
        INSERT INTO users (email, password_hash) VALUES (?, ?)
    """, (email, password_hash))
    conn.commit()

    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    new_user = cursor.fetchone()
    

    token = jwt.encode({
        "user_id": new_user["id"],
        "email": email,
        "exp": datetime.now() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")

    conn.close()

    return jsonify({"message": "Account created successfully", "token": token}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": "Email and password are required"}), 400

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()

    if not user:
        return jsonify({"error": "Invalid email or password"}), 401

    # Check password
    if not bcrypt.checkpw(password.encode("utf-8"), user["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid email or password"}), 401

    # Generate JWT token
    token = jwt.encode({
        "user_id": user["id"],
        "email": email,
        "exp": datetime.now() + timedelta(days=7)
    }, SECRET_KEY, algorithm="HS256")

    return jsonify({"token": token, "message": "Login successful"}), 200


@app.route("/profile", methods=["POST"])
def save_profile():
    # Get token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401

    token = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Session expired, please log in again"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    data = request.get_json()

    conn = get_db()
    cursor = conn.cursor()

    # Check if profile already exists
    cursor.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
    existing = cursor.fetchone()

    if existing:
        # Update existing profile
        cursor.execute("""
            UPDATE profiles SET age=?, major=?, interests=?, availability=?, medical_conditions=?
            WHERE user_id=?
        """, (
            data.get("age"),
            data.get("major"),
            data.get("interests"),
            data.get("availability"),
            data.get("medical_conditions"),
            user_id
        ))
    else:
        # Insert new profile
        cursor.execute("""
            INSERT INTO profiles (user_id, age, major, interests, availability, medical_conditions)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            data.get("age"),
            data.get("major"),
            data.get("interests"),
            data.get("availability"),
            data.get("medical_conditions")
        ))

    conn.commit()
    conn.close()

    return jsonify({"message": "Profile saved successfully"}), 200

@app.route("/profile", methods=["GET"])
def get_profile():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401

    token_str = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
    except:
        return jsonify({"error": "Invalid token"}), 401

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()
    conn.close()

    if not profile:
        return jsonify({"error": "No profile found"}), 404

    return jsonify({
        "age": profile["age"],
        "major": profile["major"],
        "interests": profile["interests"],
        "availability": profile["availability"]
    }), 200

@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401

    token_str = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Session expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 401

    # Get user profile
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    profile = cursor.fetchone()

    if not profile:
        conn.close()
        return jsonify({"error": "Please complete your profile first"}), 400

    # Get all studies
    cursor.execute("SELECT * FROM studies")
    rows = cursor.fetchall()
    conn.close()

    studies = []
    for row in rows:
        studies.append({
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "description": row["description"],
            "eligibility": json.loads(row["eligibility"]) if row["eligibility"] else [],
            "compensation": row["compensation"],
            "contact": row["contact"]
        })

    # Build prompt for Claude
    profile_text = f"""
    Age: {profile["age"]}
    Major: {profile["major"]}
    Interests: {profile["interests"]}
    Availability: {profile["availability"]}
    Medical/Personal Background: {profile["medical_conditions"]}
    """

    studies_text = ""
    for s in studies:
        studies_text += f"""
    ID: {s["id"]}
    Title: {s["title"]}
    Category: {s["category"]}
    Description: {s["description"][:300]}
    Eligibility: {", ".join(s["eligibility"][:3])}
    ---
    """

    prompt = f"""You are a research study matcher for UT Austin students.

Here is the student's profile:
{profile_text}

Here are the available studies:
{studies_text}

Pick the top 5 studies that best match this student's profile, age, interests, and background.
For each match, provide a brief personalized reason why it suits them.

Respond ONLY with a JSON array like this:
[
  {{"id": 1, "reason": "This study matches your interest in anxiety research and you meet the age requirement"}},
  {{"id": 2, "reason": "..."}}
]

Return only the JSON array, no other text."""

    # Call Claude API
    api_request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps({
            "model": "claude-sonnet-4-6",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        },
        method="POST"
    )

    with urllib.request.urlopen(api_request) as api_response:
        api_data = json.loads(api_response.read())

    ai_text = api_data["content"][0]["text"]
    matches = json.loads(ai_text)

    # Build response with full study details
    recommendations = []
    study_map = {s["id"]: s for s in studies}

    for match in matches:
        study = study_map.get(match["id"])
        if study:
            recommendations.append({
                **study,
                "reason": match["reason"]
            })

    return jsonify({"recommendations": recommendations}), 200

@app.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM studies ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    categories = [row["category"] for row in rows]
    return jsonify(categories)
# run the app and server restarts automatically when code is changed
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))