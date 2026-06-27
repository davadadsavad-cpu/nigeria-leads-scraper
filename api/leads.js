import fs from 'fs';
import path from 'path';

export const config = {
    maxDuration: 30,
};

export default function handler(req, res) {
    const url = new URL(req.url, `https://${req.headers.host}`);
    const pathname = url.pathname;
    
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    
    if (req.method === 'OPTIONS') {
        res.status(200).end();
        return;
    }
    
    // Parse CSV
    function parseCSV(csvText) {
        const lines = csvText.trim().split(/\r?\n/);
        if (lines.length < 2) return [];
        const headers = parseCSVLine(lines[0]);
        const results = [];
        for (let i = 1; i < lines.length; i++) {
            if (!lines[i].trim()) continue;
            const values = parseCSVLine(lines[i]);
            const obj = {};
            headers.forEach((h, idx) => { obj[h.trim()] = values[idx] || ''; });
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
                if (inQuotes && line[i+1] === '"') { current += '"'; i++; }
                else { inQuotes = !inQuotes; }
            } else if (char === ',' && !inQuotes) { result.push(current); current = ''; }
            else { current += char; }
        }
        result.push(current);
        return result;
    }
    
    // Debug endpoint
    if (pathname === '/api/files') {
        const info = {};
        info.cwd = process.cwd();
        try { info.haveReports = fs.existsSync('/var/task/api/reports/mixed_leads_latest.csv'); } catch(e) {}
        try {
            const content = fs.readFileSync('/var/task/api/reports/mixed_leads_latest.csv', 'utf-8-sig');
            info.lineCount = content.split('\n').length;
            info.firstLine = content.split('\n')[0];
        } catch(e) { info.err = e.message; }
        res.status(200).json(info);
        return;
    }
    
    // Load leads
    let leads = [];
    let loadedFrom = '';
    const csvPath = '/var/task/api/reports/mixed_leads_latest.csv';
    
    if (fs.existsSync(csvPath)) {
        try {
            const csv = fs.readFileSync(csvPath, 'utf-8-sig');
            leads = parseCSV(csv);
            loadedFrom = csvPath;
        } catch(e) {
            console.error('Error loading CSV:', e);
        }
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
    
    const cleanPath = pathname.replace('/api/', '');
    
    if (cleanPath === 'leads') {
        const cities = [...new Set(leads.map(l => l.city).filter(Boolean))];
        const categories = [...new Set(leads.map(l => l.category).filter(Boolean))];
        res.status(200).json({ leads, total: leads.length, cities: cities.length, categories: categories.length, _src: loadedFrom });
    } else if (cleanPath === 'stats') {
        const cities = [...new Set(leads.map(l => l.city).filter(Boolean))];
        const categories = [...new Set(leads.map(l => l.category).filter(Boolean))];
        res.status(200).json({
            total_leads: leads.length,
            cities_count: cities.length,
            categories_count: categories.length,
            feedback_count: 0,
            _src: loadedFrom
        });
    } else {
        res.status(404).json({ error: 'Not found' });
    }
}
