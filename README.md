# Horns Research Hub

A full-stack web application that helps UT Austin students discover research studies they can participate in. Instead of checking multiple fragmented sources, students can find, filter, bookmark, and get AI-powered recommendations for studies all in one place.

## Live Demo
- **Frontend:** https://temiii-1.github.io/Study-Participant-Hub/
- **Backend API:** https://study-participant-hub.onrender.com

## Features
- **Study Discovery** — Browse 35+ real UT Austin research studies from multiple sources
- **Search & Filters** — Filter by compensation, age, category, and sort by date
- **AI Recommendations** — Personalized study suggestions powered by Groq's LLaMA 3.3 model based on user profile
- **Bookmarking** — Save studies to your profile for later
- **Researcher Submissions** — Researchers can submit studies directly to the platform
- **User Accounts** — Secure authentication with JWT tokens and bcrypt password hashing
- **Contact Researcher** — Pre-filled email template to contact study researchers directly

## Data Sources
- **UT Healthy Horns** — Scraped using Python and BeautifulSoup
- **ClinicalTrials.gov** — Integrated via their public REST API
- **Researcher Submissions** — Direct submissions through the platform

## Tech Stack
- **Frontend:** HTML, CSS, JavaScript — hosted on GitHub Pages
- **Backend:** Python, Flask, SQLite — hosted on Render
- **Libraries:** BeautifulSoup, Flask-CORS, bcrypt, PyJWT, Groq SDK
- **APIs:** ClinicalTrials.gov REST API, Groq LLaMA 3.3

## Project Structure
study-participant-hub/
├── app.py                     # Flask backend API
├── scraper.py                 # Healthy Horns web scraper
├── clinicaltrials_scraper.py  # ClinicalTrials.gov API integration
├── database.py                # Database setup and data loading
├── index.html                 # Home page
├── profile.html               # User profile and recommendations
├── profile_setup.html         # Profile setup form
├── login.html                 # Login page
├── signup.html                # Sign up page
├── submit.html                # Researcher submission form
├── requirements.txt           # Python dependencies
└── README.md                  # Project documentation

## Setup & Installation

**Clone the repository:**
```bash
git clone https://github.com/temiii-1/study-participant-hub.git
cd study-participant-hub
```

**Create a virtual environment:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

**Create a `.env` file:**
GROQ_API_KEY=your_groq_api_key
SECRET_KEY=your_secret_key

**Run the scrapers to populate the database:**
```bash
python scraper.py
python clinicaltrials_scraper.py
python database.py
```

**Start the Flask server:**
```bash
python app.py
```

**Open `index.html` in your browser.**

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /studies | Returns all studies |
| GET | /categories | Returns unique categories |
| POST | /submit | Submit a new study |
| POST | /signup | Create an account |
| POST | /login | Log in |
| GET/POST | /profile | Get or save user profile |
| GET | /bookmarks | Get bookmarked studies |
| POST/DELETE | /bookmarks/\<id\> | Add or remove bookmark |
| GET | /recommendations | AI-powered study recommendations |

## Known Limitations
- Age filter uses text matching rather than numeric parsing
- Compensation field may be empty for some studies due to inconsistent HTML structure on source pages
- Render free tier spins down after inactivity — first load may take ~30 seconds