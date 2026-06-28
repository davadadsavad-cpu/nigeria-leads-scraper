#!/usr/bin/env python3
"""
Nigeria Lead Pipeline — runs scraper + email campaign in sequence.
Schedule: 9 AM Italy time daily.

Usage:
  python pipeline.py              # Full run (scrape + email)
  python pipeline.py --scrape     # Scrape only
  python pipeline.py --email      # Email only
  python pipeline.py --dry-run    # Test without sending
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from scraper import scrape_leads, save_leads_csv, send_discord_leads
from email_campaign import run_campaign
from config import DATA_DIR, REPORTS_DIR


def run_pipeline(scrape=True, email=True, dry_run=False):
    """Run the full pipeline."""
    start = datetime.now()
    print(f"\n{'#'*60}")
    print(f"# Nigeria Lead Pipeline")
    print(f"# Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"# Mode: {'DRY RUN' if dry_run else 'LIVE'}")
    print(f"{'#'*60}\n")

    results = {}

    # Step 1: Scrape leads
    if scrape:
        print("="*60)
        print("STEP 1: Scraping real Lagos business leads...")
        print("="*60)
        leads = scrape_leads(target=50)
        results["leads_scraped"] = len(leads)

        if leads:
            csv_path = save_leads_csv(leads)
            send_discord_leads(leads, csv_path)
        else:
            print("No leads scraped. Check API connection.")
    else:
        print("Skipping scrape.")
        # Load existing leads
        import json
        json_path = os.path.join(DATA_DIR, "latest_leads.json")
        if os.path.exists(json_path):
            with open(json_path, encoding="utf-8") as f:
                leads = json.load(f)
            print(f"Loaded {len(leads)} existing leads")
        else:
            leads = []

    # Step 2: Send emails
    if email and leads:
        print("\n" + "="*60)
        print("STEP 2: Running email campaign...")
        print("="*60)
        sent, failed, pending = run_campaign(leads=leads, dry_run=dry_run)
        results["emails_sent"] = sent
        results["emails_failed"] = failed
        results["emails_pending"] = pending
    elif email and not leads:
        print("No leads available for email campaign.")

    # Summary
    elapsed = (datetime.now() - start).total_seconds()
    print(f"\n{'#'*60}")
    print(f"# Pipeline Complete")
    print(f"# Duration: {elapsed:.1f}s")
    print(f"# Results: {results}")
    print(f"{'#'*60}")

    return results


if __name__ == "__main__":
    scrape = "--scrape" in sys.argv or len(sys.argv) == 1
    email = "--email" in sys.argv or len(sys.argv) == 1
    dry_run = "--dry-run" in sys.argv

    if "--scrape" in sys.argv and "--email" not in sys.argv:
        email = False
    if "--email" in sys.argv and "--scrape" not in sys.argv:
        scrape = False

    run_pipeline(scrape=scrape, email=email, dry_run=dry_run)
