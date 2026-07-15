from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import date, datetime, timedelta
from groq import Groq
from dotenv import load_dotenv
import sqlite3 
import json
import os
import bcrypt
import jwt
import urllib.request

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = Groq(api_key=GROQ_API_KEY)


app = Flask(__name__) #creates the web app
CORS(app) #allows the app to be accessed from other domains

# helper function to connect to the database
def get_db():
    conn = sqlite3.connect("studies.db")
    conn.row_factory = sqlite3.Row  # allows access to columns by name instead of index
    return conn

@app.route("/test", methods=["GET"])
def test():
    return jsonify({"message": "test works"}), 200

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


@app.route("/profile", methods=["GET", "POST", "OPTIONS"])
def user_profile():

    if request.method == "OPTIONS":
        return jsonify({}), 200

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401

    token_str = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
    except:
        return jsonify({"error": "Invalid token"}), 401

    if request.method == "POST":
        data = request.get_json()
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM profiles WHERE user_id = ?", (user_id,))
        existing = cursor.fetchone()

        if existing:
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

    else:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        prof = cursor.fetchone()
        conn.close()

        if not prof:
            return jsonify({"error": "No profile found"}), 404

        return jsonify({
            "age": prof["age"],
            "major": prof["major"],
            "interests": prof["interests"],
            "availability": prof["availability"]
        }), 200



@app.route("/categories", methods=["GET"])
def get_categories():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT category FROM studies ORDER BY category")
    rows = cursor.fetchall()
    conn.close()
    categories = [row["category"] for row in rows]
    return jsonify(categories)


@app.route("/bookmarks", methods=["GET"])
def get_bookmarks():
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
    cursor.execute("""
        SELECT studies.* FROM studies
        JOIN bookmarks ON studies.id = bookmarks.study_id
        WHERE bookmarks.user_id = ?
    """, (user_id,))
    rows = cursor.fetchall()
    conn.close()

    studies = []
    for row in rows:
        studies.append({
            "id": row["id"],
            "title": row["title"],
            "category": row["category"],
            "date": row["date"],
            "description": row["description"],
            "compensation": row["compensation"],
            "contact": row["contact"],
            "eligibility": json.loads(row["eligibility"]) if row["eligibility"] else []
        })

    return jsonify(studies), 200


@app.route("/bookmarks/<int:study_id>", methods=["POST", "DELETE"])
def toggle_bookmark(study_id):
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

    if request.method == "POST":
        try:
            cursor.execute("""
                INSERT INTO bookmarks (user_id, study_id) VALUES (?, ?)
            """, (user_id, study_id))
            conn.commit()
            conn.close()
            return jsonify({"message": "Bookmarked"}), 201
        except:
            conn.close()
            return jsonify({"error": "Already bookmarked"}), 400

    elif request.method == "DELETE":
        cursor.execute("""
            DELETE FROM bookmarks WHERE user_id = ? AND study_id = ?
        """, (user_id, study_id))
        conn.commit()
        conn.close()
        return jsonify({"message": "Bookmark removed"}), 200

@app.route("/recommendations", methods=["GET"])
def get_recommendations():
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"error": "Not authenticated"}), 401

    token_str = auth_header.split(" ")[1]

    try:
        payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
        user_id = payload["user_id"]
    except:
        return jsonify({"error": "Invalid token"}), 401

    # Get user profile
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
    prof = cursor.fetchone()

    if not prof:
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

    # Build prompt
    profile_text = f"""
    Age: {prof["age"]}
    Major: {prof["major"]}
    Interests: {prof["interests"]}
    Availability: {prof["availability"]}
    """

    studies_text = ""
    for s in studies:
        studies_text += f"ID: {s['id']} | Title: {s['title']} | Category: {s['category']} | Eligibility: {', '.join(s['eligibility'][:2])}\n"

    prompt = f"""You are a research study matcher for UT Austin students.

Student profile:
{profile_text}

Available studies:
{studies_text}

Pick the top 5 studies that best match this student based on their interests, age, and background.
Respond ONLY with a JSON array like this, no other text:
[
  {{"id": 1, "reason": "Matches your interest in anxiety research and you meet the age requirement"}},
  {{"id": 2, "reason": "..."}}
]"""

    # Call Groq API
    chat_completion = groq_client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile"
    )

    ai_text = chat_completion.choices[0].message.content.strip()
    
    # Parse JSON response
    matches = json.loads(ai_text)

    # Build full study details
    study_map = {s["id"]: s for s in studies}
    recommendations = []
    for match in matches:
        study = study_map.get(match["id"])
        if study:
            recommendations.append({
                **study,
                "reason": match["reason"]
            })

    return jsonify({"recommendations": recommendations}), 200    
# run the app and server restarts automatically when code is changed
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))