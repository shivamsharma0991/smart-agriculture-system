import json
import random
import sys
import os

# Add parent directory so db.py is importable
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from db import get_db_connection


def get_harvesting_plan(data_payload):
    """
    Get detailed harvesting plans from MySQL based on form parameters.
    Returns an array of up to 3 recommended crops.
    """
    if isinstance(data_payload, str):
        data_payload = {'crop_name': data_payload}

    season_wanted  = (data_payload.get('season')             or '').lower()
    water_wanted   = (data_payload.get('water_availability') or '').lower()
    purpose        = data_payload.get('purpose', 'personal')

    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT name, season, water_needs, soil_type, sunlight, detailed_plan FROM crops")
        rows = cursor.fetchall()
    except Exception as e:
        print(f"DB error in get_harvesting_plan: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

    scored = []
    for row in rows:
        score = 0
        row_season = (row.get('season') or '').lower()
        row_water  = (row.get('water_needs') or '').lower()

        if season_wanted and season_wanted in row_season:
            score += 2
        if water_wanted:
            if 'daily' in water_wanted and 'high' in row_water:
                score += 1
            elif 'irregular' in water_wanted and 'low' in row_water:
                score += 1

        # Parse the JSON detail_plan column
        try:
            detail = row['detailed_plan']
            if isinstance(detail, str):
                detail = json.loads(detail)
        except Exception:
            detail = {}

        scored.append((score, row, detail))

    # Sort by score desc
    scored.sort(key=lambda x: x[0], reverse=True)

    best_score = scored[0][0] if scored else 0
    top_tier   = [(r, d) for s, r, d in scored if s == best_score]
    lower_tier = [(r, d) for s, r, d in scored if s <  best_score]

    random.shuffle(top_tier)
    candidates = (top_tier + lower_tier)[:3]

    results = []
    for row, detail in candidates:
        plan = {
            'name': row['name'],
            'planting': detail.get('planting', {
                'best_time': row.get('season', ''),
            }),
            'growing_requirements': detail.get('growing_requirements', {
                'water_frequency': row.get('water_needs', ''),
                'sunlight': row.get('sunlight', ''),
                'soil_type': row.get('soil_type', ''),
            }),
            'maintenance_schedule': detail.get('maintenance_schedule', {}),
            'harvesting_plan': detail.get('harvesting_plan', {}),
            'harvest_indicators': detail.get('harvest_indicators', []),
            'common_problems': detail.get('common_problems', []),
        }

        # Build custom advisory
        custom = {}
        if purpose == 'commercial':
            custom['Commercial Strategy'] = f"Focus on high-volume {data_payload.get('market_demand', 'local')} markets."
            custom['Cost Management'] = "Optimize labor and reduce inputs to maximize ROI."
            if data_payload.get('land_size'):
                custom['Scale Considerations'] = f"For {data_payload.get('land_size')}, mechanization is highly recommended."
        else:
            custom['Home Gardening Tips'] = "Focus on soil health and organic pest control."
            if data_payload.get('space'):
                custom['Space Utilization'] = f"Ideal for {data_payload.get('space')} setups."

        if data_payload.get('climate'):
            custom['Climate Match'] = f"Adjust care based on your {data_payload.get('climate')} climate."

        plan['Custom AI Advisory'] = custom
        results.append(plan)

    return results


def search_crop_info(query, limit=10):
    """
    Search crops by name from MySQL. Returns up to `limit` matching records.
    Used by the /api/crop-info endpoint.
    """
    conn = get_db_connection()
    if conn is None:
        return []

    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT name, season, water_needs, soil_type, sunlight, detailed_plan "
            "FROM crops WHERE LOWER(name) LIKE %s LIMIT %s",
            (f'%{query.lower()}%', limit)
        )
        rows = cursor.fetchall()
    except Exception as e:
        print(f"DB error in search_crop_info: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

    results = []
    for row in rows:
        try:
            detail = row['detailed_plan']
            if isinstance(detail, str):
                detail = json.loads(detail)
        except Exception:
            detail = {}

        results.append({
            'name': row['name'],
            'planting': detail.get('planting', {'best_time': row.get('season', '')}),
            'growing_requirements': detail.get('growing_requirements', {
                'water_frequency': row.get('water_needs', ''),
                'sunlight': row.get('sunlight', ''),
                'soil_type': row.get('soil_type', ''),
            }),
            'maintenance_schedule': detail.get('maintenance_schedule', {}),
            'harvesting_plan': detail.get('harvesting_plan', {}),
            'harvest_indicators': detail.get('harvest_indicators', []),
            'common_problems': detail.get('common_problems', []),
        })
    return results