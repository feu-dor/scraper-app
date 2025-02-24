import datetime
import requests
import gspread
from bs4 import BeautifulSoup
from flask import Flask, jsonify
from google.oauth2.service_account import Credentials

app = Flask(__name__)

# ----------------- Google Sheets Setup -----------------
CREDS_FILE = "parser-data-keys-95bc06b487e1.json"
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
creds = Credentials.from_service_account_file(CREDS_FILE, scopes=SCOPES)
client = gspread.authorize(creds)
sheet = client.open("monitoring summary").worksheet("Parcel&Postal")

# ----------------- Helper Function -----------------
def strip_html(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    return soup.get_text()

# ----------------- Data Fetching -----------------
def fetch_website_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        print(f"Failed to fetch website data from {url}. Status code: {response.status_code}")
        return []
    
    posts = response.json()
    data = []
    for post in posts:
        main_html = post.get("content", {}).get("rendered", "")
        main_text = strip_html(main_html)
        entry = {
            "date of a publication": post.get("date", ""),
            "title": post.get("title", {}).get("rendered", ""),
            "main content": main_text,
            "Link": post.get("link", "")
        }
        data.append(entry)
    return data

def update_sheet(sheet, data):
    # Get current sheet values
    current_values = sheet.get_all_values()
    row_count = len(current_values)
    # Build set of existing links (assuming first row is header)
    existing_links = set()
    for row in current_values[1:]:
        if len(row) >= 5:
            existing_links.add(row[4])
    new_entries_added = 0
    for entry in data:
        link = entry.get("Link", "")
        if link and link not in existing_links:
            row_number = row_count + new_entries_added + 1
            row_data = [
                row_number,
                entry.get("date of a publication", ""),
                entry.get("title", ""),
                entry.get("main content", ""),
                link
            ]
            sheet.append_row(row_data)
            new_entries_added += 1
            existing_links.add(link)
    return new_entries_added

# ----------------- Flask Endpoint -----------------
@app.route("/run_scraper", methods=["GET"])
def run_scraper():
    website_url = "https://www.parcelandpostaltechnologyinternational.com/wp-json/wp/v2/posts"
    website_data = fetch_website_data(website_url)
    if website_data:
        new_count = update_sheet(sheet, website_data)
        return jsonify({"status": "success", "new_posts_added": new_count}), 200
    else:
        return jsonify({"status": "failed", "message": "No data fetched from the website"}), 500

# Optional: A basic index route
@app.route("/", methods=["GET"])
def index():
    return "Scraper is running. Use /run_scraper to update data."

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
