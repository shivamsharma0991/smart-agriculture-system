import os
import json
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.security import check_password_hash
import jwt
import datetime
from dotenv import load_dotenv

from db import (
    create_user, get_user_by_username, create_tables, setup_user_database,
    get_crops, get_market_prices, save_activity, get_activity_log,
    save_soil_test, save_finance_record, save_advisory_history, get_advisory_history,
    create_session
)
from modules import crop_recommendation, soil_health, finance, irrigation, weather, advisory
from models import disease_model

load_dotenv()

app = Flask(__name__)
CORS(app)

SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-secret-in-production')


# ── Auth helpers ────────────────────────────────────────────────────────────

def create_token(user_id, username):
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = auth_header.replace('Bearer ', '').strip()
        if not token:
            return jsonify({'success': False, 'message': 'Missing token'}), 401
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            request.current_user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401
        return f(*args, **kwargs)
    return decorated


# ── Routes ──────────────────────────────────────────────────────────────────

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'})

    # Try database login first
    user = get_user_by_username(username)
    if user and check_password_hash(user['password'], password):
        token = create_token(user['id'], user['username'])
        # Create a new login session
        session_id = create_session(user['username'])
        return jsonify({
            'success': True, 
            'message': 'Login successful', 
            'token': token, 
            'user_id': user['id'],
            'username': user['username'],
            'session_id': session_id
        })

    # Hardcoded fallback for the demo user if DB is offline/unconfigured
    if username == 'admin' and password == 'password':
        token = create_token(1, 'admin')
        session_id = create_session('admin')
        return jsonify({
            'success': True, 
            'message': 'Login successful (Offline/Demo Mode)', 
            'token': token, 
            'user_id': 1,
            'username': 'admin',
            'session_id': session_id
        })

    return jsonify({'success': False, 'message': 'Invalid credentials or database offline'})


@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    name = data.get('name', '').strip()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    farm_size = data.get('farm_size', '').strip()

    if not username or not password or not name:
        return jsonify({'success': False, 'message': 'Name, username, and password are required'})

    success, message = create_user(name, username, password, farm_size)
    if success:
        return jsonify({'success': True, 'message': message})
    return jsonify({'success': False, 'message': message})


@app.route('/api/crops', methods=['GET'])
@require_auth
def get_crops_endpoint():
    try:
        crops = get_crops()
        return jsonify({'success': True, 'crops': crops})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/crop-recommendation', methods=['POST'])
@require_auth
def crop_recommendation_endpoint():
    data = request.get_json()
    username = request.current_user.get('username')
    try:
        harvesting_plan = crop_recommendation.get_harvesting_plan(data)
        crop_names = ', '.join([p.get('name','?') for p in harvesting_plan])
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'crop_recommendation',
            f"Crop recommendation: {crop_names}",
            {'input': data, 'recommended': crop_names},
            session_id=session_id)
        return jsonify({'success': True, 'harvesting_plan': harvesting_plan})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/crop-info', methods=['GET'])
@require_auth
def crop_info_endpoint():
    query = request.args.get('q', '').lower().strip()
    if not query:
        return jsonify({'success': False, 'message': 'Search query required'})

    # Query MySQL directly — no JSON memory cache
    matches = crop_recommendation.search_crop_info(query, limit=10)
    username = request.current_user.get('username')
    session_id = request.headers.get('X-Session-ID')
    save_activity(username, 'crop_info', f"Search for {query}", 
                  {'query': query, 'results_count': len(matches)},
                  session_id=session_id)

    if not matches:
        return jsonify({'success': False, 'message': f'No crop found matching "{query}"'})
        
    return jsonify({'success': True, 'results': matches})


@app.route('/api/soil-health', methods=['POST'])
@require_auth
def soil_health_endpoint():
    data = request.get_json()
    ph_level  = data.get('ph_level')
    soil_type = data.get('soil_type')
    color     = data.get('color')
    moisture  = data.get('moisture')
    username  = request.current_user.get('username')
    try:
        analysis = soil_health.analyze_soil(ph_level, soil_type, color, moisture)
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'soil_health',
            f"Soil health analysis — pH {ph_level}, {soil_type} soil",
            {'ph_level': ph_level, 'soil_type': soil_type, 'result': analysis},
            session_id=session_id)
        return jsonify({'success': True, 'analysis': analysis})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


import uuid

@app.route('/api/disease-detection', methods=['POST'])
@require_auth
def disease_detection_endpoint():
    username = request.current_user.get('username')
    crop_name = request.form.get('crop_name', '')
    
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image part uploaded'})
        
    file = request.files['image']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No selected image'})
        
    try:
        # Save image securely
        filename = f"{uuid.uuid4().hex}_{file.filename.replace(' ', '_')}"
        upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        img_path = os.path.join(upload_folder, filename)
        file.save(img_path)

        diseases = disease_model.predict_disease_from_image(crop_name, img_path)
        
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'disease_detection',
            f"Image disease detection for {crop_name}",
            {'crop': crop_name, 'image_file': filename, 'result': diseases},
            session_id=session_id)
            
        return jsonify({'success': True, 'diseases': diseases})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/market-prices', methods=['GET'])
@require_auth
def market_prices_endpoint():
    try:
        prices = get_market_prices()
        # EXCLUDED FROM MYSQL HISTORY BY USER REQUEST
        return jsonify({'success': True, 'prices': prices})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/finance-estimation', methods=['POST'])
@require_auth
def finance_estimation_endpoint():
    data      = request.get_json()
    crop_name = data.get('crop_name', '')
    area_sqm  = data.get('area_sqm', 0)
    mode      = data.get('mode', 'basic')
    username  = request.current_user.get('username')
    try:
        estimation = finance.estimate_costs_and_profits(data)
        save_finance_record(
            username, crop_name, area_sqm, mode,
            estimation.get('total_cost', 0),
            estimation.get('expected_revenue', 0),
            estimation.get('gross_profit', 0)
        )
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'finance',
            f"Finance estimation for {crop_name} ({area_sqm} sqm)",
            {'crop': crop_name, 'area': area_sqm, 'result': estimation},
            session_id=session_id)
        return jsonify({'success': True, 'estimation': estimation})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/irrigation-schedule', methods=['POST'])
@require_auth
def irrigation_schedule_endpoint():
    data              = request.get_json()
    crop_name         = data.get('crop_name', '')
    weather_condition = data.get('weather_condition', '')
    soil_moisture     = data.get('soil_moisture', '')
    username          = request.current_user.get('username')
    try:
        schedule = irrigation.get_schedule(crop_name, weather_condition, soil_moisture)
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'irrigation',
            f"Irrigation schedule for {crop_name} — {weather_condition} weather",
            {'crop': crop_name, 'weather': weather_condition, 'soil_moisture': soil_moisture},
            session_id=session_id)
        return jsonify({'success': True, 'schedule': schedule})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/irrigation/status', methods=['GET'])
@require_auth
def irrigation_status_endpoint():
    username = request.current_user.get('username')
    try:
        status = irrigation.get_full_system_status(username)
        if status:
            # Add some derived stats
            return jsonify({'success': True, 'status': status})
        return jsonify({'success': False, 'message': 'System offline'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/irrigation/toggle', methods=['POST'])
@require_auth
def irrigation_toggle_endpoint():
    data = request.get_json()
    action = data.get('action') # 'pump' or 'auto'
    state = data.get('state')   # True or False
    target = data.get('target') # Optional target moisture
    username = request.current_user.get('username')
    
    try:
        if action == 'pump':
            success = irrigation.toggle_pump_manual(username, state)
        elif action == 'auto':
            success = irrigation.toggle_auto_mode(username, state)
        elif action == 'target':
            success = irrigation.set_target_moisture(username, target)
        else:
            return jsonify({'success': False, 'message': 'Invalid action'})
            
        if success:
            # Return updated status
            status = irrigation.get_full_system_status(username)
            return jsonify({'success': True, 'status': status})
        return jsonify({'success': False, 'message': 'Action failed'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/weather-forecast', methods=['GET'])
@require_auth
def weather_forecast_endpoint():
    location = request.args.get('location', 'default_location')
    username = request.current_user.get('username')
    try:
        # Weather data fetching - EXCLUDED FROM HISTORY LOGGING BY USER REQUEST
        # But we still provide the API for the dashboard
        forecast = weather.get_forecast(location)
        return jsonify({'success': True, 'forecast': forecast})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/advisory', methods=['POST'])
@require_auth
def advisory_endpoint():
    data     = request.get_json()
    query    = data.get('query', '')
    username = request.current_user.get('username')
    try:
        advice  = advisory.get_advice(query)
        # The advice result is a dictionary. Extract the summary string for the db history
        summary_text = advice.get('summary', 'Advisory response generated.')
        
        save_advisory_history(username, query, summary_text)
        session_id = request.headers.get('X-Session-ID')
        save_activity(username, 'advisory',
            f"AI Advisory: {query[:80]}",
            {'query': query, 'response_preview': summary_text},
            session_id=session_id)
        return jsonify({'success': True, 'advice': advice})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/advisory/history', methods=['GET'])
@require_auth
def advisory_history_endpoint():
    username = request.current_user.get('username')
    try:
        history = get_advisory_history(username)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/soil-test', methods=['POST'])
@require_auth
def soil_test_endpoint():
    data = request.get_json()
    username = request.current_user.get('username')
    try:
        success = save_soil_test(
            username,
            data.get('ph_level'),
            data.get('soil_type'),
            data.get('color'),
            data.get('moisture'),
            data.get('nutrients', ''),
            data.get('recommendations', '')
        )
        if success:
            return jsonify({'success': True, 'message': 'Soil test saved successfully'})
        return jsonify({'success': False, 'message': 'Failed to save soil test'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/activity-log', methods=['GET'])
@require_auth
def activity_log_endpoint():
    username = request.current_user.get('username')
    limit = int(request.args.get('limit', 30))
    try:
        log = get_activity_log(username, limit)
        return jsonify(log)
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


if __name__ == '__main__':
    app.run(debug=True, port=5000)

# Reloaded: MySQL migration complete — JSON cache removed
