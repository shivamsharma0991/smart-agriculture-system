import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

# Support multiple API keys for the waterfall fallback system
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
COHERE_API_KEY = os.getenv('COHERE_API_KEY')


SYSTEM_PROMPT = """You are an expert agricultural advisor with deep knowledge of:
- Crop planning, growing, and harvesting
- Soil health and management
- Pest and disease identification and treatment
- Irrigation and water management
- Organic and sustainable farming practices
- Market trends and financial planning for farmers
- Climate-smart agriculture

Provide practical, actionable advice tailored to the farmer's question.
Keep responses clear and concise. Format your response as JSON with this structure:
{
  "title": "short topic title",
  "category": "one of: pest_control | irrigation | soil_health | planting | harvesting | organic | climate | finance | general",
  "summary": "2-3 sentence overview",
  "recommendations": ["list", "of", "actionable", "steps"],
  "tips": ["additional", "helpful", "tips"],
  "warning": "any important caution or null if none"
}
Return only valid JSON, no markdown, no extra text."""


def get_advice(query):
    """
    WATERFALL SYSTEM: 
    Tries APIs in sequence (Gemini -> Groq -> OpenAI). 
    If one fails or lacks a key, it falls back to the next.
    """
    last_error = ""

    # 1. Try Google Gemini (Free & Fast)
    if GEMINI_API_KEY:
        try:
            print("Advisory: Trying Gemini API...")
            return _call_gemini(query)
        except Exception as e:
            print(f"Gemini failed: {e}")
            last_error = str(e)

    # 2. Try Groq (Llama 3 - Free & Fast)
    if GROQ_API_KEY:
        try:
            print("Advisory: Trying Groq API...")
            return _call_groq(query)
        except Exception as e:
            print(f"Groq failed: {e}")
            last_error = str(e)

    # 3. Try Cohere 
    if COHERE_API_KEY:
        try:
            print("Advisory: Trying Cohere API...")
            return _call_cohere(query)
        except Exception as e:
            print(f"Cohere failed: {e}")
            last_error = str(e)

    # 4. Final Fallback (Offline Rules)
    print("Advisory: All AI APIs failed or unavailable. Using offline fallback rules.")
    fallback = _fallback_advice(query)
    if last_error:
        fallback['warning'] = f"AI APIs were unavailable. Displaying offline generic advice. (Last err: {last_error})"
    return fallback


def _call_gemini(query):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [{"parts": [{"text": query}]}],
        "generationConfig": {"responseMimeType": "application/json"}
    }
    response = requests.post(url, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    text = data['candidates'][0]['content']['parts'][0]['text'].strip()
    return json.loads(text)


def _call_groq(query):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": query}
        ],
        "response_format": {"type": "json_object"}
    }
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    content = data['choices'][0]['message']['content']
    return json.loads(content)


def _call_cohere(query):
    url = "https://api.cohere.com/v1/chat"
    headers = {
        "Authorization": f"Bearer {COHERE_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "message": query,
        "model": "command-r",
        "preamble_override": SYSTEM_PROMPT
    }
    response = requests.post(url, headers=headers, json=payload, timeout=15)
    response.raise_for_status()
    data = response.json()
    text = data.get('text', '').strip()
    
    # Strip any accidental markdown fences
    if text.startswith('```'):
        text = text.split('```')[1]
        if text.startswith('json'):
            text = text[4:]
    return json.loads(text.strip())


def _fallback_advice(query):
    """Rule-based fallback when no API key is configured."""
    query_lower = query.lower()

    if any(w in query_lower for w in ['pest', 'insect', 'bug', 'disease', 'fungus', 'mold']):
        category = 'pest_control'
        title = 'Pest and disease management'
        recommendations = [
            'Identify the pest or disease before treating',
            'Use integrated pest management (IPM)',
            'Use organic pesticides like neem oil as a first option'
        ]
        tips = ['Remove and destroy infected material promptly']

    elif any(w in query_lower for w in ['water', 'irrigation', 'drought']):
        category = 'irrigation'
        title = 'Watering and irrigation'
        recommendations = [
            'Water deeply but less frequently to encourage deep roots',
            'Water early morning to reduce evaporation',
            'Check soil moisture 5 cm deep before watering'
        ]
        tips = ['Drip irrigation saves up to 50% more water than overhead sprinklers']

    elif any(w in query_lower for w in ['soil', 'ph', 'nutrient', 'compost', 'fertilizer']):
        category = 'soil_health'
        title = 'Soil health and management'
        recommendations = [
            'Test soil pH and nutrients annually',
            'Add compost or organic matter regularly',
            'Avoid tilling wet or very dry soil'
        ]
        tips = ['Healthy soil = healthy crops — invest in soil first']

    else:
        category = 'general'
        title = 'General farming advice'
        recommendations = [
            'Keep a farming journal to track what works',
            'Focus on soil health as the foundation of success',
            'Start small and scale as you gain experience'
        ]
        tips = ['Ask about specific topics like pests, watering, or soil for detailed advice']

    return {
        'title': title,
        'category': category,
        'summary': f'Here is some guidance on {title.lower()}.',
        'recommendations': recommendations,
        'tips': tips,
        'warning': None
    }

def _error_advice(message):
    return {
        'title': 'Advisory unavailable',
        'category': 'general',
        'summary': message,
        'recommendations': ['Please try again in a moment'],
        'tips': [],
        'warning': None
    }
