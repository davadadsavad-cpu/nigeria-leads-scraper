#!/usr/bin/env python3
"""
Email Campaign System for Nigeria Leads.
- Generates personalized emails for each lead
- Sends via Gmail SMTP
- Tracks sent/pending for follow-up loop
- Notifies Discord with email links
"""

import csv
import json
import os
import random
import smtplib
import time
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import (
    SMTP_SERVER, SMTP_PORT, EMAIL_FROM, EMAIL_FROM_NAME, SMTP_APP_PASSWORD,
    DISCORD_WEBHOOK_EMAILS, DAILY_EMAILS_TARGET, SEND_DELAY_SECONDS,
    DATA_DIR, REPORTS_DIR, SENT_FILE, PENDING_FILE, EMAIL_LOG,
    YOUR_NAME, YOUR_COMPANY, YOUR_PHONE, YOUR_WEBSITE,
)

# ─── Email Templates ──────────────────────────────────────────────────

TEMPLATES = [
    {
        "subject": "Help {business} get more customers online",
        "body": """Hi {owner},

I came across {business} in {city} and was impressed by your {category} business.

I noticed you don't have a website yet — which means potential customers searching online can't find you. In Lagos, most people search Google before visiting any business.

I'd love to help you get online with a professional website that:
- Shows up when people search for {category} in {city}
- Displays your services, location, and contact details
- Lets customers reach you directly via WhatsApp or phone

It's simpler and more affordable than you think.

Would you be open to a quick 10-minute call this week to discuss?

Best regards,
{your_name}
{your_company}
{your_phone}
{your_website}""",
    },
    {
        "subject": "Your {business} deserves an online presence",
        "body": """Hello {owner},

I hope this message finds you well. I'm {your_name} from {your_company}.

I was looking for {category} businesses in {city} and found {business} — great reviews! But I noticed you don't have a website yet.

Here's the thing: 70% of customers in Lagos search online before choosing a {category}. Without a website, you're missing out on all those potential customers.

I can build you a simple, professional website that:
- Ranks on Google when people search for {category} in {city}
- Shows your business hours, location on a map, and services
- Works perfectly on mobile phones

Interested? Just reply to this email or call me at {your_phone}.

Cheers,
{your_name}
{your_company}""",
    },
    {
        "subject": "Quick question about {business}",
        "body": """Hi {owner},

Quick question — have you ever had a customer say "I couldn't find your website so I went somewhere else"?

That happens to a lot of great businesses in {city} that don't have an online presence yet.

I help {category} businesses like {business} get found online with a professional website. It takes just a few days to set up and costs less than you'd expect.

Want me to show you what other {category} businesses in Lagos are doing?

Reply "yes" and I'll send you some examples.

Best,
{your_name}
{your_company}
{your_phone}""",
    },
    {
        "subject": "Free website consultation for {business}",
        "body": """Hello {owner},

I'm {your_name} from {your_company}, and I help local businesses in Lagos get online.

I found {business} while researching {category} businesses in {city} and wanted to reach out.

I'm offering a free 15-minute consultation where I'll:
- Show you what a professional website looks like for {category} businesses
- Explain how it can bring you more customers
- Give you a custom quote — no obligation

Many business owners are surprised how simple and affordable it is.

Would next Tuesday or Wednesday work for a quick call?

Best regards,
{your_name}
{your_company}
{your_phone}""",
    },
]

# ─── Personalization ──────────────────────────────────────────────────

def personalize_email(lead, template):
    """Fill template with lead data."""
    business = lead.get("business_name", "your business")
    city = lead.get("city", "Lagos")
    category = lead.get("category", "business")
    owner = lead.get("email", "").split("@")[0].replace(".", " ").replace("_", " ").replace("-", " ").title()
    if not owner or len(owner) < 3:
        owner = "Owner"

    subject = template["subject"].format(
        business=business, owner=owner, city=city, category=category,
    )
    body = template["body"].format(
        business=business, owner=owner, city=city, category=category,
        your_name=YOUR_NAME, your_company=YOUR_COMPANY,
        your_phone=YOUR_PHONE, your_website=YOUR_WEBSITE,
    )
    return subject, body

# ─── Send Engine ───────────────────────────────────────────────────────

def load_sent():
    """Load set of already-sent email addresses."""
    if os.path.exists(SENT_FILE):
        with open(SENT_FILE, "r", encoding="utf-8") as f:
            return {row[0].strip().lower() for row in csv.reader(f) if row}
    return set()

def load_pending():
    """Load pending leads (from previous day's unfinished batch)."""
    if os.path.exists(PENDING_FILE):
        with open(PENDING_FILE, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    return []

def save_pending(leads):
    """Save unsent leads for next day."""
    if not leads:
        if os.path.exists(PENDING_FILE):
            os.remove(PENDING_FILE)
        return
    fields = ["business_name", "category", "phone", "email", "address", "city", "area",
              "rating", "review_count", "lead_id", "source"]
    with open(PENDING_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in fields})

def log_email(email, business, subject, status, error=""):
    """Log email send attempt."""
    with open(EMAIL_LOG, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow([
            datetime.now().isoformat(), email, business, subject, status, error,
        ])

def send_single_email(to_email, subject, body):
    """Send one email via Gmail SMTP."""
    msg = MIMEMultipart("alternative")
    msg["From"] = f"{EMAIL_FROM_NAME} <{EMAIL_FROM}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_FROM, SMTP_APP_PASSWORD)
        server.sendmail(EMAIL_FROM, to_email, msg.as_string())
        server.quit()
        return True, ""
    except Exception as e:
        return False, str(e)

def send_discord_email_link(lead, subject, email_url=""):
    """Notify Discord when an email is sent."""
    payload = {
        "content": (
            f"**Email Sent** to {lead.get('business_name', '?')}\n"
            f"To: {lead.get('email', '?')}\n"
            f"Subject: {subject}\n"
            f"Category: {lead.get('category', '?')} | City: {lead.get('city', '?')}"
        ),
    }
    try:
        import requests
        resp = requests.post(DISCORD_WEBHOOK_EMAILS, json=payload, timeout=15)
        return resp.status_code in [200, 204]
    except:
        return False

# ─── Campaign Runner ──────────────────────────────────────────────────

def run_campaign(leads=None, target=DAILY_EMAILS_TARGET, dry_run=False):
    """
    Run email campaign. If leads is None, loads from latest_leads.json.
    Handles follow-up: pending emails from yesterday are sent first.
    """
    print(f"{'='*60}")
    print(f"Email Campaign — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*60}")

    # Load pending from yesterday first
    pending = load_pending()
    if pending:
        print(f"Loading {len(pending)} pending leads from yesterday")

    # Load fresh leads
    if leads is None:
        json_path = os.path.join(DATA_DIR, "latest_leads.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                leads = json.load(f)
            print(f"Loaded {len(leads)} fresh leads from JSON")
        else:
            leads = []
            print("No fresh leads found")

    # Combine: pending first, then fresh
    all_leads = pending + leads
    print(f"Total leads to process: {len(all_leads)}")

    # Filter: must have email, not already sent
    sent = load_sent()
    unsent = []
    for l in all_leads:
        email = (l.get("email") or "").strip().lower()
        if not email or "@" not in email:
            continue
        if email in sent:
            continue
        unsent.append(l)

    print(f"Unsent leads with email: {len(unsent)}")

    # Take up to target
    to_send = unsent[:target]
    remaining = unsent[target:]

    print(f"Will send: {len(to_send)} emails")
    print(f"Remaining for tomorrow: {len(remaining)}")

    # Send emails
    sent_count = 0
    failed_count = 0

    for i, lead in enumerate(to_send):
        email = lead["email"].strip().lower()
        template = random.choice(TEMPLATES)
        subject, body = personalize_email(lead, template)

        if dry_run:
            print(f"\n[DRY RUN] {i+1}/{len(to_send)}")
            print(f"  To: {email}")
            print(f"  Subject: {subject}")
            print(f"  Business: {lead.get('business_name', '?')}")
            sent_count += 1
            continue

        success, error = send_single_email(email, subject, body)

        if success:
            sent_count += 1
            sent.add(email)
            log_email(email, lead.get("business_name", ""), subject, "sent")
            send_discord_email_link(lead, subject)
            print(f"  [{sent_count}/{len(to_send)}] Sent to {lead.get('business_name', '?')} <{email}>")
        else:
            failed_count += 1
            log_email(email, lead.get("business_name", ""), subject, "failed", error)
            print(f"  FAILED: {email} — {error}")

        if i < len(to_send) - 1:
            time.sleep(SEND_DELAY_SECONDS)

    # Save remaining for tomorrow
    save_pending(remaining)

    # Save updated sent list
    with open(SENT_FILE, "w", encoding="utf-8", newline="") as f:
        for e in sent:
            f.write(f"{e}\n")

    # Summary
    print(f"\n{'='*60}")
    print(f"Campaign Summary:")
    print(f"  Sent: {sent_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Pending for tomorrow: {len(remaining)}")
    print(f"{'='*60}")

    # Send summary to Discord
    if not dry_run:
        payload = {
            "content": (
                f"**Email Campaign Summary — {datetime.now().strftime('%Y-%m-%d')}**\n"
                f"Sent: {sent_count} | Failed: {failed_count}\n"
                f"Pending for tomorrow: {len(remaining)}"
            ),
        }
        try:
            import requests
            requests.post(DISCORD_WEBHOOK_EMAILS, json=payload, timeout=15)
        except:
            pass

    return sent_count, failed_count, len(remaining)

# ─── Main ─────────────────────────────────────────────────────────────

def main():
    import sys
    dry_run = "--dry-run" in sys.argv
    run_campaign(dry_run=dry_run)

if __name__ == "__main__":
    main()
