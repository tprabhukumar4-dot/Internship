from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

app = Flask(__name__, template_folder="templates")

# ------------------------
# Google Sheets Connection
# ------------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/spreadsheets",
         "https://www.googleapis.com/auth/drive.file",
         "https://www.googleapis.com/auth/drive"]

creds = ServiceAccountCredentials.from_json_keyfile_name("inten.json", scope)
client = gspread.authorize(creds)

SHEET_URL = "https://docs.google.com/spreadsheets/d/1kiU7qr6syo2OXxon-qIGjXaCdPRKogGhjzW4pQFam0I/edit"
sheet = client.open_by_url(SHEET_URL).sheet1

# YouTube links for skills
youtube_links = {
    "python": "https://www.youtube.com/watch?v=_uQrJ0TkZlc",
    "sql": "https://www.youtube.com/watch?v=HXV3zeQKqGY",
    "machine learning": "https://www.youtube.com/watch?v=GwIo3gDZCVQ",
    "excel": "https://www.youtube.com/watch?v=Vl0H-qTclOg",
    "tableau": "https://www.youtube.com/watch?v=TpLhLbCXoS8",
    "power bi": "https://www.youtube.com/watch?v=oYF8XH7dZVI",
    "communication": "https://www.youtube.com/watch?v=HAnw168huqA",
    "presentation": "https://www.youtube.com/watch?v=QKpLQK0DAcM",
    "finance": "https://www.youtube.com/watch?v=2g9lsbJBPEs",
    "marketing": "https://www.youtube.com/watch?v=nk0Y7hRBqSU",
    "graphic design": "https://www.youtube.com/watch?v=FtRzOZ06lpo",
}

# ------------------------
# Routes
# ------------------------

@app.route("/")
def home():
    """Serve the frontend HTML page"""
    return render_template("index.html")


@app.route("/recommend", methods=["POST"])
def recommend():
    """Handle recommendations based on user input"""
    data = request.json
    user_skills = [s.lower() for s in data.get("skills", [])]
    user_min_stipend = int(data.get("stipend", 0))
    user_min_duration = int(data.get("duration", 0))

    # Load sheet into DataFrame
    df = pd.DataFrame(sheet.get_all_records())

    # Normalize text
    df["skills"] = df["skills"].astype(str).str.lower()
    df["internship_title"] = df["internship_title"].astype(str).str.lower()
    df["company_name"] = df["company_name"].astype(str).str.lower()

    # Convert stipend & duration to numeric
    df["stipend_min"] = pd.to_numeric(df.get("stipend_min", 0), errors="coerce").fillna(0)
    df["stipend_max"] = pd.to_numeric(df.get("stipend_max", 0), errors="coerce").fillna(0)
    df["duration_value"] = pd.to_numeric(df.get("duration_value", 0), errors="coerce").fillna(0)

    # Lists to store results
    match_scores = []
    missing_skills_list = []
    missing_urls_list = []

    # Rule-based scoring
    for _, row in df.iterrows():
        score = 0
        total = 0

        internship_skills = [s.strip() for s in row["skills"].split(",")]
        internship_skills_lower = [s.lower() for s in internship_skills]

        # --- Skill Matching (50%) ---
        matched = [skill for skill in user_skills if skill in internship_skills_lower]
        unmatched = [skill for skill in internship_skills_lower if skill not in user_skills]

        skill_score = (len(matched) / len(internship_skills)) * 100 if internship_skills else 0
        score += skill_score * 0.5
        total += 50

        # --- Stipend Matching (25%) ---
        stipend_score = 100 if row["stipend_max"] >= user_min_stipend else 0
        score += stipend_score * 0.25
        total += 25

        # --- Duration Matching (25%) ---
        duration_score = 100 if row["duration_value"] >= user_min_duration else 0
        score += duration_score * 0.25
        total += 25

        percentage_match = (score / total) * 100
        match_scores.append(percentage_match)

        # Missing skills + video links
        missing_skills_list.append(unmatched if unmatched else [])
        urls = [youtube_links[s] for s in unmatched if s in youtube_links]
        missing_urls_list.append(urls if urls else [])

    # Add results to DataFrame
    df["match_percentage"] = match_scores
    df["missing_skills"] = missing_skills_list
    df["missing_skill_urls"] = missing_urls_list

    # Sort & return top 3
    df_sorted = df.sort_values(by="match_percentage", ascending=False).head(3)
    return jsonify(df_sorted.to_dict(orient="records"))


if __name__ == "__main__":
    app.run(debug=True)
