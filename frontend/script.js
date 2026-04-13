// API Base URL
const API_BASE = 'http://localhost:5000/api';

let currentUser = null;

// Map any item to its base crop, then fetch
const BASE_CROPS = [
  "tomato","lettuce","carrot","spinach","pepper","potato","onion","rice","wheat","maize",
  "cucumber","eggplant","cabbage","broccoli","garlic","strawberry","melon","pumpkin","zucchini","beans",
  "apple","almond","apricot","asparagus","avocado","banana","barley","basil","beetroot","blackberry",
  "blueberry","cacao","cassava","cauliflower","celery","cherry","chickpea","chili","chives","cilantro",
  "coconut","coffee","cranberry","date","dill","fig","flax","ginger","grape","grapefruit",
  "guava","hazelnut","hemp","kale","kiwi","leek","lemon","lentil","lime","macadamia",
  "mango","mint","mustard","oats","olive","orange","oregano","papaya","parsley","parsnip",
  "pea","peach","peanut","pear","pecan","pineapple","pistachio","plum","pomegranate","quinoa",
  "radish","raspberry","rosemary","rye","saffron","sage","sesame","sorghum","soy","sunflower",
  "sweetcorn","taro","thyme","turnip","vanilla","walnut","watermelon","yam"
];

function getBaseCrop(varietyName) {
  return BASE_CROPS.find(crop => varietyName.toLowerCase().includes(crop)) || varietyName.toLowerCase().split(' ').pop();
}

async function getCropImage(varietyName) {
  const crop = getBaseCrop(varietyName);
  try {
      const res = await fetch(`https://api.unsplash.com/search/photos?query=${crop}&per_page=1`, {
        headers: { Authorization: "Client-ID 2gPE3XR7RqCCgAfSpJX5YnEVWjZgkx763Bq0TxT0OJ0" }
      });
      const data = await res.json();
      return data.results[0]?.urls?.regular || 'https://images.unsplash.com/photo-1592424001809-54898de5d275?auto=format&fit=crop&w=600&q=80';
  } catch (e) {
      return 'https://images.unsplash.com/photo-1592424001809-54898de5d275?auto=format&fit=crop&w=600&q=80';
  }
}

// ── Auth helpers ─────────────────────────────────────────────────────────────

function getToken() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return user.token || '';
}

function authHeaders() {
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    return {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${user.token || ''}`,
        'X-Session-ID': user.session_id || ''
    };
}

// Wrapper that adds auth headers and handles 401 by redirecting to login
async function apiFetch(url, options = {}) {
    const res = await fetch(url, {
        ...options,
        headers: { ...authHeaders(), ...(options.headers || {}) }
    });
    if (res.status === 401) {
        localStorage.removeItem('user');
        window.location.href = 'index.html';
        return null;
    }
    return res;
}

// ── Language Toggle System ───────────────────────────────────────────────────

function toggleLanguage() {
    const isHindi = document.body.classList.toggle('hindi-mode');
    localStorage.setItem('language', isHindi ? 'hi' : 'en');
}

// Auto-apply language on load
document.addEventListener('DOMContentLoaded', () => {
    if (localStorage.getItem('language') === 'hi') {
        document.body.classList.add('hindi-mode');
    }
});

// ── Bootstrap ─────────────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    if (document.getElementById('loginForm')) {
        initializeAuth();
    } else if (document.querySelector('.dashboard')) {
        initializeDashboard();
    }
});

// ── Authentication (Login & Register) ─────────────────────────────────────────

function toggleAuth(mode) {
    const loginContainer = document.getElementById('loginContainer');
    const registerContainer = document.getElementById('registerContainer');
    if (mode === 'register') {
        loginContainer.style.display = 'none';
        registerContainer.style.display = 'block';
    } else {
        registerContainer.style.display = 'none';
        loginContainer.style.display = 'block';
    }
}

function initializeAuth() {
    // Login Submission
    const loginForm = document.getElementById('loginForm');
    if(loginForm) {
        loginForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const username = document.getElementById('username').value.trim();
            const password = document.getElementById('password').value;

            try {
                const res = await fetch(`${API_BASE}/login`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                const data = await res.json();

                if (data.success) {
                    // data includes token, user_id, username, and session_id
                    localStorage.setItem('user', JSON.stringify(data));
                    window.location.href = 'dashboard.html';
                } else {
                    showMessage('loginMessage', data.message, 'error');
                }
            } catch (err) {
                showMessage('loginMessage', 'Login failed. Please try again.', 'error');
                console.error('Login error:', err);
            }
        });
    }

    // Register Submission
    const registerForm = document.getElementById('registerForm');
    if(registerForm) {
        registerForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const name = document.getElementById('regName').value.trim();
            const username = document.getElementById('regUsername').value.trim();
            const password = document.getElementById('regPassword').value;
            const farmSize = document.getElementById('regFarmSize').value.trim();

            try {
                const res = await fetch(`${API_BASE}/register`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, username, password, farm_size: farmSize })
                });
                const data = await res.json();

                if (data.success) {
                    showMessage('registerMessage', 'Account created successfully! You can now login.', 'success');
                    setTimeout(() => toggleAuth('login'), 2000);
                } else {
                    showMessage('registerMessage', data.message || 'Registration failed.', 'error');
                }
            } catch (err) {
                showMessage('registerMessage', 'Registration failed. Please try again.', 'error');
                console.error('Register error:', err);
            }
        });
    }
}

// ── Dashboard ─────────────────────────────────────────────────────────────────

function initializeDashboard() {
    const stored = localStorage.getItem('user');
    if (!stored) {
        window.location.href = 'index.html';
        return;
    }
    currentUser = JSON.parse(stored);
    initializeForms();
    loadDashboardData();
    showSection('dashboard');
    
    // Start Irrigation management polling
    initIrrigationDashboard();
}

function initializeForms() {
    const bindings = [
        ['cropForm',       handleCropPlanning],
        ['cropInfoForm',   handleCropInfoSearch],
        ['soilForm',       handleSoilAnalysis],
        ['diseaseForm',    handleDiseaseDetection],
        ['financeForm',    handleFinanceCalculation],
        ['irrigationForm', handleIrrigationSchedule],
    ];
    bindings.forEach(([id, handler]) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('submit', handler);
    });

    const advisoryInput = document.getElementById('advisoryQuery');
    if (advisoryInput) {
        advisoryInput.addEventListener('keypress', function (e) {
            if (e.key === 'Enter') sendAdvisoryQuery();
        });
    }

    // Populate dynamic crop search dropdown
    const cropSearchDropdown = document.getElementById('cropInfoSearch');
    if (cropSearchDropdown) {
        // Sort alphabetically to look nice
        const sortedCrops = [...BASE_CROPS].sort((a,b) => a.localeCompare(b));
        sortedCrops.forEach(cropName => {
            const prettyName = cropName.charAt(0).toUpperCase() + cropName.slice(1);
            const opt = document.createElement('option');
            opt.value = cropName;
            opt.textContent = prettyName;
            cropSearchDropdown.appendChild(opt);
        });
    }
}

async function loadDashboardData() {
    loadUserProfile();
    loadPastConversations();
}

// ── User profile & recent conversations (dashboard overview) ────────────────

function loadUserProfile() {
    const el = document.getElementById('user-profile');
    if (!el) return;
    
    // currentUser is set during login
    const username = currentUser.username || 'Farmer';
    
    el.innerHTML = `
        <div class="profile-info" style="line-height: 1.6;">
            <p><strong>Username:</strong> ${username}</p>
            <p><strong>Status:</strong> <span style="color: #2d5a27; font-weight: bold;">Online 🟢</span></p>
            <p><strong>Session Active:</strong> Yes</p>
        </div>
    `;
}

const ACTIVITY_ICONS = {
    crop_recommendation: '🌾',
    soil_health:         '🌱',
    disease_detection:   '🦠',
    finance:             '💰',
    irrigation:          '💧',
    weather:             '🌤️',
    advisory:            '🤖',
    crop_info:           '📚',
};

async function loadActivityLog() {
    const el = document.getElementById('recent-conversations');
    if (!el) return;

    try {
        const res = await apiFetch(`${API_BASE}/activity-log?limit=10`);
        if (!res || !res.ok) {
            el.innerHTML = '<p style="color:#888">No activity recorded yet.</p>';
            return;
        }
        const sessions = await res.json();
        
        if (!sessions || sessions.length === 0) {
            el.innerHTML = '<p style="color:#888">No activity recorded yet. Start using the tools above!</p>';
            return;
        }

        el.innerHTML = `
            <div style="max-height:400px; overflow-y:auto; padding-right:4px">
                ${sessions.map((sess, idx) => {
                    const dt = new Date(sess.login_time).toLocaleString();
                    const isOpen = idx === 0; // Open first session by default
                    const activities = sess.activities || [];
                    
                    return `
                    <div class="session-group" style="margin-bottom: 12px; border: 1px solid #e9ecef; border-radius: 8px; overflow: hidden;">
                        <div onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none';" 
                             style="background: #f8f9fa; padding: 12px; cursor: pointer; display: flex; justify-content: space-between; align-items: center; border-bottom: ${isOpen ? '1px solid #e9ecef' : 'none'}">
                            <div style="display:flex; align-items:center; gap:10px;">
                                <span style="font-size:1.2rem;">🔑</span>
                                <div>
                                    <span style="font-weight:600; color:#2d5a27;">Login Activity</span>
                                    <div style="font-size:0.75rem; color:#999;">${dt}</div>
                                </div>
                            </div>
                            <span style="font-size:0.8rem; color:#666;">${activities.length} actions ▾</span>
                        </div>
                        <div style="display: ${isOpen ? 'block' : 'none'}; padding: 0 12px 12px;">
                            ${activities.length === 0 ? '<p style="margin-top:10px; font-size:0.85rem; color:#999; text-align:center;">No tool activities in this session.</p>' : 
                                activities.map(entry => {
                                    const icon  = ACTIVITY_ICONS[entry.activity_type] || '📋';
                                    const label = entry.activity_type.replace(/_/g,' ').replace(/\b\w/g, c => c.toUpperCase());
                                    const entryDt = new Date(entry.created_at).toLocaleTimeString();
                                    return `
                                    <div style="display:flex; align-items:flex-start; gap:10px; padding:10px 0; border-top:1px solid #f1f3f5;">
                                        <span style="font-size:1.1rem; line-height:1">${icon}</span>
                                        <div style="flex:1; min-width:0">
                                            <div style="display:flex; justify-content:space-between; align-items:center;">
                                                <span style="font-weight:600; font-size:0.75rem; text-transform:uppercase; color:#2d5a27; letter-spacing:.5px">${label}</span>
                                                <span style="font-size:0.7rem; color:#bbb;">${entryDt}</span>
                                            </div>
                                            <p style="margin:2px 0 0; font-size:0.85rem; color:#555; word-break:break-word">${entry.summary}</p>
                                        </div>
                                    </div>`;
                                }).join('')
                            }
                        </div>
                    </div>`;
                }).join('')}
            </div>`;
    } catch (err) {
        console.error('Activity log load error:', err);
        el.innerHTML = '<p style="color:#888">Could not load activity log.</p>';
    }
}

// ── Weather widget (dashboard overview) ──────────────────────────────────────


async function loadWeatherData() {
    try {
        const res = await apiFetch(`${API_BASE}/weather-forecast?location=default`);
        if (!res) return;
        const data = await res.json();
        if (!data.success) return;

        const current = data.forecast.weather_data.current;
        const el = document.getElementById('weather-summary');
        if (el) {
            el.innerHTML = `
                <div class="weather-info">
                    <p><strong>${current.condition}</strong></p>
                    <p>Temperature: ${current.temperature}°C</p>
                    <p>Humidity: ${current.humidity}%</p>
                    <p>Precipitation: ${current.precipitation_chance}%</p>
                </div>`;
        }
    } catch (err) {
        console.error('Weather load error:', err);
    }
}

// ── Market prices widget (dashboard overview) ─────────────────────────────────

async function loadMarketPrices() {
    try {
        const res = await apiFetch(`${API_BASE}/market-prices`);
        if (!res) return;
        const data = await res.json();
        if (!data.success) return;

        const el = document.getElementById('market-insights');
        if (el) {
            el.innerHTML = '<div class="price-list">' +
                Object.entries(data.prices).map(([crop, price]) =>
                    `<p><strong>${crop}:</strong> $${price}/kg</p>`
                ).join('') +
                '</div>';
        }
    } catch (err) {
        console.error('Market prices load error:', err);
    }
}

// ── Crop planning ─────────────────────────────────────────────────────────────

function toggleFarmingPurposeFields() {
    const purpose = document.getElementById('farmingPurpose').value;
    const personalFields = document.getElementById('personalFields');
    const commercialFields = document.getElementById('commercialFields');
    const submitBtn = document.getElementById('cropSubmitBtn');

    if (purpose === 'personal') {
        personalFields.style.display = 'flex';
        commercialFields.style.display = 'none';
        submitBtn.style.display = 'inline-block';
    } else if (purpose === 'commercial') {
        personalFields.style.display = 'none';
        commercialFields.style.display = 'flex';
        submitBtn.style.display = 'inline-block';
    } else {
        personalFields.style.display = 'none';
        commercialFields.style.display = 'none';
        submitBtn.style.display = 'none';
    }
}

async function handleCropPlanning(e) {
    e.preventDefault();
    const resultsDiv = document.getElementById('cropResults');
    resultsDiv.innerHTML = '<p class="loading">Getting recommendations…</p>';

    const purpose = document.getElementById('farmingPurpose').value;
    let payload = { purpose };

    if (purpose === 'personal') {
        payload.climate = document.getElementById('personalClimate').value;
        payload.soil = document.getElementById('personalSoil').value;
        payload.water_availability = document.getElementById('personalWater').value;
        payload.space = document.getElementById('personalSpace').value;
        payload.season = document.getElementById('personalSeason').value;
        payload.crop_duration = document.getElementById('personalDuration').value;
        payload.low_maintenance = document.getElementById('personalLowMaintenance').checked;
    } else if (purpose === 'commercial') {
        payload.climate = document.getElementById('commercialClimate').value;
        payload.soil_fertility = document.getElementById('commercialSoil').value;
        payload.water_availability = document.getElementById('commercialWater').value;
        payload.market_demand = document.getElementById('commercialMarket').value;
        payload.profitability = document.getElementById('commercialProfitability').value;
        payload.pest_management = document.getElementById('commercialPest').value;
        payload.cost_of_production = document.getElementById('commercialCost').value;
        payload.land_size = document.getElementById('commercialLand').value;
    }

    try {
        const res = await apiFetch(`${API_BASE}/crop-recommendation`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const plans = data.harvesting_plan;
            if (!plans || !plans.length) {
                resultsDiv.innerHTML = '<div class="message error">No suitable crops found for these conditions.</div>';
                return;
            }
            const htmlCards = await Promise.all(plans.map(async plan => {
                const imgUrl = await getCropImage(plan.name || '');
                return `
                <div class="result-highlight" style="margin-bottom: 30px; display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <h3 style="color: #2d5a27; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-bottom: 15px;">
                            ${plan.name || 'Crop Plan'}
                        </h3>
                        ${renderSection('Planting', plan.planting)}
                        ${renderSection('Growing requirements', plan.growing_requirements)}
                        ${renderSection('Maintenance', plan.maintenance_schedule)}
                        ${renderSection('Harvesting', plan.harvesting_plan)}
                        ${plan.common_problems ? renderSection('Common problems', plan.common_problems) : ''}
                        ${plan['Custom AI Advisory'] ? renderSection('AI Advisory', plan['Custom AI Advisory']) : ''}
                    </div>
                    <div style="width: 300px; height: 300px; flex-shrink: 0; border-radius: 8px; overflow: hidden; background: #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <img src="${imgUrl}" alt="${plan.name}" style="width: 100%; height: 100%; object-fit: cover; display: block;">
                    </div>
                </div>
                `;
            }));
            resultsDiv.innerHTML = '<h3>Recommended Crops for Your Setup</h3>' + htmlCards.join('');
            loadActivityLog(); // refresh recent activity immediately
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error getting crop recommendations.</div>';
        console.error(err);
    }
}

function renderSection(title, obj) {
    if (!obj || (Array.isArray(obj) && obj.length === 0)) return '';

    // Array of objects (e.g. common_problems: [{problem, symptoms, solution}, ...])
    if (Array.isArray(obj)) {
        const items = obj.map(item => {
            if (typeof item === 'object' && item !== null) {
                const inner = Object.entries(item).map(([k, v]) =>
                    `<div><strong style="text-transform:capitalize">${k.replace(/_/g,' ')}:</strong> ${v}</div>`
                ).join('');
                return `<li style="margin-bottom:10px; padding:8px; background:#f8f9fa; border-radius:6px; list-style:none;">${inner}</li>`;
            }
            return `<li>${item}</li>`;
        }).join('');
        return `<div class="result-item"><h4>${title}</h4><ul style="padding-left:0">${items}</ul></div>`;
    }

    // Plain object (e.g. maintenance_schedule, harvesting_plan)
    if (typeof obj === 'object') {
        let rows = '';
        for (const [key, val] of Object.entries(obj)) {
            const label = key.replace(/_/g, ' ');
            let display;
            if (Array.isArray(val)) {
                display = `<ul>${val.map(v => typeof v === 'object' ? `<li>${JSON.stringify(v)}</li>` : `<li>${v}</li>`).join('')}</ul>`;
            } else if (typeof val === 'object' && val !== null) {
                display = Object.entries(val).map(([k2, v2]) => `<div><em>${k2}:</em> ${v2}</div>`).join('');
            } else {
                display = `<span>${val}</span>`;
            }
            rows += `<tr><td style="padding:6px 12px 6px 0; vertical-align:top; color:#555; white-space:nowrap"><strong>${label}</strong></td><td style="padding:6px 0">${display}</td></tr>`;
        }
        return `<div class="result-item"><h4>${title}</h4><table class="info-table" style="width:100%">${rows}</table></div>`;
    }

    // Primitive fallback
    return `<div class="result-item"><h4>${title}</h4><p>${obj}</p></div>`;
}

// ── Crop Encyclopedia Info ──────────────────────────────────────────────────────

async function handleCropInfoSearch(e) {
    if (e) e.preventDefault();
    const query = document.getElementById('cropInfoSearch').value.trim();
    const resultsDiv = document.getElementById('cropInfoResults');
    
    if (!query) {
        resultsDiv.innerHTML = '<div class="message error">Please enter a crop to search.</div>';
        return;
    }
    
    resultsDiv.innerHTML = '<p class="loading">Searching encyclopedia...</p>';

    try {
        const res = await apiFetch(`${API_BASE}/crop-info?q=${encodeURIComponent(query)}`);
        if (!res) return;
        const data = await res.json();

        if (data.success && data.results && data.results.length > 0) {
            const htmlCards = await Promise.all(data.results.map(async plan => {
                const imgUrl = await getCropImage(plan.name || '');
                return `
                <div class="result-highlight" style="margin-bottom: 30px; display: flex; gap: 20px; align-items: flex-start; flex-wrap: wrap;">
                    <div style="flex: 1; min-width: 300px;">
                        <h3 style="color: #2d5a27; border-bottom: 2px solid #ddd; padding-bottom: 5px; margin-bottom: 15px;">
                            ${plan.name || 'Crop Plan'}
                        </h3>
                        ${renderSection('Planting', plan.planting)}
                        ${renderSection('Growing requirements', plan.growing_requirements)}
                        ${renderSection('Maintenance', plan.maintenance_schedule)}
                        ${renderSection('Harvesting', plan.harvesting_plan)}
                        ${plan.common_problems ? renderSection('Common problems', plan.common_problems) : ''}
                    </div>
                    <div style="width: 300px; height: 300px; flex-shrink: 0; border-radius: 8px; overflow: hidden; background: #e9ecef; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <img src="${imgUrl}" alt="${plan.name}" style="width: 100%; height: 100%; object-fit: cover; display: block;">
                    </div>
                </div>
                `;
            }));
            resultsDiv.innerHTML = `<h3>Search Results for "${query}"</h3>` + htmlCards.join('');
            loadActivityLog();
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message || 'No results found.'}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error searching crop encyclopedia.</div>';
        console.error(err);
    }
}

// ── Soil health ───────────────────────────────────────────────────────────────

async function handleSoilAnalysis(e) {
    e.preventDefault();
    const resultsDiv = document.getElementById('soilResults');
    resultsDiv.innerHTML = '<p class="loading">Analysing soil…</p>';

    try {
        const res = await apiFetch(`${API_BASE}/soil-health`, {
            method: 'POST',
            body: JSON.stringify({
                ph_level:  document.getElementById('phLevel').value,
                soil_type: document.getElementById('soilTypeAnalysis').value,
                color:     document.getElementById('color').value,
                moisture:  document.getElementById('moisture').value,
            })
        });
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const a = data.analysis;
            resultsDiv.innerHTML = `
                <h3>Soil health analysis</h3>
                <div class="result-highlight"><h4>Status: ${a.health_status}</h4></div>
                <div class="result-item">
                    <h4>Recommendations</h4>
                    <ul>${a.recommendations.map(r => `<li>${r}</li>`).join('')}</ul>
                </div>
                <div class="result-item">
                    <h4>Suitable crops</h4>
                    <p>${a.suitable_crops.join(', ') || 'N/A'}</p>
                </div>
                <div class="result-item">
                    <h4>Nutrient notes</h4>
                    <ul>${a.nutrient_needs.map(n => `<li>${n}</li>`).join('')}</ul>
                </div>`;
            loadActivityLog();
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error analysing soil.</div>';
        console.error(err);
    }
}

// ── Disease detection ─────────────────────────────────────────────────────────

function previewDiseaseImage(event) {
    const file = event.target.files[0];
    const previewContainer = document.getElementById('imagePreviewContainer');
    const previewImg = document.getElementById('diseaseImagePreview');
    
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            previewImg.src = e.target.result;
            previewContainer.style.display = 'block';
        };
        reader.readAsDataURL(file);
    } else {
        previewContainer.style.display = 'none';
        previewImg.src = '';
    }
}

async function handleDiseaseDetection(e) {
    e.preventDefault();
    const resultsDiv = document.getElementById('diseaseResults');
    const cropName = document.getElementById('cropName').value;
    const fileInput = document.getElementById('diseaseImage');
    
    if (!fileInput.files.length) {
        resultsDiv.innerHTML = '<div class="message error">Please upload a photo of the plant to analyze.</div>';
        return;
    }

    resultsDiv.innerHTML = '<p class="loading">Running CNN image analysis…</p>';

    const formData = new FormData();
    formData.append('crop_name', cropName);
    formData.append('image', fileInput.files[0]);

    try {
        const headers = authHeaders();
        delete headers['Content-Type']; // Let browser set multipart/form-data boundary
        
        const res = await fetch(`${API_BASE}/disease-detection`, {
            method: 'POST',
            headers: headers,
            body: formData
        });
        
        if (res.status === 401 || res.status === 403) {
            logout();
            return;
        }
        
        const data = await res.json();

        if (data.success) {
            resultsDiv.innerHTML = '<h3>Disease detection results</h3>' +
                data.diseases.map(d => `
                    <div class="result-item">
                        <h4>${d.disease}
                            <span class="confidence-badge">${d.confidence}% match</span>
                        </h4>
                        <p><strong>Crop:</strong> ${d.crop}</p>
                        <p><strong>Key symptoms:</strong> ${d.symptoms}</p>
                        <p><strong>Treatment:</strong> ${d.treatment}</p>
                        <p><strong>Prevention:</strong> ${d.prevention}</p>
                    </div>`
                ).join('');
            loadActivityLog();
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error detecting disease.</div>';
        console.error(err);
    }
}

// ── Finance estimation ────────────────────────────────────────────────────────

function toggleFinanceMode() {
    const mode = document.getElementById('financeMode').value;
    const detailedFields = document.getElementById('detailedFinanceFields');
    if (mode === 'detailed') {
        detailedFields.style.display = 'block';
    } else {
        detailedFields.style.display = 'none';
    }
}

async function handleFinanceCalculation(e) {
    e.preventDefault();
    const resultsDiv = document.getElementById('financeResults');
    resultsDiv.innerHTML = '<p class="loading">Calculating…</p>';

    const mode = document.getElementById('financeMode').value;
    let payload = {
        mode: mode,
        crop_name: document.getElementById('financeCrop').value,
        area_sqm:  parseFloat(document.getElementById('area').value) || 0
    };

    if (mode === 'detailed') {
        payload.cost_fixed = parseFloat(document.getElementById('costFixed').value) || 0;
        payload.cost_variable = parseFloat(document.getElementById('costVariable').value) || 0;
        payload.yield_scenario = document.getElementById('yieldScenario').value;
        payload.target_price = parseFloat(document.getElementById('targetPrice').value) || null;
        
        payload.loan_amount = parseFloat(document.getElementById('loanAmount').value) || 0;
        payload.loan_interest = parseFloat(document.getElementById('loanInterest').value) || 0;
        payload.loan_duration = parseInt(document.getElementById('loanDuration').value) || 0;
    }

    try {
        const res = await apiFetch(`${API_BASE}/finance-estimation`, {
            method: 'POST',
            body: JSON.stringify(payload)
        });
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const est = data.estimation;
            const profitColor = est.gross_profit >= 0 ? 'green' : 'red';
            
            let detailedHtml = '';
            if (mode === 'detailed') {
                detailedHtml += `
                    <div class="result-item">
                        <h4>Detailed Analysis</h4>
                        <p>Scenario Used: <strong>${(payload.yield_scenario || 'realistic').toUpperCase()}</strong></p>
                        ${payload.loan_amount > 0 ? `<p>Monthly Loan EMI: <strong>$${est.monthly_emi || 'N/A'}</strong></p>
                        <p>Net Profit (after loan): <strong>$${est.net_profit || 'N/A'}</strong></p>` : ''}
                    </div>
                `;
            }

            resultsDiv.innerHTML = `
                <h3>Financial estimation</h3>
                <div class="result-highlight">
                    <p>Total cost: <strong>$${est.total_cost}</strong></p>
                    <p>Expected revenue: <strong>$${est.expected_revenue}</strong></p>
                    <p>Gross profit: <strong style="color:${profitColor}">$${est.gross_profit}</strong></p>
                    <p>Profit margin: <strong>${est.profit_margin_percent}%</strong></p>
                    <p>ROI: <strong>${est.roi_percent}%</strong></p>
                </div>
                ${detailedHtml}
                <div class="result-item">
                    <h4>Cost breakdown</h4>
                    <ul>${Object.entries(est.costs_breakdown || {}).map(([k, v]) =>
                        `<li>${k.replace(/_/g, ' ')}: $${v}</li>`).join('')}</ul>
                </div>
                <div class="result-item">
                    <h4>Additional details</h4>
                    <p>Expected yield: ${est.expected_yield_kg} kg</p>
                    <p>Growing period: ${est.growing_period_months} months</p>
                    <p>Monthly cost: $${est.monthly_cost}</p>
                    <p>Break-even yield: ${est.break_even_point} kg</p>
                </div>`;
            loadActivityLog();
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error calculating finances.</div>';
        console.error(err);
    }
}

// ── Irrigation schedule ───────────────────────────────────────────────────────

async function handleIrrigationSchedule(e) {
    e.preventDefault();
    const resultsDiv = document.getElementById('irrigationResults');
    resultsDiv.innerHTML = '<p class="loading">Building schedule…</p>';

    try {
        const res = await apiFetch(`${API_BASE}/irrigation-schedule`, {
            method: 'POST',
            body: JSON.stringify({
                crop_name:         document.getElementById('irrigationCrop').value,
                weather_condition: document.getElementById('weatherCondition').value,
                soil_moisture:     document.getElementById('soilMoisture').value,
            })
        });
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const s = data.schedule;
            resultsDiv.innerHTML = `
                <h3>Irrigation schedule</h3>
                <div class="result-highlight">
                    <h4>${s.crop_name} — ${s.frequency}</h4>
                    <p>Amount per session: <strong>${s.amount_per_session}</strong></p>
                    <p>Weekly requirement: <strong>${s.weekly_water_requirement_mm} mm</strong></p>
                    <p>Best time to water: ${s.best_time_to_water}</p>
                    <p>Recommended method: ${s.irrigation_method}</p>
                </div>
                <div class="result-item">
                    <h4>Watering tips</h4>
                    <ul>${s.watering_tips.map(t => `<li>${t}</li>`).join('')}</ul>
                </div>
                <div class="result-item">
                    <h4>Water saving tips</h4>
                    <ul>${s.water_saving_tips.map(t => `<li>${t}</li>`).join('')}</ul>
                </div>`;
            loadActivityLog();
            
            // Sync with Live Controls
            syncRecommendationToLive(s.weekly_water_requirement_mm);
        } else {
            resultsDiv.innerHTML = `<div class="message error">${data.message}</div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error getting irrigation schedule.</div>';
        console.error(err);
    }
}

// ── AI Advisory chat ──────────────────────────────────────────────────────────

async function sendAdvisoryQuery() {
    const input = document.getElementById('advisoryQuery');
    const query = input.value.trim();
    if (!query) return;

    addChatMessage(query, 'user');
    input.value = '';

    // Typing indicator
    const typingId = 'typing-' + Date.now();
    addChatMessage('…', 'bot', typingId);

    try {
        const res = await apiFetch(`${API_BASE}/advisory`, {
            method: 'POST',
            body: JSON.stringify({ query })
        });

        // Remove typing indicator
        document.getElementById(typingId)?.remove();

        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const advice = data.advice;
            // Build a readable chat bubble from the structured response
            let html = `<strong>${advice.title}</strong>`;

            if (advice.summary) {
                html += `<p>${advice.summary}</p>`;
            }
            if (advice.recommendations && advice.recommendations.length) {
                html += '<ul>' + advice.recommendations.map(r => `<li>${r}</li>`).join('') + '</ul>';
            }
            if (advice.tips && advice.tips.length) {
                html += `<p><em>Tips: ${advice.tips.join(' · ')}</em></p>`;
            }
            if (advice.warning) {
                html += `<p class="advisory-warning">⚠ ${advice.warning}</p>`;
            }
            if (advice.note) {
                html += `<p class="advisory-note">${advice.note}</p>`;
            }
            addChatMessage(html, 'bot', null, true);
            loadActivityLog();
        } else {
            addChatMessage('Sorry, I could not process your question. Please try again.', 'bot');
        }
    } catch (err) {
        document.getElementById(typingId)?.remove();
        addChatMessage('Error connecting to advisory service. Please try again.', 'bot');
        console.error('Advisory error:', err);
    }
}

function addChatMessage(content, sender, id = null, isHtml = false) {
    const chatMessages = document.getElementById('chatMessages');
    const div = document.createElement('div');
    div.className = `message ${sender}-message`;
    if (id) div.id = id;

    const inner = document.createElement('div');
    inner.className = 'message-content';
    if (isHtml) {
        inner.innerHTML = content;
    } else {
        inner.textContent = content;
    }

    div.appendChild(inner);
    chatMessages.appendChild(div);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ── Navigation ────────────────────────────────────────────────────────────────

function showSection(sectionId) {
    document.querySelectorAll('.content-section').forEach(s => s.classList.remove('active'));
    document.querySelectorAll('.sidebar-menu a').forEach(a => a.classList.remove('active'));

    document.getElementById(sectionId)?.classList.add('active');
    document.querySelector(`[onclick="showSection('${sectionId}')"]`)?.classList.add('active');

    if (sectionId === 'market-prices') loadMarketPricesSection();
    if (sectionId === 'weather')       loadWeatherSection();
}

async function loadMarketPricesSection() {
    const resultsDiv = document.getElementById('pricesResults');
    if (!resultsDiv) return;
    resultsDiv.innerHTML = '<p class="loading">Loading prices…</p>';

    try {
        const res = await apiFetch(`${API_BASE}/market-prices`);
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            resultsDiv.innerHTML = '<h3>Current market prices</h3><div class="price-grid">' +
                Object.entries(data.prices).map(([crop, price]) => `
                    <div class="price-card">
                        <h4>${crop}</h4>
                        <p class="price">$${price}<span class="unit">/kg</span></p>
                    </div>`
                ).join('') + '</div>';
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error loading market prices.</div>';
        console.error(err);
    }
}

function filterMarketPrices() {
    const query = document.getElementById('marketSearch').value.toLowerCase();
    const cards = document.querySelectorAll('#pricesResults .price-card');
    cards.forEach(card => {
        const cropName = card.querySelector('h4').textContent.toLowerCase();
        if (cropName.includes(query)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
}

async function loadWeatherSection() {
    const resultsDiv = document.getElementById('weatherResults');
    if (!resultsDiv) return;
    resultsDiv.innerHTML = '<p class="loading">Loading forecast…</p>';

    try {
        const res = await apiFetch(`${API_BASE}/weather-forecast?location=default`);
        if (!res) return;
        const data = await res.json();

        if (data.success) {
            const w = data.forecast.weather_data;
            const recs = data.forecast.farming_recommendations;
            const alerts = data.forecast.alerts || [];

            const alertsHtml = alerts.length
                ? '<div class="result-item"><h4>Alerts</h4><ul>' +
                  alerts.map(a => `<li class="alert-${a.severity}">${a.message}</li>`).join('') +
                  '</ul></div>'
                : '';

            const forecastHtml = w.forecast.slice(0, 5).map(day => `
                <div class="forecast-day">
                    <strong>${day.date}</strong>
                    <span>${day.condition}</span>
                    <span>${day.temperature_min}–${day.temperature_max}°C</span>
                    <span>💧 ${day.precipitation_chance}%</span>
                </div>`).join('');

            resultsDiv.innerHTML = `
                <h3>Weather forecast & recommendations</h3>
                <div class="result-highlight">
                    <h4>Current conditions</h4>
                    <p>Temperature: ${w.current.temperature}°C</p>
                    <p>Condition: ${w.current.condition}</p>
                    <p>Humidity: ${w.current.humidity}%</p>
                    <p>Wind: ${w.current.wind_speed} km/h</p>
                </div>
                ${alertsHtml}
                <div class="result-item">
                    <h4>5-day forecast</h4>
                    <div class="forecast-grid">${forecastHtml}</div>
                </div>
                <div class="result-item">
                    <h4>Farming recommendations</h4>
                    <ul>${recs.map(r => `<li>${r}</li>`).join('')}</ul>
                </div>`;
        }
    } catch (err) {
        resultsDiv.innerHTML = '<div class="message error">Error loading weather data.</div>';
        console.error(err);
    }
}

// ── Utilities ─────────────────────────────────────────────────────────────────

function showMessage(elementId, message, type = 'info') {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = message;
    el.className = `message ${type}`;
    el.style.display = 'block';
    setTimeout(() => { el.style.display = 'none'; }, 5000);
}

function logout() {
    localStorage.removeItem('user');
    window.location.href = 'index.html';
}

// ── Irrigation Management ──────────────────────────────────────────────────

let irrigationInterval = null;

function initIrrigationDashboard() {
    // Only start polling if we haven't already
    if (!irrigationInterval) {
        refreshIrrigationStatus(); // Initial load
        irrigationInterval = setInterval(refreshIrrigationStatus, 3000); // 3-second heartbeat
    }
}

async function refreshIrrigationStatus() {
    // Only poll if the irrigation section is active or we're on dashboard
    const activeSection = document.querySelector('.content-section.active')?.id;
    if (activeSection !== 'irrigation' && activeSection !== 'dashboard') return;

    try {
        const res = await apiFetch(`${API_BASE}/irrigation/status`);
        if (!res) return;
        const data = await res.json();
        if (data.success) {
            updateIrrigationUI(data.status);
        }
    } catch (err) {
        console.error('Irrigation status error:', err);
    }
}

function updateIrrigationUI(status) {
    const s = status.settings;
    const logs = status.recent_logs;
    
    // 1. Update Soil Moisture
    const moisture = parseFloat(s.current_moisture);
    const gauge = document.getElementById('moistureGauge');
    const valueText = document.getElementById('moistureValue');
    if (gauge) gauge.style.width = `${moisture}%`;
    if (valueText) valueText.textContent = `${moisture.toFixed(1)}%`;
    
    // 2. Update Pump Status
    const isPumpOn = s.pump_state;
    const pumpStatus = document.getElementById('pumpStatus');
    const pumpIcon = document.getElementById('pumpIcon');
    const pumpBtn = document.getElementById('pumpToggleBtn');
    
    if (pumpStatus) {
        pumpStatus.textContent = isPumpOn ? 'ON' : 'OFF';
        pumpStatus.style.color = isPumpOn ? '#38a169' : '#718096';
    }
    if (pumpIcon) {
        pumpIcon.className = `status-icon ${isPumpOn ? 'pump-on' : 'pump-off'}`;
        pumpIcon.textContent = isPumpOn ? '💧' : '🔌';
    }
    if (pumpBtn) {
        const enText = isPumpOn ? 'Stop Pump' : 'Start Pump';
        const hiText = isPumpOn ? 'पंप रोकें' : 'पंप शुरू करें';
        pumpBtn.innerHTML = `<span class="lang-en">${enText}</span><span class="lang-hi">${hiText}</span>`;
        pumpBtn.className = isPumpOn ? 'btn btn-warning' : 'btn btn-secondary';
    }
    
    // 3. Update Auto Mode
    const autoToggle = document.getElementById('autoModeToggle');
    if (autoToggle) {
        autoToggle.checked = !!s.auto_mode;
    }
    
    // 4. Update Target Moisture
    const targetRange = document.getElementById('targetMoistureRange');
    const targetLabel = document.getElementById('targetMoistureLabel');
    if (targetRange && !targetRange.matches(':active')) { // Don't snap while user is sliding
        targetRange.value = s.target_moisture;
        if (targetLabel) targetLabel.innerHTML = `<span class="lang-en">Threshold: ${s.target_moisture}%</span><span class="lang-hi">सीमा: ${s.target_moisture}%</span>`;
    }
    
    // 5. Update Water Consumed
    const consumption = document.getElementById('waterConsumed');
    if (consumption) {
        consumption.textContent = `${parseFloat(s.water_consumed_today).toFixed(2)} L`;
    }
    
    // 6. Update History Log
    updateIrrigationHistoryTable(logs);
}

function updateIrrigationHistoryTable(logs) {
    const body = document.getElementById('irrigationHistoryBody');
    if (!body || !logs) return;
    
    if (logs.length === 0) {
        body.innerHTML = '<tr><td colspan="4" style="text-align:center; padding:20px; color:#999;">No activities yet.</td></tr>';
        return;
    }
    
    body.innerHTML = logs.map(log => `
        <tr>
            <td>${log.timestamp}</td>
            <td><strong>${log.action}</strong></td>
            <td><span class="badge" style="background:${log.source === 'auto' ? '#ebf8ff' : '#f7fafc'}; color:${log.source === 'auto' ? '#2b6cb0' : '#4a5568'}; padding:2px 6px; border-radius:4px; font-size:0.75rem; text-transform:uppercase;">${log.source}</span></td>
            <td>${parseFloat(log.water_used_liters) > 0 ? log.water_used_liters + ' L' : '—'}</td>
        </tr>
    `).join('');
}

async function togglePump() {
    const pumpStatus = document.getElementById('pumpStatus').textContent;
    const newState = pumpStatus === 'OFF'; // If currently off, turn on
    
    try {
        const res = await apiFetch(`${API_BASE}/irrigation/toggle`, {
            method: 'POST',
            body: JSON.stringify({ action: 'pump', state: newState })
        });
        const data = await res.json();
        if (data.success) {
            updateIrrigationUI(data.status);
        }
    } catch (err) {
        console.error('Toggle pump error:', err);
    }
}

async function toggleAutoMode() {
    const toggle = document.getElementById('autoModeToggle');
    const newState = toggle.checked;
    
    try {
        const res = await apiFetch(`${API_BASE}/irrigation/toggle`, {
            method: 'POST',
            body: JSON.stringify({ action: 'auto', state: newState })
        });
        const data = await res.json();
        if (data.success) {
            updateIrrigationUI(data.status);
        }
    } catch (err) {
        console.error('Toggle auto error:', err);
    }
}

async function updateTargetMoisture(val) {
    const label = document.getElementById('targetMoistureLabel');
    if (label) label.innerHTML = `<span class="lang-en">Threshold: ${val}%</span><span class="lang-hi">सीमा: ${val}%</span>`;
    
    // Debounce this better in production, but for now just send on change
    try {
        await apiFetch(`${API_BASE}/irrigation/toggle`, {
            method: 'POST',
            body: JSON.stringify({ action: 'target', target: val })
        });
    } catch (err) {
        console.error('Update target error:', err);
    }
}

async function syncRecommendationToLive(weeklyWaterReq) {
    // Map weekly req (mm) to target moisture %
    // Logic: Low needs (10mm) -> 40%, High (40mm) -> 80%
    let target = 50;
    if (weeklyWaterReq > 40) target = 80;
    else if (weeklyWaterReq > 30) target = 70;
    else if (weeklyWaterReq > 20) target = 60;
    else if (weeklyWaterReq > 10) target = 45;
    else target = 35;

    // Update UI components
    const targetRange = document.getElementById('targetMoistureRange');
    const targetLabel = document.getElementById('targetMoistureLabel');
    const controlCard = targetRange?.closest('.dashboard-card');

    if (targetRange) {
        targetRange.value = target;
        if (targetLabel) targetLabel.innerHTML = `<span class="lang-en">Threshold: ${target}% (Synced)</span><span class="lang-hi">सीमा: ${target}% (सिंक)</span>`;
        
        // Visual feedback: brief highlight
        if (controlCard) {
            controlCard.style.transition = 'all 0.5s ease';
            controlCard.style.boxShadow = '0 0 20px rgba(56, 161, 105, 0.4)';
            controlCard.style.borderColor = '#38a169';
            setTimeout(() => {
                controlCard.style.boxShadow = '';
                controlCard.style.borderColor = '';
            }, 3000);
        }

        // Persist to backend
        try {
            await apiFetch(`${API_BASE}/irrigation/toggle`, {
                method: 'POST',
                body: JSON.stringify({ action: 'target', target: target })
            });
            
            // Automatically enable Auto-Irrigation if it was off
            const autoToggle = document.getElementById('autoModeToggle');
            if (autoToggle && !autoToggle.checked) {
                autoToggle.checked = true;
                await toggleAutoMode();
            }
        } catch (err) {
            console.error('Sync persistence error:', err);
        }
    }
}

// ── Extra styles injected at runtime ─────────────────────────────────────────

const extraStyles = `
.loading { color: var(--text-muted, #666); font-style: italic; }
.info-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; }
.info-table td { padding: 4px 8px; vertical-align: top; font-size: 0.9rem; }
.info-table tr:nth-child(odd) td { background: rgba(0,0,0,0.03); }
.confidence-badge {
    font-size: 0.75rem; font-weight: normal;
    background: #e8f5e9; color: #2d5a27;
    padding: 2px 8px; border-radius: 12px; margin-left: 8px;
}
.advisory-warning { color: #b45309; background: #fffbeb; padding: 6px 10px; border-radius: 4px; }
.advisory-note    { color: #555; font-size: 0.85rem; font-style: italic; }
.price-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 1rem; margin-top: 1rem;
}
.price-card {
    background: #f8f9fa; padding: 1rem;
    border-radius: 8px; text-align: center;
    border: 1px solid #e9ecef;
}
.price-card h4 { color: #2d5a27; margin-bottom: 0.4rem; }
.price { font-size: 1.4rem; font-weight: bold; color: #2d5a27; }
.unit  { font-size: 0.8rem; color: #666; }
.forecast-grid { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
.forecast-day {
    display: flex; flex-direction: column; gap: 2px;
    background: #f8f9fa; border: 1px solid #e9ecef;
    border-radius: 8px; padding: 8px 12px; font-size: 0.85rem; min-width: 120px;
}
.forecast-day strong { color: #2d5a27; }
.alert-high   { color: #b91c1c; }
.alert-medium { color: #b45309; }
.alert-low    { color: #1d4ed8; }
`;

const styleEl = document.createElement('style');
styleEl.textContent = extraStyles;
document.head.appendChild(styleEl);
