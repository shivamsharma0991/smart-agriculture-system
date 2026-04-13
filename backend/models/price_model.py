import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_API_URL = 'https://api.anthropic.com/v1/messages'

SYSTEM_PROMPT = """You are an agricultural market analyst. Predict crop prices and provide market insights.

Respond ONLY with valid JSON (no markdown, no extra text):
{
  "crop": "crop name",
  "predicted_price_per_kg": 2.50,
  "currency": "USD",
  "price_trend": "rising | stable | falling",
  "confidence": 75,
  "factors": ["key factor 1", "key factor 2"],
  "market_outlook": "brief 1-2 sentence market outlook",
  "best_selling_months": ["Month1", "Month2"]
}"""

# Static base prices used as fallback
BASE_PRICES = {
    'Tomato': 2.50, 'Lettuce': 1.80, 'Carrot': 1.20,
    'Spinach': 3.00, 'Pepper': 4.50, 'Potato': 1.50,
    'Onion': 2.00, 'Rice': 1.80, 'Wheat': 1.50, 'Maize': 1.20,
}


def predict_price(crop_name, month=None, season=None):
    """Predict price for a crop using Claude API."""
    if not month:
        month = datetime.now().strftime('%B')
    if not season:
        m = datetime.now().month
        season = 'Spring' if m in [3,4,5] else 'Summer' if m in [6,7,8] else 'Fall' if m in [9,10,11] else 'Winter'

    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY.startswith('sk-ant-...'):
        return _fallback_prediction(crop_name, month, season)

    prompt = f"Predict market price for {crop_name} in {month} ({season} season)."

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
        return json.loads(text.strip())
    except Exception as e:
        print(f"Price prediction API error: {e}")
        return _fallback_prediction(crop_name, month, season)


def _fallback_prediction(crop_name, month, season):
    base = BASE_PRICES.get(crop_name, 2.00)
    seasonal_multiplier = {'Summer': 1.1, 'Winter': 1.2, 'Spring': 0.95, 'Fall': 1.0}
    price = round(base * seasonal_multiplier.get(season, 1.0), 2)
    return {
        'crop': crop_name,
        'predicted_price_per_kg': price,
        'currency': 'USD',
        'price_trend': 'stable',
        'confidence': 60,
        'factors': ['Seasonal demand', 'Historical average'],
        'market_outlook': f'{crop_name} prices are expected to remain stable this {season}.',
        'best_selling_months': ['June', 'July'],
        'note': 'Add ANTHROPIC_API_KEY for AI-powered price predictions.'
    }


# Global instance stub — kept so existing imports don't break
class _PriceModelShim:
    def predict_price(self, crop_name, **kwargs):
        return predict_price(crop_name, **kwargs)

price_model = _PriceModelShim()
