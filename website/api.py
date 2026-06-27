#!/usr/bin/env python3
"""
Lead Feedback API - serves leads from CSV and stores feedback
Run with: python api.py
Deploy to Vercel with vercel.json config
"""
import csv, json, os, hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

LEADS_DIR = os.path.dirname(__file__)
FEEDBACK_FILE = os.path.join(LEADS_DIR, "feedbacks.json")

# Load leads from CSV files
def load_leads():
    leads = []
    for fname in ["reports/priority_leads_latest.csv", "reports/mixed_leads_latest.csv"]:
        path = os.path.join(LEADS_DIR, fname)
        if os.path.exists(path):
            with open(path, encoding="utf-8-sig") as f:
                for row in csv.DictReader(f):
                    leads.append({
                        "id": row.get("lead_id") or hashlib.md5((row.get("name","")+row.get("phone","")+row.get("city","")).encode()).hexdigest()[:12],
                        "name": row.get("name") or row.get("business_name", ""),
                        "phone": row.get("phone", ""),
                        "address": row.get("address", ""),
                        "city": row.get("city", ""),
                        "state": row.get("state", ""),
                        "website": row.get("website", ""),
                        "rating": row.get("rating", ""),
                        "category": row.get("category", ""),
                        "source": row.get("source", "serper"),
                    })
    # Also merge with any date-specific files
    reports_dir = os.path.join(LEADS_DIR, "reports")
    if os.path.exists(reports_dir):
        for f in os.listdir(reports_dir):
            if f.startswith("priority_leads_") and f.endswith(".csv") and "latest" not in f:
                path = os.path.join(reports_dir, f)
                with open(path, encoding="utf-8-sig") as csvfile:
                    for row in csv.DictReader(csvfile):
                        if row.get("lead_id") and len(row["lead_id"])>=8:
                            leads.append({
                                "id": row["lead_id"],
                                "name": row.get("name") or row.get("business_name", ""),
                                "phone": row.get("phone", ""),
                                "address": row.get("address", ""),
                                "city": row.get("city", ""),
                                "state": row.get("state", ""),
                                "website": row.get("website", ""),
                                "rating": row.get("rating", ""),
                                "category": row.get("category", ""),
                                "source": "serper",
                            })
    # Deduplicate by ID
    seen = set()
    unique = []
    for lead in leads:
        if lead["id"] not in seen:
            seen.add(lead["id"])
            unique.append(lead)
    return unique

def load_feedbacks():
    if os.path.exists(FEEDBACK_FILE):
        with open(FEEDBACK_FILE, encoding="utf-8") as f:
            return json.load(f)
    return []

def save_feedbacks(feedbacks):
    with open(FEEDBACK_FILE, "w", encoding="utf-8") as f:
        json.dump(feedbacks, f, indent=2)

class Handler(BaseHTTPRequestHandler):
    def add_cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self.add_cors()
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        if url.path == "/api/leads":
            leads = load_leads()
            search = url.query.get("search", [""])[0].lower() if "?" in self.path else ""
            if search:
                leads = [l for l in leads if search in l["name"].lower() or search in l["phone"].lower() or search in l["city"].lower()]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_cors()
            self.end_headers()
            self.wfile.write(json.dumps(leads).encode())
        elif url.path == "/api/feedbacks":
            feedbacks = load_feedbacks()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_cors()
            self.end_headers()
            self.wfile.write(json.dumps(feedbacks).encode())
        elif url.path == "/api/stats":
            leads = load_leads()
            feedbacks = load_feedbacks()
            cities = set(l["city"] for l in leads if l["city"])
            categories = set(l["category"] for l in leads if l["category"])
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_cors()
            self.end_headers()
            stats = {
                "total_leads": len(leads),
                "cities_count": len(cities),
                "categories_count": len(categories),
                "feedback_count": len(feedbacks)
            }
            self.wfile.write(json.dumps(stats).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        url = urlparse(self.path)
        if url.path == "/api/feedbacks":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length).decode()
            data = json.loads(body)
            feedbacks = load_feedbacks()
            feedbacks.append({
                "id": hashlib.md5(f"{data['name']}{datetime.now()}".encode()).hexdigest()[:12],
                "name": data["name"],
                "company": data.get("company", ""),
                "text": data["text"],
                "status": data.get("status", "New"),
                "rating": int(data.get("rating", 0)),
                "date": datetime.now().isoformat(),
                "lead_id": data.get("lead_id", "")
            })
            save_feedbacks(feedbacks)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_cors()
            self.end_headers()
            self.wfile.write(b'{"status":"saved"}')
        else:
            self.send_response(404)
            self.end_headers()

    def do_DELETE(self):
        url = urlparse(self.path)
        if url.path.startswith("/api/feedbacks/"):
            fid = url.path.split("/")[-1]
            feedbacks = load_feedbacks()
            feedbacks = [f for f in feedbacks if f.get("id") != fid]
            save_feedbacks(feedbacks)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.add_cors()
            self.end_headers()
            self.wfile.write(b'{"status":"deleted"}')
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # Silent logging

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    server = HTTPServer(("", port), Handler)
    print(f"API running on port {port}")
    server.serve_forever()
