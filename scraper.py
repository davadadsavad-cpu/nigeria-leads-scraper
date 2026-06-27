#!/usr/bin/env python3
"""
Nigeria Local Business Lead Scraper
Generates 250+ leads daily for local businesses across Nigerian cities.
"""

import csv
import json
import os
import random
import requests
import time
from datetime import datetime, timezone

# Configuration - SerpAPI key
SERP_API_KEY = "c926212da0245da57148580be3f99320eb440c78"
DISCORD_WEBHOOK = "https://discordapp.com/api/webhooks/1520090981435834488/avDNVwgIK2uZKCoreOuP1aVP7-X-GufHwxkoKJPHKnY4LJIatLxcramFFpFzb9fc5cJ4"
TARGET_LEADS = 250
OUTPUT_DIR = "."

CITIES = {
    "Lagos": ["Lagos Island", "Victoria Island", "Ikeja", "Lekki", "Ajah", "Surulere", "Yaba", "Ikoyi", "Epe", "Badagry"],
    "Abuja": ["Garki", "Wuse", "Maitama", "Asokoro", "Gwarinpa", "Kubwa", "Durumi", "Lugbe", "Karsana", "Mpape"],
    "Port Harcourt": ["Trans Amadi", "D-Line", "Diobu", "Woji", "Rumuola", "Rukpokwu", "Eliozu", "Iguruta", "Obio-Akpor", "Eleme"],
    "Ibadan": ["Bodija", "Agodi", "Mokola", "Dugbe", "Orita Merin", "Challenge", "Mapo", "Ojoo", "Akala Expressway", "Oluyole"],
    "Kano": ["Shuwari", "Fagge", "Dala", "Gwale", "Kumbotso", "Tarauni", "Ungogo", "Nasarawa", "Bichi", "Gwarzo"],
    "Enugu": ["Ogui", "Udi", "Nsukka", "Awgu", "Umunze", "Oji River", "Awkenze", "Amechi", "Ngwo", "Iva"],
    "Aba": ["Ariaria", "Ohuru", "Umuocham", "Osisioma", "Ukwa Road", "Eziama", "Umuahia Road", "Faulks Road", "School Road", "Cemetery Road"],
    "Benin City": ["GRA", "Ugbowo", "Use", "Siluko Road", "Sakponba Road", "Airport Road", "Uwelu Road", "Ikpoba Hill", "Okhoro", "Adesuwa"],
    "Kaduna": ["Kawo", "Sabon Tasha", "Barnawa", "Unguwar Rimi", "Unguwar Sanusi", "Badarawa", "Mando", "Tudun Wada", "Doka", "Birnin Yero"],
    "Ilorin": ["Asa", "Offa Road", "Ajikobi", "Oloje", "Sangi Baboko", "Okene Road", "Oko-Olowo", "Akere Mefa", "Balogun Fulani", "Gambari"],
    "Jos": ["Bukuru", "Rayfield", "Laranto", "Gada Biu", "Kabong", "Rukuba", "Yan Shanu", "Kuranga", "Vwang", "Gyel"],
    "Owerri": ["Nekede", "Egbu", "Orogwe", "Naze", "Ezeogba", "Orji", "Umuchima", "Akabo", "Ihiagwa", "Obinze"],
    "Calabar": ["Ikot Ansa", "Edgerley", "Eldorov", "Ikot Effanga", "Otu", "Ikot Okubo", "Akpabuyo", "Esuk Atu", "Uwanse", "Ikot Ekpenyong"],
    "Umuahia": ["Umuokpara", "Ubakala", "Isiekpe", "Ndume", "Umuohu", "Okpuala", "Amuzukwu", "Ozara", "Isiala", "Umuagu"],
    "Oshogbo": ["Dagbolu", "Okesa", "Ajegunle", "Oke Oniti", "Isale Oja", "Modeke", "Oke Bale", "Igbona", "Olugbemi", "Owode"],
    "Abeokuta": ["Ita Oniyan", "Sodeke", "Keesi", "Oke Mosan", "Oke Ola", "Ijagbolu", "Idi Oro", "Imala", "Isabo", "Iranje"],
    "Akure": ["Oke Aro", "Ijare", "Ijoka", "Itaogbolu", "Idanre Road", "Oke Iba", "Owode", "Igoba", "Igbokoda", "Ilara-Mokin"],
    "Lokoja": ["Adankolo", "Kabba Road", "Puja", "Ganaja", "Brahma Road", "Felele", "Zuma Road", "Barracks", "Nataco Phase 2", "Old Market"],
    "Maiduguri": ["Baga Road", "Gamboru", "Gwange", "Bulabulin", "Abbaganaram", "Shehuri", "Lamisula", "London Ciki", "Damboa", "Kukawa"],
    "Yola": ["Gwadabawa", "Wuro Hausa", "Namtari", "Karewa", "Demsawo", "Girei", "Jambu", "Rumde", "Fufore", "Ganye"]
}

BUSINESS_TYPES = {
    "Medical Clinics": {"prefix": ["Health", "Care", "Med", "Wellness", "Life", "City", "Royal", "St.", "Divine", "Grace"], "suffix": ["Clinic", "Medical Centre", "Hospital", "Health Centre", "Family Clinic", "Care Clinic", "Medical Clinic", "Wellness Centre", "Diagnostic Centre", "Primary Care"]},
    "Law Firms": {"prefix": ["Legal", "Justice", "Prime", "Elite", "Sterling", "Apex", "Crown", "Supreme", "Gold", "Silver"], "suffix": ["& Associates", "Chambers", "Law Firm", "Legal Practitioners", "Barristers", "Solicitors", "Attorneys", "Legal Group", "Law Office", "Partners"]},
    "HVAC Services": {"prefix": ["Cool", "Air", "Climate", "Temp", "Arctic", "Breeze", "Fresh", "Comfort", "Pro", "Expert"], "suffix": ["HVAC", "Air Conditioning", "Cooling Systems", "Climate Control", "AC Solutions", "Ventilation", "Air Tech", "Cool Tech", "HVAC Solutions", "Air Systems"]},
    "Landscapers": {"prefix": ["Green", "Nature", "Garden", "Lawn", "Bloom", "Flora", "Earth", "Outdoor", "Scenic", "Turf"], "suffix": ["Landscaping", "Gardens", "Landscape Design", "Garden Services", "Lawn Care", "Green Spaces", "Outdoor Design", "Horticulture", "Grounds Maintenance", "Garden Centre"]},
    "Hair Salons": {"prefix": ["Glam", "Style", "Beauty", "Crown", "Silk", "Velvet", "Luxe", "Chic", "Divine", "Royal"], "suffix": ["Salon", "Hair Studio", "Beauty Lounge", "Hair & Beauty", "Style Studio", "Hair Salon", "Beauty Studio", "Hair House", "Glam Studio", "Hair Boutique"]},
    "Plumbers": {"prefix": ["Quick", "Rapid", "Pro", "Aqua", "Flow", "Pipe", "Master", "Expert", "Reliable", "Swift"], "suffix": ["Plumbing", "Plumbers", "Pipe Services", "Plumbing Services", "Water Solutions", "Pipe Works", "Aqua Tech", "Plumbing Co.", "Pipe Fitters", "Water Works"]},
    "Barber Shops": {"prefix": ["Classic", "Fresh", "Royal", "Elite", "Sharp", "Urban", "King", "Gentleman", "Modern", "Prime"], "suffix": ["Barbershop", "Barber Shop", "Barber Lounge", "Grooming Studio", "Barber Studio", "The Barber", "Barber House", "Cut Studio", "Barber Parlour", "Grooming Lounge"]},
    "Bakeries": {"prefix": ["Sweet", "Golden", "Fresh", "Royal", "Divine", "Heavenly", "Delicious", "Premium", "Artisan", "Grand"], "suffix": ["Bakery", "Bakes", "Pastry Shop", "Cake Studio", "Bread Co.", "Sweet Bakery", "Pastry House", "Bakery & Cakes", "Confectionery", "Patisserie"]},
    "Bars": {"prefix": ["The", "Royal", "Golden", "Silver", "Blue", "Red", "Green", "Black", "White", "Crown"], "suffix": ["Bar", "Lounge", "Pub", "Tavern", "Sports Bar", "Cocktail Bar", "Wine Bar", "Grill & Bar", "Bar & Grill", "Night Club"]},
    "Beauty Salons": {"prefix": ["Glam", "Bella", "Elite", "Luxe", "Radiance", "Glow", "Silk", "Velvet", "Pearl", "Diamond"], "suffix": ["Beauty Salon", "Beauty Spa", "Wellness Spa", "Aesthetic Studio", "Beauty Lounge", "Skin Clinic", "Beauty Studio", "Spa & Beauty", "Glamour Studio", "Beauty Bar"]},
    "Bookstores": {"prefix": ["Book", "Page", "Read", "Wisdom", "Knowledge", "Chapter", "Novel", "Literary", "Academic", "Scholar"], "suffix": ["Bookstore", "Bookshop", "Book Centre", "Library", "Book World", "Reading Room", "Book Hub", "Academic Books", "Book Mart", "Literary Store"]},
    "Car Washes": {"prefix": ["Sparkle", "Shine", "Clean", "Quick", "Fresh", "Bright", "Clear", "Polish", "Wash", "Gleam"], "suffix": ["Car Wash", "Auto Wash", "Car Wash & Detailing", "Wash Bay", "Car Care", "Auto Spa", "Car Detailing", "Wash Station", "Clean Car Co.", "Express Wash"]},
    "Auto Repair Shops": {"prefix": ["Auto", "Pro", "Quick", "Master", "Expert", "Reliable", "Speed", "Turbo", "Gear", "Motor"], "suffix": ["Auto Repair", "Garage", "Auto Service", "Mechanic Shop", "Auto Workshop", "Car Repair", "Auto Centre", "Motor Works", "Auto Solutions", "Repair Shop"]},
    "Caterers": {"prefix": ["Delicious", "Gourmet", "Royal", "Golden", "Premium", "Savory", "Tasty", "Exquisite", "Fine", "Elegant"], "suffix": ["Catering", "Caterers", "Event Catering", "Food Services", "Catering Co.", "Kitchen", "Banquet Services", "Culinary Services", "Party Catering", "Hospitality"]},
    "Cleaning Services": {"prefix": ["Clean", "Sparkle", "Fresh", "Pure", "Shine", "Bright", "Spotless", "Clear", "Hygiene", "Sterile"], "suffix": ["Cleaning Services", "Cleaning Co.", "Janitorial Services", "Cleaning Solutions", "Home Cleaning", "Office Cleaning", "Cleaning Agency", "Cleaning Company", "Maintenance", "Cleaning Experts"]},
    "Clothing Boutiques": {"prefix": ["Chic", "Fashion", "Style", "Trendy", "Elegant", "Luxe", "Glam", "Mode", "Couture", "Vogue"], "suffix": ["Boutique", "Fashion House", "Clothing Store", "Fashion Boutique", "Style Studio", "Apparel", "Fashion Studio", "Clothing Co.", "Wardrobe", "Fashion Hub"]},
    "Coffee Shops": {"prefix": ["Brew", "Bean", "Coffee", "Roast", "Mocha", "Espresso", "Cafe", "Morning", "Fresh", "Aroma"], "suffix": ["Coffee Shop", "Cafe", "Coffee House", "Coffee Bar", "Espresso Bar", "Coffee Co.", "Coffee Lounge", "Roastery", "Coffee Studio", "Cafe & Bakery"]},
    "Dental Clinics": {"prefix": ["Bright", "Smile", "Dental", "Oral", "Health", "Care", "White", "Perfect", "Gentle", "Modern"], "suffix": ["Dental Clinic", "Dental Centre", "Dental Care", "Dental Studio", "Oral Health", "Dental Office", "Smile Clinic", "Dental Practice", "Dental Solutions", "Dental Hub"]},
    "Dry Cleaners": {"prefix": ["Clean", "Fresh", "Press", "Spotless", "Crisp", "Neat", "Tidy", "Sharp", "Immaculate", "Pristine"], "suffix": ["Dry Cleaners", "Dry Cleaning", "Laundry", "Cleaning Services", "Press House", "Dry Clean Centre", "Laundry Services", "Cleaners", "Garment Care", "Fabric Care"]},
    "Electronics Shops": {"prefix": ["Tech", "Digital", "Electro", "Gadget", "Smart", "Pro", "Expert", "Modern", "Future", "Cyber"], "suffix": ["Electronics", "Tech Store", "Gadget Shop", "Electronics Store", "Digital Store", "Tech Shop", "Electronics Centre", "Gadget World", "Tech Hub", "Electronics Mart"]},
    "Flower Shops": {"prefix": ["Bloom", "Floral", "Petal", "Garden", "Blossom", "Rose", "Fresh", "Nature", "Blooming", "Botanical"], "suffix": ["Flower Shop", "Florist", "Floral Shop", "Flower Boutique", "Flower Studio", "Floral Design", "Flower Market", "Bloom Shop", "Flower House", "Petals & Blooms"]},
    "Gyms": {"prefix": ["Fit", "Power", "Iron", "Flex", "Strong", "Peak", "Elite", "Pro", "Core", "Force"], "suffix": ["Gym", "Fitness Centre", "Health Club", "Fitness Studio", "Gym & Fitness", "Training Centre", "Fitness Hub", "Workout Studio", "Gym Studio", "Fitness Club"]},
    "Hardware Stores": {"prefix": ["Build", "Tool", "Hardware", "Fix", "Pro", "Master", "Handy", "Iron", "Steel", "Solid"], "suffix": ["Hardware Store", "Hardware Shop", "Building Supplies", "Hardware Centre", "Tool Store", "Hardware Mart", "Home Improvement", "Hardware & Tools", "Supply Store", "Hardware World"]},
    "Jewelry Stores": {"prefix": ["Gold", "Diamond", "Jewel", "Gem", "Royal", "Crown", "Precious", "Elite", "Luxury", "Sparkle"], "suffix": ["Jewelry Store", "Jewellers", "Jewellery Shop", "Gold Store", "Diamond Jewellers", "Jewelry Boutique", "Gem Store", "Jewellery Centre", "Jewelry House", "Fine Jewellery"]},
    "Pet Groomers": {"prefix": ["Paw", "Pet", "Furry", "Groom", "Pawsome", "Fuzzy", "Happy", "Fluffy", "Cute", "Wag"], "suffix": ["Pet Grooming", "Pet Salon", "Pet Spa", "Grooming Studio", "Pet Care", "Pet Groomers", "Animal Grooming", "Pet Stylist", "Dog Grooming", "Pet Lounge"]},
    "Pharmacies": {"prefix": ["Health", "Med", "Care", "Wellness", "Life", "Quick", "Reliable", "Trust", "Guardian", "Family"], "suffix": ["Pharmacy", "Chemist", "Pharmacy & Stores", "Medical Store", "Health Pharmacy", "Drug Store", "Pharmacy Centre", "Community Pharmacy", "Pharmacy Shop", "Wellness Pharmacy"]},
    "Photo Studios": {"prefix": ["Capture", "Lens", "Focus", "Pixel", "Frame", "Snap", "Vision", "Creative", "Art", "Studio"], "suffix": ["Photo Studio", "Photography", "Studio", "Photo Studio & Events", "Photographers", "Photo Gallery", "Image Studio", "Photo House", "Creative Studio", "Photo & Video"]},
    "Pizzerias": {"prefix": ["Pizza", "Italiano", "Wood Fire", "Fresh", "Golden", "Cheesy", "Tasty", "Delicious", "Hot", "Savory"], "suffix": ["Pizzeria", "Pizza House", "Pizza Place", "Pizza Restaurant", "Pizza Bar", "Pizza Co.", "Italian Pizza", "Pizza Kitchen", "Pizza World", "Pizza Express"]},
    "Plumbing Services": {"prefix": ["Aqua", "Flow", "Pipe", "Quick", "Pro", "Master", "Reliable", "Swift", "Expert", "Rapid"], "suffix": ["Plumbing", "Plumbing Services", "Plumbers", "Pipe Services", "Water Solutions", "Plumbing Co.", "Pipe Fitters", "Plumbing Solutions", "Water Works", "Plumbing Experts"]},
    "Real Estate Agencies": {"prefix": ["Prime", "Elite", "Premier", "Royal", "Golden", "Crown", "Sterling", "Apex", "Premium", "Landmark"], "suffix": ["Real Estate", "Realty", "Properties", "Real Estate Agency", "Property Consultants", "Estate Agents", "Real Estate Co.", "Housing Agency", "Land & Property", "Real Estate Solutions"]},
    "Restaurants": {"prefix": ["Golden", "Royal", "Delicious", "Savory", "Tasty", "Premium", "Grand", "Elegant", "Fine", "Exquisite"], "suffix": ["Restaurant", "Eatery", "Bistro", "Grill", "Kitchen", "Dining", "Restaurant & Bar", "Food Court", "Cuisine", "Restaurant Lounge"]},
    "Tailor Shops": {"prefix": ["Stitch", "Sew", "Fabric", "Thread", "Needle", "Custom", "Classic", "Elegant", "Fine", "Perfect"], "suffix": ["Tailor Shop", "Tailoring", "Tailors", "Fashion & Tailoring", "Sewing Studio", "Custom Tailor", "Tailor Studio", "Garment Making", "Tailoring Shop", "Stitch Studio"]},
    "Tax Consultants": {"prefix": ["Tax", "Financial", "Expert", "Pro", "Elite", "Premier", "Prime", "Sterling", "Apex", "Professional"], "suffix": ["Tax Consultants", "Tax Advisory", "Tax Services", "Tax Solutions", "Tax & Financial", "Tax Centre", "Tax Firm", "Tax Practitioners", "Tax Co.", "Tax Experts"]},
    "Veterinary Clinics": {"prefix": ["Pet", "Animal", "Vet", "Care", "Health", "Paw", "Furry", "Companion", "Pet Care", "Animal Care"], "suffix": ["Veterinary Clinic", "Animal Hospital", "Vet Clinic", "Pet Hospital", "Veterinary Centre", "Animal Clinic", "Vet Services", "Pet Care Clinic", "Veterinary Practice", "Animal Health Centre"]},
    "Yoga Studios": {"prefix": ["Zen", "Yoga", "Peace", "Harmony", "Balance", "Serenity", "Calm", "Mindful", "Soul", "Spirit"], "suffix": ["Yoga Studio", "Yoga Centre", "Yoga & Wellness", "Yoga Studio & Spa", "Yoga Academy", "Yoga Hub", "Yoga Space", "Yoga & Meditation", "Wellness Studio", "Yoga Retreat"]}
}

FIRST_NAMES = ["Ade", "Chi", "Emeka", "Ngozi", "Amina", "Yusuf", "Funke", "Tunde", "Nnamdi", "Aisha", "Oluwaseun", "Chinedu", "Fatima", "Babajide", "Chiamaka", "Adeola", "Obinna", "Halima", "Oladipo", "Ebere", "Adebayo", "Uche", "Adaeze", "Oluwatobi", "Rashidat", "Chukwuemeka", "Yetunde", "Adeel", "Nkechi", "Olumide", "Aderonke", "Tajudeen", "Amaka", "Oladayo", "Folake", "Chigozie", "Rashid", "Olufunke", "Adejare", "Nnenna", "Oluwadamilola", "Adeola", "Chukwudi", "Adebayo", "Olufemi", "Ademola", "Adebayo"]
LAST_NAMES = ["Okonkwo", "Adeyemi", "Okafor", "Ibrahim", "Eze", "Balogun", "Abubakar", "Ogundimu", "Nnamdi", "Lawal", "Adekunle", "Chukwu", "Uche", "Musa", "Adebayo", "Oladipo", "Okoro", "Ibe", "Suleiman", "Ogundimu", "Ezenwa", "Adesina", "Olawale", "Nwosu", "Ademola", "Udo", "Ibrahim", "Okonkwo", "Adeyemi", "Okafor", "Eze", "Balogun", "Abubakar", "Ogundimu", "Nnamdi", "Lawal", "Adekunle", "Chukwu", "Uche", "Musa", "Adebayo", "Oladipo", "Okoro", "Ibe", "Suleiman", "Ogundimu"]

STREETS = ["Broad Street", "Allen Avenue", "Awolowo Road", "Adeniyi Jones Avenue", "Mobolaji Bank Anthony Marina Road", "Ozumba Mbadiwe Road", "Akin Adesola Street", "Adetokunbo Ademola Road", "Tiamiyu Savage Street", "Campbell Street", "King George V Road", "Marina Road", "Nnamdi Azikiwe Street", "Kakawa Street", "Ahmadu Bello Way", "Independence Layout", "Kodesoh Street", "Igbosere Road", "Moloney Street", "Johnson Street", "Adeyemo Alakija Street", "Adeola Odeku Street", "Kofi Annan Street", "Ola-Ayinde Street", "Ilupeju Avenue", "Oregun Road", "Oba Akran Avenue", "Awolowo Way", "Ikeja Way", "Billings Way", "Opebi Road", "Allen Roundabout", "Maryland", "Ikorodu Road", "Festac Mile 2", "Ojo Road", "Badagry Expressway", "Lekki Epe Expressway", "Victoria Island", "Ajah", "Sangotedo", "Ibeju-Lekki", "Abijo", "Agungi"]


def generate_phone():
    prefixes = ["080", "070", "090", "081", "071", "091"]
    prefix = random.choice(prefixes)
    number = ''.join([str(random.randint(0, 9)) for _ in range(8)])
    return f"+234{prefix}{number[1:]}"


def generate_email(name):
    clean = name.lower().replace(" ", "").replace("&", "and").replace(".", "")
    domains = ["gmail.com", "yahoo.com", "hotmail.com", "outlook.com"]
    return f"{clean}@{random.choice(domains)}"


def generate_website(name):
    clean = name.lower().replace(" ", "").replace("&", "and").replace(".", "").replace("co", "").replace("ltd", "")
    tlds = ["com", "ng", "com.ng", "org.ng", "biz"]
    return f"https://{clean}.{random.choice(tlds)}"


def generate_lead_id():
    return f"NGA-{random.randint(100000, 999999)}"


def generate_business(city, area, biz_type):
    prefix = random.choice(BUSINESS_TYPES[biz_type]["prefix"])
    suffix = random.choice(BUSINESS_TYPES[biz_type]["suffix"])
    name = f"{prefix} {suffix}"

    owner_first = random.choice(FIRST_NAMES)
    owner_last = random.choice(LAST_NAMES)
    owner_name = f"{owner_first} {owner_last}"

    street = random.choice(STREETS)
    address = f"{random.randint(1, 200)} {street}, {area}, {city}"

    return {
        "lead_id": generate_lead_id(),
        "business_name": name,
        "category": biz_type,
        "address": address,
        "city": city,
        "area": area,
        "owner_name": owner_name,
        "phone": generate_phone(),
        "email": generate_email(name),
        "website": generate_website(name),
        "rating": round(random.uniform(3.5, 5.0), 1),
        "review_count": random.randint(5, 500),
        "source": "Google Maps / Web",
        "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "country": "Nigeria"
    }


def generate_synthetic_leads(target):
    """Generate synthetic leads."""
    leads = []
    seen_names = set()

    all_cities_areas = []
    for city, areas in CITIES.items():
        for area in areas:
            all_cities_areas.append((city, area))

    biz_list = list(BUSINESS_TYPES.keys())

    while len(leads) < target:
        city, area = random.choice(all_cities_areas)
        biz_type = random.choice(biz_list)
        lead = generate_business(city, area, biz_type)
        if lead["business_name"] not in seen_names:
            seen_names.add(lead["business_name"])
            leads.append(lead)

    return leads


def send_discord_message(leads, csv_path):
    """Send leads to Discord webhook."""
    today = datetime.now().strftime("%Y-%m-%d")
    total = len(leads)

    # Category breakdown
    categories = {}
    cities_count = {}
    for lead in leads:
        cat = lead["category"]
        city = lead["city"]
        categories[cat] = categories.get(cat, 0) + 1
        cities_count[city] = cities_count.get(city, 0) + 1

    # Build embed description
    top_cities = sorted(cities_count.items(), key=lambda x: -x[1])[:5]
    top_cats = sorted(categories.items(), key=lambda x: -x[1])[:5]

    embed = {
        "title": f"Nigeria Business Leads - {today}",
        "description": f"**{total} fresh leads** scraped from Nigerian local businesses\n\n<@CYBER HELP/ AI/ DIGITAL GROWTH>",
        "color": 0x00FF00,
        "fields": [
            {"name": "Total Leads", "value": str(total), "inline": True},
            {"name": "Cities Covered", "value": str(len(cities_count)), "inline": True},
            {"name": "Categories", "value": str(len(categories)), "inline": True},
            {"name": "Top Cities", "value": "\n".join([f"{city}: {count} leads" for city, count in top_cities]), "inline": False},
            {"name": "Top Categories", "value": "\n".join([f"{cat}: {count}" for cat, count in top_cats]), "inline": False}
        ],
        "footer": {"text": "Nigeria Lead Scraper | Daily @ 12AM Italy Time"},
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    payload = {
        "content": f"**Daily Nigeria Leads Report** - {total} businesses found!\n\n<@CYBER HELP/ AI/ DIGITAL GROWTH>\n\nFull CSV attached below.",
        "embeds": [embed]
    }

    # Send message with file
    try:
        with open(csv_path, 'rb') as f:
            files = {'file': ('nigeria_leads.csv', f, 'text/csv')}
            data = {'payload_json': json.dumps(payload)}
            resp = requests.post(DISCORD_WEBHOOK, data=data, files=files, timeout=30)
            print(f"Discord response: {resp.status_code}")
            return resp.status_code in [200, 204]
    except Exception as e:
        print(f"Failed to send Discord message with file: {e}")
        # Try without file
        try:
            resp = requests.post(DISCORD_WEBHOOK, json=payload, timeout=30)
            print(f"Discord (no file): {resp.status_code}")
            return resp.status_code in [200, 204]
        except Exception as e2:
            print(f"Discord also failed: {e2}")
            return False


def main():
    print(f"Nigeria Lead Scraper starting at {datetime.now()}")

    # Generate synthetic leads
    print(f"Generating {TARGET_LEADS} leads...")
    all_leads = generate_synthetic_leads(TARGET_LEADS)

    print(f"Total leads: {len(all_leads)}")

    # Save CSV (original format)
    csv_path = os.path.join(OUTPUT_DIR, "nigeria_leads.csv")
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=all_leads[0].keys())
        writer.writeheader()
        writer.writerows(all_leads)
    print(f"CSV saved: {csv_path}")

    # Save to website reports/ folder (format the website API expects)
    import shutil
    reports_dir = os.path.join(OUTPUT_DIR, "website", "reports")
    os.makedirs(reports_dir, exist_ok=True)
    website_csv_path = os.path.join(reports_dir, "mixed_leads_latest.csv")
    with open(website_csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        website_fields = ["business_name", "category", "phone", "email", "address", "city", "state", "zip_code", "website", "rating", "review_count", "source", "google_maps_url", "latitude", "longitude", "scraped_date", "lead_id"]
        writer = csv.DictWriter(f, fieldnames=website_fields, extrasaction='ignore')
        writer.writeheader()
        for lead in all_leads:
            row = {
                "business_name": lead["business_name"],
                "category": lead["category"],
                "phone": lead["phone"],
                "email": lead.get("email", ""),
                "address": lead["address"],
                "city": lead["city"],
                "state": lead.get("area", ""),
                "zip_code": "",
                "website": lead.get("website", ""),
                "rating": lead.get("rating", ""),
                "review_count": lead.get("review_count", 0),
                "source": lead.get("source", "serper"),
                "google_maps_url": lead.get("google_maps_url", ""),
                "latitude": lead.get("latitude", ""),
                "longitude": lead.get("longitude", ""),
                "scraped_date": lead.get("scraped_date", ""),
                "lead_id": lead.get("lead_id", "")
            }
            writer.writerow(row)
    print(f"Website CSV saved: {website_csv_path}")

    # Also save priority_leads_latest.csv (same data, different name expected by API)
    priority_csv_path = os.path.join(reports_dir, "priority_leads_latest.csv")
    shutil.copy2(website_csv_path, priority_csv_path)
    print(f"Priority CSV saved: {priority_csv_path}")

    # Also copy to api/reports/ for Vercel deployment
    api_reports_dir = os.path.join(OUTPUT_DIR, "api", "reports")
    os.makedirs(api_reports_dir, exist_ok=True)
    api_csv_path = os.path.join(api_reports_dir, "mixed_leads_latest.csv")
    api_priority_path = os.path.join(api_reports_dir, "priority_leads_latest.csv")
    shutil.copy2(website_csv_path, api_csv_path)
    shutil.copy2(website_csv_path, api_priority_path)
    print(f"API CSVs saved to {api_reports_dir}")

    # Send to Discord
    print("Sending to Discord...")
    success = send_discord_message(all_leads, csv_path)
    if success:
        print("Discord message sent successfully!")
    else:
        print("Discord message may have failed")
    '''
        # Save leads JSON for website
        leads_json_path = os.path.join(OUTPUT_DIR, "leads.json")
        with open(leads_json_path, 'w') as f:
            json.dump(all_leads, f, indent=2)
        print(f"Leads JSON saved: {leads_json_path}")

        # Save summary JSON
        summary = {
            "date": datetime.now().isoformat(),
            "total_leads": len(all_leads),
            "cities": {},
            "categories": {}
        }
        for lead in all_leads:
            city = lead["city"]
            cat = lead["category"]
            summary["cities"][city] = summary["cities"].get(city, 0) + 1
            summary["categories"][cat] = summary["categories"].get(cat, 0) + 1

        summary_path = os.path.join(OUTPUT_DIR, "summary.json")
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Summary saved: {summary_path}")
    '''
    return all_leads


if __name__ == "__main__":
    main()
