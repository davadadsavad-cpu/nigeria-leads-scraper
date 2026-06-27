// Vercel Serverless Function - serves leads from embedded data
// Since Vercel Python doesn't reliably copy CSV files, we use Node.js with
// leads data loaded client-side from a generated JSON file

import fs from 'fs';
import path from 'path';

export const config = {
    maxDuration: 10,
};

export default function handler(req, res) {
    const url = new URL(req.url, `https://${req.headers.host}`);
    const pathname = url.pathname;
    
    // Handle CORS
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }
    
    // Try to load leads.json
    let leads = [];
    let feedbacks = [];
    
    try {
        // Try multiple paths
        const possibleLeadsPaths = [
            path.join(process.cwd(), 'api', 'reports', 'mixed_leads_latest.csv'),
            path.join(process.cwd(), 'reports', 'mixed_leads_latest.csv'),
            path.join(process.cwd(), 'website', 'reports', 'mixed_leads_latest.csv'),
            '/var/task/api/reports/mixed_leads_latest.csv',
            '/var/task/reports/mixed_leads_latest.csv',
        ];
        
        for (const p of possibleLeadsPaths) {
            if (fs.existsSync(p)) {
                const csv = fs.readFileSync(p, 'utf-8-sig');
                leads = parseCSV(csv);
                break;
            }
        }
    } catch (e) {
        console.error('Error loading leads:', e);
    }
    
    try {
        const fbPaths = [
            path.join(process.cwd(), 'feedbacks.json'),
            path.join(process.cwd(), 'api', 'feedbacks.json'),
            '/var/task/feedbacks.json',
        ];
        for (const p of fbPaths) {
            if (fs.existsSync(p)) {
                feedbacks = JSON.parse(fs.readFileSync(p, 'utf-8'));
                break;
            }
        }
    } catch (e) {
        console.error('Error loading feedbacks:', e);
    }
    
    // Search
    const search = url.searchParams.get('search') || '';
    if (search) {
        const s = search.toLowerCase();
        leads = leads.filter(l => 
            (l.name && l.name.toLowerCase().includes(s)) ||
            (l.phone && l.phone.toLowerCase().includes(s)) ||
            (l.city && l.city.toLowerCase().includes(s)) ||
            (l.category && l.category.toLowerCase().includes(s))
        );
    }
    
    const pathname_clean = pathname.replace('/api/', '');
    
    if (pathname_clean === 'leads' || pathname === '/api/leads') {
        const cities = new Set(leads.map(l => l.city).filter(Boolean));
        const categories = new Set(leads.map(l => l.category).filter(Boolean));
        res.status(200).json({ leads, summary: { total: leads.length, cities: cities.size, categories: categories.size } });
    } else if (pathname_clean === 'feedbacks' || pathname === '/api/feedbacks') {
        res.status(200).json({ feedbacks });
    } else if (pathname_clean === 'stats' || pathname === '/api/stats') {
        const cities = new Set(leads.map(l => l.city).filter(Boolean));
        const categories = new Set(leads.map(l => l.category).filter(Boolean));
        res.status(200).json({
            total_leads: leads.length,
            cities_count: cities.size,
            categories_count: categories.size,
            feedback_count: feedbacks.length
        });
    } else {
        res.status(404).json({ error: 'Not found' });
    }
}

function parseCSV(csvText) {
    const lines = csvText.trim().split('\n');
    if (lines.length < 2) return [];
    
    const headers = parseCSVLine(lines[0]);
    const results = [];
    
    for (let i = 1; i < lines.length; i++) {
        const values = parseCSVLine(lines[i]);
        const obj = {};
        headers.forEach((h, idx) => {
            obj[h.trim()] = values[idx] || '';
        });
        
        // Map to our frontend format
        results.push({
            id: obj.lead_id || obj.business_name,
            name: obj.business_name || obj.name || 'Unknown',
            phone: obj.phone || '',
            email: obj.email || '',
            address: obj.address || '',
            city: obj.city || '',
            state: obj.state || '',
            website: obj.website || '',
            rating: obj.rating || '',
            category: obj.category || '',
            source: obj.source || 'serper'
        });
    }
    
    return results;
}

function parseCSVLine(line) {
    const result = [];
    let current = '';
    let inQuotes = false;
    
    for (let i = 0; i < line.length; i++) {
        const char = line[i];
        if (char === '"') {
            if (inQuotes && line[i + 1] === '"') {
                current += '"';
                i++;
            } else {
                inQuotes = !inQuotes;
            }
        } else if (char === ',' && !inQuotes) {
            result.push(current);
            current = '';
        } else {
            current += char;
        }
    }
    result.push(current);
    return result;
}
