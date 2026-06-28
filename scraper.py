#!/usr/bin/env python3
"""
Nigeria Lead Scraper v2 — Real business data from Google Maps via Playwright.
No API key needed. Fetches actual Lagos businesses, filters out those with websites,
validates Nigerian phone numbers, and outputs 50 quality leads/day.
"""

import csv
import hashlib
import json
import os
import random
import re
import time
from datetime import datetime, timezone
from urllib.parse import quote_plus

from config import (
    DISCORD_WEBHOOK_LEADS, DAILY_LEADS_TARGET,
    LAGOS_AREAS, OTHER_CITIES, BUSINESS_CATEGORIES,
    DATA_DIR, REPORTS_DIR, LEADS_DB,
)

# ─── Dedup DB ────────────────────────────────────────────────────────

def load_dedup():
    if os.path.exists(LEADS_DB):
        return set(json.loads(open(LEADS_DB, encoding="utf-8").read()))
    return set()

def save_dedup(hashed):
    open(LEADS_DB, "w", encoding="utf-8").write(json.dumps(list(hashed), ensure_ascii=False))

def lead_hash(name, phone, address):
    raw = f"{(name or '').lower().strip()}|{(phone or '').strip()}|{(address or '').lower().strip()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:14]

# ─── Nigerian Phone Validation ────────────────────────────────────────

VALID_PREFIXES = ("080", "081", "070", "071", "090", "091")

def is_valid_nigerian_phone(phone):
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("234") and len(digits) == 13:
        digits = "0" + digits[3:]
    if len(digits) != 11 or not digits.startswith("0"):
        return False
    return any(digits.startswith(p) for p in VALID_PREFIXES)

def format_nigerian_phone(phone):
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("234"):
        digits = "0" + digits[3:]
    if len(digits) == 11 and digits.startswith("0"):
        return f"+234{digits[1:]}"
    return phone.strip()

# ─── Text Extraction ──────────────────────────────────────────────────

def extract_phone_from_text(text):
    patterns = [
        r'\+234[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',
        r'\+234[\s\-]?\d{10}',
        r'0\d{3}[\s\-]?\d{3}[\s\-]?\d{4}',
        r'0\d{10}',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for m in matches:
            if is_valid_nigerian_phone(m):
                return format_nigerian_phone(m)
    return ""

def extract_email_from_text(text):
    emails = re.findall(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text)
    bad_exts = ('.png', '.jpg', '.gif', '.svg', '.webp', '.css', '.js')
    valid = [e for e in emails if not any(e.endswith(ext) for ext in bad_exts)]
    return valid[0] if valid else ""

# ─── Playwright Google Maps Scraper ───────────────────────────────────

def scrape_google_maps_playwright(query, max_results=20):
    """Scrape Google Maps using Playwright headless browser."""
    from playwright.sync_api import sync_playwright

    leads = []
    search_url = f"https://www.google.com/maps/search/{quote_plus(query)}/"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"]
            )
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = context.new_page()

            page.goto(search_url, timeout=30000, wait_until="domcontentloaded")
            page.wait_for_timeout(3000)

            # Handle consent dialog
            for text in ["Accept all", "Accept", "I agree", "Acepto"]:
                try:
                    btn = page.locator(f'button:has-text("{text}")').first
                    if btn.count():
                        btn.click(timeout=3000)
                        page.wait_for_timeout(2000)
                        break
                except:
                    pass

            # Scroll the results panel
            try:
                panel = page.locator("div[role='feed']").first
                if panel.count():
                    for _ in range(10):
                        panel.evaluate("el => el.scrollTop = el.scrollHeight")
                        page.wait_for_timeout(800)
            except:
                pass

            # Extract results
            items = page.locator("div.Nv2PK, a.hfpxzc").all()
            print(f"  Found {len(items)} raw results for: {query}")

            for item in items[:max_results]:
                try:
                    # Get business name
                    name_el = item.locator(".qBF1Pd, .fontHeadlineSmall, .NrDZNb").first
                    name = name_el.inner_text(timeout=2000) if name_el.count() else ""
                    if not name or len(name) < 3:
                        # Try getting from aria-label
                        name = item.get_attribute("aria-label") or ""
                    if not name or len(name) < 3:
                        continue

                    # Click to open detail panel
                    link = item.locator("a.hfpxzc, a").first
                    if link.count():
                        link.click(timeout=3000)
                        page.wait_for_timeout(2000)

                    # Extract from detail panel
                    detail_text = ""

                    # Phone number
                    phone = ""
                    try:
                        phone_el = page.locator('button[data-item-id*="phone"], a[data-item-id*="phone"]').first
                        if phone_el.count():
                            phone_text = phone_el.get_attribute("aria-label") or phone_el.inner_text(timeout=2000)
                            phone = extract_phone_from_text(phone_text)
                    except:
                        pass

                    if not phone:
                        try:
                            # Try the info section
                            info_items = page.locator("div.fontBodyMedium span").all()
                            for info in info_items:
                                txt = info.inner_text(timeout=1000)
                                phone = extract_phone_from_text(txt)
                                if phone:
                                    break
                        except:
                            pass

                    # Website
                    website = ""
                    try:
                        web_el = page.locator('a[data-item-id*="authority"], a[data-item-id*="website"]').first
                        if web_el.count():
                            website = web_el.get_attribute("href") or ""
                    except:
                        pass

                    # Address
                    address = ""
                    try:
                        addr_el = page.locator('button[data-item-id*="address"], div[data-item-id*="address"]').first
                        if addr_el.count():
                            address = addr_el.inner_text(timeout=2000)
                    except:
                        pass

                    # Rating
                    rating = 0.0
                    try:
                        rating_el = item.locator(".MW4etd, span.ZkP5Je").first
                        if rating_el.count():
                            rating_text = rating_el.inner_text(timeout=1000)
                            rating = float(re.sub(r"[^\d.]", "", rating_text) or 0)
                    except:
                        pass

                    # Reviews count
                    reviews = 0
                    try:
                        rev_el = item.locator("span.UY7F9, span.ceNzKf").first
                        if rev_el.count():
                            rev_text = rev_el.inner_text(timeout=1000)
                            reviews = int(re.sub(r"\D", "", rev_text) or 0)
                    except:
                        pass

                    # Category
                    category = ""
                    try:
                        cat_el = page.locator("button.DkEaL, span.DkEaL").first
                        if cat_el.count():
                            category = cat_el.inner_text(timeout=1000)
                    except:
                        pass

                    # Skip if has website
                    if website and "google.com" not in website and "maps.google" not in website:
                        continue

                    # Validate phone
                    if not phone or not is_valid_nigerian_phone(phone):
                        continue

                    # Get Google Maps URL
                    maps_url = page.url

                    leads.append({
                        "business_name": name,
                        "category": category,
                        "phone": phone,
                        "email": "",
                        "address": address,
                        "city": "Lagos",
                        "area": "",
                        "rating": rating,
                        "review_count": reviews,
                        "website": "",
                        "google_maps_url": maps_url,
                        "latitude": "",
                        "longitude": "",
                        "source": "google_maps",
                        "scraped_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                        "lead_id": "",
                    })

                except Exception as e:
                    continue

            browser.close()

    except Exception as e:
        print(f"  Playwright error: {e}")

    return leads

# ─── Bing Search Fallback ─────────────────────────────────────────────

def scrape_bing_fallback(query, city):
    """Fallback: search Bing for business listings."""
    import httpx
    from bs4 import BeautifulSoup

    url = f"https://www.bing.com/search?q={quote_plus(query + ' ' + city + ' Nigeria phone contact')}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }

    leads = []
    try:
        r = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        if r.status_code != 200:
            return leads

        soup = BeautifulSoup(r.text, "html.parser")
        for li in soup.find_all("li", class_="b_algo"):
            h2 = li.find("h2")
            if not h2:
                continue
            a = h2.find("a")
            name = a.get_text(strip=True) if a else ""
            snippet = li.get_text(separator=" ", strip=True)

            phone = extract_phone_from_text(snippet)
            if not phone or not is_valid_nigerian_phone(phone):
                continue

            website = a.get("href", "") if a else ""
            if website and "google.com" not in website and "bing.com" not in website:
                continue  # Has a website

            email = extract_email_from_text(snippet)

            leads.append({
                "business_name": name,
                "category": query.split(" in ")[0] if " in " in query else query,
                "phone": phone,
                "email": email,
                "address": "",
                "city": city,
                "area": "",
                "rating": 0,
                "review_count": 0,
                "website": "",
                "google_maps_url": website,
                "latitude": "",
                "longitude": "",
                "source": "bing",
                "scraped_date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
                "lead_id": "",
            })

    except Exception as e:
        print(f"  Bing error: {e}")

    return leads

# ─── Main Scraper ─────────────────────────────────────────────────────

def scrape_leads(target=DAILY_LEADS_TARGET):
    """Scrape real Lagos business leads."""
    print(f"{'='*60}")
    print(f"Nigeria Lead Scraper v2 — Real Google Maps Data")
    print(f"Target: {target} leads (Lagos-focused)")
    print(f"{'='*60}")

    dedup = load_dedup()
    print(f"Dedup DB: {len(dedup)} existing leads")

    all_leads = []
    seen_hashes = set(dedup)

    # Build search tasks: Lagos first (80%), then other cities (20%)
    tasks = []

    for area in LAGOS_AREAS:
        cats = random.sample(BUSINESS_CATEGORIES, min(6, len(BUSINESS_CATEGORIES)))
        for cat in cats:
            tasks.append((cat, area, "Lagos"))

    for city, areas in OTHER_CITIES.items():
        for area in areas[:2]:
            cats = random.sample(BUSINESS_CATEGORIES, min(3, len(BUSINESS_CATEGORIES)))
            for cat in cats:
                tasks.append((cat, area, city))

    random.shuffle(tasks)
    print(f"Search tasks: {len(tasks)}")

    for i, (category, area, city) in enumerate(tasks):
        if len(all_leads) >= target:
            print(f"Target reached: {len(all_leads)} leads")
            break

        query = f"{category} in {area}, {city}"
        print(f"[{i+1}/{len(tasks)}] {query}")

        # Try Playwright first
        results = scrape_google_maps_playwright(query, max_results=15)

        # Fallback to Bing if Playwright fails
        if not results:
            print(f"  Playwright returned 0, trying Bing fallback...")
            results = scrape_bing_fallback(query, city)

        for lead in results:
            if len(all_leads) >= target:
                break

            h = lead_hash(lead["business_name"], lead["phone"], lead["address"])
            if h in seen_hashes:
                continue
            seen_hashes.add(h)
            lead["lead_id"] = f"NGA-{h[:8].upper()}"
            lead["area"] = area
            all_leads.append(lead)

        # Delay between searches
        time.sleep(random.uniform(2, 4))

        if (i + 1) % 5 == 0:
            print(f"  Progress: {i+1}/{len(tasks)} | Leads: {len(all_leads)}")

    save_dedup(seen_hashes)

    # Sort by quality
    def quality_score(l):
        s = 0
        if l["phone"]: s += 5
        if l["email"]: s += 5
        if l["rating"] >= 4.0: s += 3
        if l["review_count"] >= 10: s += 2
        if l["address"]: s += 1
        return s

    all_leads.sort(key=quality_score, reverse=True)

    print(f"\nTotal leads scraped: {len(all_leads)}")
    return all_leads[:target]

# ─── CSV Output ───────────────────────────────────────────────────────

def save_leads_csv(leads, filename="nigeria_leads.csv"):
    if not leads:
        print("No leads to save.")
        return None

    path = os.path.join(REPORTS_DIR, filename)
    fields = [
        "lead_id", "business_name", "category", "phone", "email",
        "address", "city", "area", "rating", "review_count",
        "website", "google_maps_url", "latitude", "longitude",
        "source", "scraped_date",
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for lead in leads:
            writer.writerow({k: lead.get(k, "") for k in fields})

    print(f"Saved {len(leads)} leads to {path}")
    return path

# ─── Discord Notification ─────────────────────────────────────────────

def send_discord_leads(leads, csv_path):
    import requests as req

    today = datetime.now().strftime("%Y-%m-%d")

    cities = {}
    categories = {}
    for l in leads:
        c = l.get("city", "Unknown")
        cat = l.get("category", "Unknown")
        cities[c] = cities.get(c, 0) + 1
        categories[cat] = categories.get(cat, 0) + 1

    top_cities = sorted(cities.items(), key=lambda x: -x[1])[:5]
    top_cats = sorted(categories.items(), key=lambda x: -x[1])[:5]

    with_email = sum(1 for l in leads if l.get("email"))
    with_phone = sum(1 for l in leads if l.get("phone"))

    embed = {
        "title": f"Nigeria Leads — {today}",
        "description": f"**{len(leads)} real business leads** from Google Maps\nLagos-focused, no websites",
        "color": 0x00FF00,
        "fields": [
            {"name": "Total Leads", "value": str(len(leads)), "inline": True},
            {"name": "With Phone", "value": str(with_phone), "inline": True},
            {"name": "With Email", "value": str(with_email), "inline": True},
            {"name": "Cities", "value": "\n".join(f"{c}: {n}" for c, n in top_cities), "inline": False},
            {"name": "Categories", "value": "\n".join(f"{c}: {n}" for c, n in top_cats), "inline": False},
        ],
        "footer": {"text": "Nigeria Lead Scraper v2 | Real Google Maps Data"},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    payload = {
        "content": f"**Daily Nigeria Leads** — {len(leads)} real businesses found!",
        "embeds": [embed],
    }

    try:
        with open(csv_path, "rb") as f:
            files = {"file": ("nigeria_leads.csv", f, "text/csv")}
            data = {"payload_json": json.dumps(payload)}
            resp = req.post(DISCORD_WEBHOOK_LEADS, data=data, files=files, timeout=30)
            print(f"Discord response: {resp.status_code}")
            return resp.status_code in [200, 204]
    except Exception as e:
        print(f"Discord error: {e}")
        return False

# ─── Main ─────────────────────────────────────────────────────────────

def main():
    start = datetime.now()
    print(f"Started at {start}")

    leads = scrape_leads(DAILY_LEADS_TARGET)

    if leads:
        csv_path = save_leads_csv(leads)
        if csv_path:
            send_discord_leads(leads, csv_path)

        json_path = os.path.join(DATA_DIR, "latest_leads.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(leads, f, indent=2, ensure_ascii=False)
        print(f"JSON saved: {json_path}")
    else:
        print("No leads found. Try again later.")

    elapsed = (datetime.now() - start).total_seconds()
    print(f"\nDone in {elapsed:.1f}s")
    return leads

if __name__ == "__main__":
    main()
