#!/usr/bin/env python3
"""Configuration for Nigeria Lead Scraper + Email Campaign System."""
import os

# === SerpAPI (optional — Playwright is primary) ===
SERP_API_KEY = os.environ.get("SERP_API_KEY", "")

# === Gmail SMTP ===
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_FROM = "eclatagency96@gmail.com"
EMAIL_FROM_NAME = "Eclat Agency"
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD", "")  # Gmail app password from secrets

# === Discord Webhooks ===
DISCORD_WEBHOOK_LEADS = "https://discordapp.com/api/webhooks/1520090981435834488/avDNVwgIK2uZKCoreOuP1aVP7-X-GufHwxkoKJPHKnY4LJIatLxcramFFpFzb9fc5cJ4"
DISCORD_WEBHOOK_EMAILS = "https://discordapp.com/api/webhooks/1520227344261058721/kH1OnCV6j_ix0-twF6vXk-QU0TzgQnEe4e1GYRQXK2xqZR5JaI_gtzgfTSHd__QZFS-T"

# === Campaign Settings ===
DAILY_LEADS_TARGET = 50
DAILY_EMAILS_TARGET = 250
SEND_DELAY_SECONDS = 30

# === Lagos Areas (priority — 80% of leads) ===
LAGOS_AREAS = [
    "Lagos Island", "Victoria Island", "Ikeja", "Lekki", "Ajah",
    "Surulere", "Yaba", "Ikoyi", "Epe", "Badagry",
    "Mushin", "Oshodi", "Agege", "Ikorodu", "Alimosho",
    "Kosofe", "Shomolu", "Ojo", "Amuwo-Odofin", "Ajeromi-Ifelodun",
]

# === Other Nigerian Cities (secondary — 20% of leads) ===
OTHER_CITIES = {
    "Abuja": ["Garki", "Wuse", "Maitama", "Asokoro", "Gwarinpa"],
    "Port Harcourt": ["Trans Amadi", "D-Line", "Diobu", "Woji", "Rumuola"],
    "Ibadan": ["Bodija", "Agodi", "Mokola", "Dugbe", "Challenge"],
    "Kano": ["Shuwari", "Fagge", "Dala", "Gwale", "Kumbotso"],
}

# === Business Categories (Nigeria-relevant) ===
BUSINESS_CATEGORIES = [
    "restaurant",
    "hair salon",
    "barber shop",
    "pharmacy",
    "bakery",
    "boutique",
    "electronics store",
    "plumber",
    "car wash",
    "photo studio",
    "gym",
    "real estate agency",
    "law firm",
    "dental clinic",
    "beauty salon",
    "cleaning service",
    "tailor shop",
    "hardware store",
    "coffee shop",
    "auto repair shop",
]

# === Paths ===
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
REPORTS_DIR = os.path.join(ROOT_DIR, "reports")
LEADS_DB = os.path.join(DATA_DIR, "leads_dedup.json")
SENT_FILE = os.path.join(DATA_DIR, "sent_emails.csv")
PENDING_FILE = os.path.join(DATA_DIR, "pending_emails.csv")
EMAIL_LOG = os.path.join(DATA_DIR, "email_log.csv")

for d in [DATA_DIR, REPORTS_DIR]:
    os.makedirs(d, exist_ok=True)

# === Email Templates Context ===
YOUR_NAME = "David"
YOUR_COMPANY = "Eclat Agency"
YOUR_PHONE = "+39 377 573 2812"
YOUR_WEBSITE = "https://eclat-agency.vercel.app"
