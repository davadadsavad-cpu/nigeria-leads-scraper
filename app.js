const API_BASE = window.location.origin + "/api";
let leads = [];
let feedbacks = [];
let selectedRating = 0;
let selectedLeads = new Set();

// Load all data on startup
async function loadData() {
    try {
        const [leadsRes, feedbacksRes, statsRes] = await Promise.all([
            fetch("/leads-data.json"),
            fetch("/api/feedbacks"),
            fetch("/api/stats")
        ]);
        leads = await leadsRes.json();
        feedbacks = await feedbacksRes.json();
        const stats = await statsRes.json();

        // Update stats
        document.getElementById("total-leads").textContent = stats.total_leads;
        document.getElementById("cities-count").textContent = stats.cities_count;
        document.getElementById("categories-count").textContent = stats.categories_count;

        // Populate selects
        const cities = [...new Set(leads.map(l => l.city).filter(c => c))].sort();
        const categories = [...new Set(leads.map(l => l.category).filter(c => c))].sort();
        const citySelect = document.getElementById("filter-city");
        const catSelect = document.getElementById("filter-category");
        citySelect.innerHTML = '<option value="all">All Cities</option>' +
            cities.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
        catSelect.innerHTML = '<option value="all">All Categories</option>' +
            categories.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");

        // Populate lead select dropdown
        const leadSelect = document.getElementById("lead-select");
        leadSelect.innerHTML = '<option value="">-- Choose a lead --</option>' +
            leads.slice(0, 100).map(l =>
                `<option value="${escapeHtml(l.id)}">${escapeHtml(l.name)} - ${escapeHtml(l.phone || l.city)}</option>`).join("");

        renderLeads();
        renderFeedbacks();
    } catch (e) {
        console.log("API not available (using localStorage):", e);
        loadFeedbacks();
        renderFeedbacks();
    }
}

function renderLeads() {
    const list = document.getElementById("leads-list");
    const search = document.getElementById("search").value.toLowerCase();
    const filterCity = document.getElementById("filter-city").value;
    const filterCategory = document.getElementById("filter-category").value;

    let filtered = leads.filter(l => {
        const match = !search || (
            (l.name && l.name.toLowerCase().includes(search)) ||
            (l.phone && l.phone.toLowerCase().includes(search)) ||
            (l.city && l.city.toLowerCase().includes(search))
        );
        const matchCity = filterCity === "all" || l.city === filterCity;
        const matchCat = filterCategory === "all" || l.category === filterCategory;
        return match && matchCity && matchCat;
    });

    if (filtered.length === 0) {
        list.innerHTML = '<div class="empty-state">No leads found</div>';
        return;
    }

    list.innerHTML = filtered.map(lead => {
        const checked = selectedLeads.has(lead.id) ? "checked" : "";
        return `
            <div class="feedback-card">
                <div class="card-header">
                    <div>
                        <input type="checkbox" data-id="${lead.id}" class="lead-check" ${checked}>
                        <h3>${escapeHtml(lead.name || "Unknown")}</h3>
                        <span class="company-name">${escapeHtml(lead.category || "business")}</span>
                    </div>
                    <div class="card-rating">${lead.phone ? "📞" : "⭐"} ${escapeHtml(lead.phone || lead.rating)}</div>
                </div>
                <div class="card-footer">
                    <span>${escapeHtml(lead.city || "")}, ${escapeHtml(lead.state || "")}</span>
                    <span>${lead.website ? `<a href="${escapeHtml(lead.website)}" target="_blank">🌐</a>` : ""}</span>
                </div>
            </div>
        `;
    }).join("");

    // Add checkbox listeners
    document.querySelectorAll(".lead-check").forEach(cb => {
        cb.addEventListener("change", (e) => {
            if (e.target.checked) {
                selectedLeads.add(e.target.dataset.id);
            } else {
                selectedLeads.delete(e.target.dataset.id);
            }
        });
    });
}

document.getElementById("select-all").addEventListener("change", (e) => {
    if (e.target.checked) {
        leads.forEach(l => selectedLeads.add(l.id));
    } else {
        selectedLeads.clear();
    }
    renderLeads();
});

document.getElementById("export-all").addEventListener("click", () => {
    if (!leads || leads.length === 0) { alert("No leads to export"); return; }
    const csv = "Name,Phone,Category,City,State,Website,Rating\n" +
        leads.map(l => `"${escapeCsv(l.name)}","${escapeCsv(l.phone)}","${escapeCsv(l.category)}","${escapeCsv(l.city)}","${escapeCsv(l.state)}","${escapeCsv(l.website)}","${escapeCsv(l.rating)}"`).join("\n");
    downloadCSV(csv, "all_leads.csv");
});

document.getElementById("export-selected").addEventListener("click", () => {
    const selected = leads.filter(l => selectedLeads.has(l.id));
    if (selected.length === 0) { alert("No leads selected"); return; }
    const csv = "Name,Phone,Category,City,State,Website,Rating\n" +
        selected.map(l => `"${escapeCsv(l.name)}","${escapeCsv(l.phone)}","${escapeCsv(l.category)}","${escapeCsv(l.city)}","${escapeCsv(l.state)}","${escapeCsv(l.website)}","${escapeCsv(l.rating)}"`).join("\n");
    downloadCSV(csv, "selected_leads.csv");
});

function downloadCSV(csv, filename) {
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
}

function escapeCsv(str) {
    return (str || "").replace(/"/g, '""');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

document.getElementById("search").addEventListener("input", renderLeads);
document.getElementById("filter-city").addEventListener("change", renderLeads);
document.getElementById("filter-category").addEventListener("change", renderLeads);

document.addEventListener('DOMContentLoaded', loadData);

// Feedback form handler
document.getElementById('feedback-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const lead_id = document.getElementById('lead-select').value;
    const name = document.getElementById('feedback-name').value.trim() || "User";
    const text = document.getElementById('feedback-text').value.trim();
    const status = document.getElementById('status').value;
    const rating = parseInt(document.getElementById('rating').value);

    if (!text || rating === 0) return;

    try {
        await fetch(API_BASE + "/feedbacks", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({name, company: "Feedback", text, status, rating, lead_id})
        });
    } catch (err) {
        feedbacks.unshift({name, company: "Feedback", text, status, rating, date: new Date().toISOString()});
        localStorage.setItem('lead-feedback', JSON.stringify(feedbacks));
    }

    document.getElementById('feedback-form').reset();
    document.getElementById('rating').value = '0';
    document.getElementById('feedback-name').value = '';
    selectedRating = 0;
    document.querySelectorAll('.star').forEach(s => s.classList.remove('active'));
    loadData();
});

// Star rating
document.querySelectorAll('.star').forEach(star => {
    star.addEventListener('click', () => {
        selectedRating = parseInt(star.dataset.value);
        document.getElementById('rating').value = selectedRating;
        document.querySelectorAll('.star').forEach(s =>
            s.classList.toggle('active', parseInt(s.dataset.value) <= selectedRating));
    });
});

// Fallback localStorage functions
function loadFeedbacks() {
    const data = localStorage.getItem('lead-feedback');
    if (data) {
        feedbacks = JSON.parse(data);
    }
}

function renderFeedbacks() {
    const list = document.getElementById('feedback-list');
    const search = document.getElementById('search-feedback').value.toLowerCase();
    const filterStatus = document.getElementById('filter-feedback-status').value;

    const filtered = feedbacks.filter(f => {
        const matchSearch = f.name.toLowerCase().includes(search) ||
            (f.company && f.company.toLowerCase().includes(search));
        const matchStatus = filterStatus === 'all' || f.status === filterStatus;
        return matchSearch && matchStatus;
    });

    if (filtered.length === 0) {
        list.innerHTML = '<div class="empty-state">No feedback found</div>';
        return;
    }

    list.innerHTML = filtered.map((f, i) => {
        const idx = feedbacks.indexOf(f);
        const stars = '★'.repeat(f.rating) + '☆'.repeat(5 - f.rating);
        const date = new Date(f.date).toLocaleDateString('en-US', {
            month: 'short', day: 'numeric', year: 'numeric'
        });
        return `
            <div class="feedback-card">
                <div class="card-header">
                    <div>
                        <h3>${escapeHtml(f.name)}</h3>
                        ${f.company ? `<span class="company-name">${escapeHtml(f.company)}</span>` : ''}
                    </div>
                    <div class="card-rating">${stars}</div>
                </div>
                <div class="card-feedback">${escapeHtml(f.text)}</div>
                <div class="card-footer">
                    <span class="status-badge ${f.status}">${f.status}</span>
                    <span class="card-date">${date}</span>
                    <button class="delete-btn" data-index="${idx}" title="Delete">&times;</button>
                </div>
            </div>
        `;
    }).join('');

    document.querySelectorAll('.delete-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.index);
            feedbacks.splice(idx, 1);
            localStorage.setItem('lead-feedback', JSON.stringify(feedbacks));
            renderFeedbacks();
        });
    });
}

document.getElementById('search-feedback')?.addEventListener('input', renderFeedbacks);
document.getElementById('filter-feedback-status')?.addEventListener('change', renderFeedbacks);