from flask import Flask, request, jsonify, render_template
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os
import base64
import tempfile
app = Flask(__name__, template_folder="templates")

# ------------------------
# Google Sheets Connection
# ------------------------
scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
    "https://www.googleapis.com/auth/drive"
]

json_b64 = os.environ.get("INTEN_JSON_B64")
if not json_b64:
    raise RuntimeError("Missing INTEN_JSON_B64 environment variable for Google service account key")

json_str = base64.b64decode(json_b64).decode('utf-8')

with tempfile.NamedTemporaryFile(mode="w+", delete=False) as temp_file:
    temp_file.write(json_str)
    temp_file.flush()
    creds = ServiceAccountCredentials.from_json_keyfile_name(temp_file.name, scope)

client = gspread.authorize(creds)
sheet = client.open_by_url(SHEET_URL).sheet1


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

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/recommend", methods=["POST"])
def recommend():
    data = request.json
    user_skills = [s.lower() for s in data.get("skills", [])]
    user_min_stipend = int(data.get("stipend", 0))
    user_min_duration = int(data.get("duration", 0))

    records = sheet.get_all_records()

    results = []

    for row in records:
        skills_raw = row.get("skills", "")
        internship_skills = [s.strip().lower() for s in skills_raw.split(",")] if skills_raw else []

        internship_title = row.get("internship_title", "")
        company_name = row.get("company_name", "")

        try:
            stipend_min = int(row.get("stipend_min", 0))
        except:
            stipend_min = 0
        try:
            stipend_max = int(row.get("stipend_max", 0))
        except:
            stipend_max = 0
        try:
            duration_value = int(row.get("duration_value", 0))
        except:
            duration_value = 0

        matched = [skill for skill in user_skills if skill in internship_skills]
        unmatched = [skill for skill in internship_skills if skill not in user_skills]
        skill_score = (len(matched) / len(internship_skills) * 100) if internship_skills else 0

        stipend_score = 100 if stipend_max >= user_min_stipend else 0
        duration_score = 100 if duration_value >= user_min_duration else 0

        total_weight = 50 + 25 + 25
        score = (skill_score * 0.5) + (stipend_score * 0.25) + (duration_score * 0.25)
        percentage_match = (score / total_weight) * 100

        urls = [youtube_links.get(s) for s in unmatched if s in youtube_links]

        results.append({
            "internship_title": internship_title,
            "company_name": company_name,
            "stipend_min": stipend_min,
            "stipend_max": stipend_max,
            "duration_value": duration_value,
            "match_percentage": percentage_match,
            "missing_skills": unmatched,
            "missing_skill_urls": urls
        })

    top_results = sorted(results, key=lambda x: x["match_percentage"], reverse=True)[:3]

    return jsonify(top_results)

if __name__ == "__main__":
    app.run(debug=True)

