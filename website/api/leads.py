import json
import csv
import os

def handler(request):
    # Read leads from CSV and convert to JSON
    leads_path = os.path.join(os.path.dirname(__file__), '..', 'leads.json')
    
    if os.path.exists(leads_path):
        with open(leads_path, 'r') as f:
            leads = json.load(f)
    else:
        # Try CSV as fallback
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'nigeria_leads.csv')
        if os.path.exists(csv_path):
            leads = []
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    leads.append(dict(row))
        else:
            leads = []
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({'leads': leads, 'total': len(leads)})
    }
