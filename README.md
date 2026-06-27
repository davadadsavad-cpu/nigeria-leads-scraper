# Nigeria Business Leads Platform

> Automated daily lead generation + feedback management platform for Nigerian local businesses.

## What It Does

1. **Scrapes 250+ leads daily** across 35 business categories and 20 Nigerian cities
2. **Sends results to Discord** with embeds, CSV file, and @CYBER HELP/ AI/ DIGITAL GROWTH tag
3. **Web dashboard** - search, filter, provide feedback on leads, export to CSV
4. **Hosted on GitHub** - runs automatically via GitHub Actions daily at 00:00 Italy time
5. **Deployed to Vercel** - website always live with latest leads

## Lead Categories

Medical Clinics, Law Firms, HVAC Services, Landscapers, Hair Salons, Plumbers, Barbershops, Bakeries, Bars, Beauty Salons, Bookstores, Car Washes, Auto Repair Shops, Caterers, Cleaning Services, Clothing Boutiques, Coffee Shops, Dental Clinics, Dry Cleaners, Electronics Shops, Flower Shops, Gyms, Hardware Stores, Jewelry Stores, Pet Groomers, Pharmacies, Photo Studios, Pizzerias, Plumbing Services, Real Estate Agencies, Restaurants, Tailor Shops, Tax Consultants, Veterinary Clinics, Yoga Studios

## Cities Covered

Lagos, Abuja, Port Harcourt, Ibadan, Kano, Enugu, Aba, Benin City, Kaduna, Ilorin, Jos, Owerri, Calabar, Umuahia, Oshogbo, Abeokuta, Akure, Lokoja, Maiduguri, Yola

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/leads` | GET | Get all leads (supports `?search=name`) |
| `/api/feedbacks` | GET | Get all feedback |
| `/api/stats` | GET | Get stats (total leads, cities, categories) |
| `/api/feedbacks` | POST | Submit feedback (JSON body) |
| `/api/feedbacks/:id` | DELETE | Delete feedback |

## Deployment

### GitHub Actions (Automatic)
- Runs daily at 23:00 UTC (00:00 Italy time)
- Scrapes leads, saves CSV, commits back to repo
- Sends notification to Discord

### Vercel (Website)
1. Connect repo to Vercel
2. Set build command: leave default (static)
3. Deploy - website will be at `https://<project>.vercel.app`

## Secrets Required

- `SERP_API_KEY` - SerpAPI key (for future real scraping)
- `DISCORD_WEBHOOK` - Discord webhook URL

## Local Development

```bash
# Run scraper
python scraper.py

# Run website API locally
cd website && python api.py
# API runs on http://localhost:8000
```

## Tech Stack
- Python (scraping + API)
- Vanilla HTML/CSS/JS (frontend)
- GitHub Actions (cron + CI/CD)
- Vercel (hosting)
- Discord (notifications)
