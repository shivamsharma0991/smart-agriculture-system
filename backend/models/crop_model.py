import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'

SYSTEM_PROMPT = """You are an expert agronomist. Given environmental conditions, recommend the top 3 most suitable crops.

Respond ONLY with valid JSON (no markdown, no extra text):
{
  "recommendations": [
    {
      "rank": 1,
      "crop": "Crop name",
      "confidence": 92,
      "reason": "Brief reason why this crop suits these conditions",
      "notes": "One key growing tip"
    }
  ]
}"""


def predict_disease(crop_name, symptoms):
    """Kept for backwards compatibility — delegates to disease_model."""
    from models.disease_model import predict_disease as _predict
    return _predict(crop_name, symptoms)


def get_crop_recommendations(temperature, humidity, ph, rainfall, soil_type):
    """Get AI-powered crop recommendations based on environmental conditions."""
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith('sk-ant-...'):
        return _fallback_recommendations(temperature, humidity, ph, rainfall, soil_type)

    prompt = (
        f"Recommend crops for these conditions:\n"
        f"- Temperature: {temperature}°C\n"
        f"- Humidity: {humidity}%\n"
        f"- Soil pH: {ph}\n"
        f"- Annual rainfall: {rainfall}mm\n"
        f"- Soil type: {soil_type}"
    )

    try:
        response = requests.post(
            ANTHROPIC_API_URL,
            headers={
                'x-api-key': ANTHROPIC_API_KEY,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 512,
                'system': SYSTEM_PROMPT,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=15
        )
        response.raise_for_status()
        text = response.json()['content'][0]['text'].strip()
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        return json.loads(text.strip()).get('recommendations', [])
    except Exception as e:
        print(f"Crop recommendation API error: {e}")
        return _fallback_recommendations(temperature, humidity, ph, rainfall, soil_type)


def _fallback_recommendations(temperature, humidity, ph, rainfall, soil_type):
    """Simple rule-based fallback."""
    recs = []
    temp = float(temperature)
    ph_val = float(ph)

    if temp >= 20 and ph_val >= 5.5:
        recs.append({'rank': 1, 'crop': 'Tomato', 'confidence': 80, 'reason': 'Warm temperature and suitable pH', 'notes': 'Requires staking and consistent watering'})
    if temp <= 25 and ph_val >= 6.0:
        recs.append({'rank': 2, 'crop': 'Lettuce', 'confidence': 75, 'reason': 'Moderate temperature, prefers neutral pH', 'notes': 'Bolts in heat — provide afternoon shade'})
    if temp >= 15:
        recs.append({'rank': 3, 'crop': 'Carrot', 'confidence': 70, 'reason': 'Adaptable to a wide range of conditions', 'notes': 'Needs deep, loose soil for straight roots'})

    if not recs:
        recs = [{'rank': 1, 'crop': 'Spinach', 'confidence': 65, 'reason': 'Hardy and adaptable', 'notes': 'Cool-season crop, plant in spring or fall'}]

    return recs[:3]


# Global instance stub — kept so existing imports don't break
class _CropModelShim:
    def predict_crop(self, conditions):
        return get_crop_recommendations(
            conditions.get('temperature', 25),
            conditions.get('humidity', 60),
            conditions.get('ph', 6.5),
            conditions.get('rainfall', 800),
            conditions.get('soil_type', 'loamy')
        )

crop_model = _CropModelShim()
