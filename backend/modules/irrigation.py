import json
import os

def load_irrigation_data():
    try:
        with open('backend/data/irrigation_data.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}

IRRIGATION_DATA = load_irrigation_data()

def get_schedule(crop_name, weather_condition, soil_moisture):
    """
    Get irrigation schedule recommendations based on crop, weather, and soil moisture.
    Returns detailed watering schedule and tips.
    """
    crop_info = IRRIGATION_DATA.get(crop_name.lower().strip(), {})
    base_level = crop_info.get('base_level', 'Moderate')
    
    level_map = {
        'Very High': 50,
        'High': 25,
        'Moderate': 20,
        'Low': 12
    }
    base_water = level_map.get(base_level, 20)

    # Weather adjustment factors
    weather_factors = {
        'sunny': 1.3,
        'hot': 1.4,
        'cloudy': 0.9,
        'rainy': 0.6,
        'windy': 1.2,
        'cool': 0.8,
        'moderate': 1.0
    }

    # Soil moisture adjustment
    moisture_factors = {
        'dry': 1.3,
        'low': 1.1,
        'medium': 1.0,
        'high': 0.8,
        'wet': 0.5
    }

    # Get base water need
    # Apply weather adjustment
    weather_factor = weather_factors.get(weather_condition.lower(), 1.0)
    adjusted_water = base_water * weather_factor

    # Apply soil moisture adjustment
    moisture_factor = moisture_factors.get(soil_moisture.lower(), 1.0)
    final_water = adjusted_water * moisture_factor

    # Calculate daily/weekly schedule
    if final_water > 40:  # Rice or very high needs
        frequency = "Daily flooding/maintenance"
        amount_per_session = f"{final_water/7:.1f} mm per day"
    elif final_water > 25:
        frequency = "3-4 times per week"
        amount_per_session = f"{final_water/3.5:.1f} mm per session"
    elif final_water > 18:
        frequency = "2-3 times per week"
        amount_per_session = f"{final_water/2.5:.1f} mm per session"
    elif final_water > 12:
        frequency = "2 times per week"
        amount_per_session = f"{final_water/2:.1f} mm per session"
    else:
        frequency = "1-2 times per week"
        amount_per_session = f"{final_water/1.5:.1f} mm per session"

    # Generate schedule
    schedule = {
        'crop_name': crop_name,
        'weather_condition': weather_condition,
        'soil_moisture': soil_moisture,
        'weekly_water_requirement_mm': round(final_water, 1),
        'frequency': frequency,
        'amount_per_session': amount_per_session,
        'best_time_to_water': get_best_watering_time(weather_condition),
        'watering_tips': get_watering_tips(crop_name, soil_moisture),
        'water_saving_tips': get_water_saving_tips(),
        'irrigation_method': recommend_irrigation_method(crop_name, final_water)
    }

    return schedule

def get_best_watering_time(weather_condition):
    """Get best time to water based on weather."""
    if weather_condition.lower() in ['hot', 'sunny']:
        return "Early morning (5-7 AM) or evening (6-8 PM) to minimize evaporation"
    elif weather_condition.lower() in ['cloudy', 'cool']:
        return "Morning (7-9 AM) when temperatures are moderate"
    elif weather_condition.lower() == 'rainy':
        return "Water only if soil is dry; avoid overwatering"
    else:
        return "Early morning (6-8 AM) for best absorption"

def get_watering_tips(crop_name, soil_moisture):
    """Get specific watering tips for crop and soil conditions."""
    tips = [
        "Water at soil level, not on leaves, to prevent fungal diseases",
        "Check soil moisture 2-3 inches deep before watering",
        "Use mulch to retain soil moisture and reduce evaporation"
    ]

    if soil_moisture.lower() in ['dry', 'low']:
        tips.append("Soil is dry - increase watering frequency")
        tips.append("Deep watering is better than frequent shallow watering")
    elif soil_moisture.lower() in ['high', 'wet']:
        tips.append("Reduce watering frequency to prevent root rot")
        tips.append("Ensure good drainage to avoid waterlogging")

    # Crop-specific tips
    crop_tips = {
        'Tomato': "Water consistently to prevent cracking; avoid wetting leaves",
        'Lettuce': "Keep soil consistently moist; bolt if water-stressed",
        'Rice': "Maintain flooded conditions during growing season",
        'Carrot': "Even moisture prevents cracking; avoid overwatering",
        'Spinach': "Regular watering prevents bitterness"
    }

    if crop_name in crop_tips:
        tips.append(crop_tips[crop_name])

    return tips

def get_water_saving_tips():
    """Get general water-saving tips."""
    return [
        "Use drip irrigation for efficient water delivery",
        "Water during cooler parts of the day to reduce evaporation",
        "Group plants with similar water needs together",
        "Apply mulch to reduce soil evaporation",
        "Use rain barrels to collect and reuse rainwater",
        "Install moisture sensors for automated watering",
        "Water deeply but less frequently to encourage deep roots"
    ]

def recommend_irrigation_method(crop_name, water_requirement):
    """Recommend irrigation method based on crop and water needs."""
    if water_requirement > 40:
        return "Flood irrigation or paddy field system"
    elif water_requirement > 25:
        return "Drip irrigation or soaker hoses"
    elif water_requirement > 15:
        return "Sprinkler system or drip irrigation"
    else:
        return "Drip irrigation or hand watering"

def calculate_water_efficiency(current_method, recommended_method):
    """Calculate water savings by switching irrigation methods."""
    efficiency_rates = {
        'flood': 0.6,
        'sprinkler': 0.75,
        'drip': 0.9,
        'hand_watering': 0.7
    }

    current_eff = efficiency_rates.get(current_method.lower().replace(' ', '_'), 0.7)
    recommended_eff = efficiency_rates.get(recommended_method.lower().replace(' ', '_'), 0.8)

    savings_percent = ((recommended_eff - current_eff) / current_eff) * 100

    return {
        'current_method': current_method,
        'recommended_method': recommended_method,
        'potential_savings_percent': round(savings_percent, 1),
        'efficiency_improvement': f"{recommended_eff * 100:.0f}% vs {current_eff * 100:.0f}%"
    }

def simulate_system_step(username):
    """
    Simulates a time step for the irrigation system.
    Adjusts current moisture based on pump state and weather.
    """
    from db import get_irrigation_status, update_irrigation_status, log_irrigation_event
    import random
    
    status = get_irrigation_status(username)
    if not status or not status['settings']:
        return None
    
    settings = status['settings']
    current_moisture = float(settings['current_moisture'])
    target_moisture = float(settings['target_moisture'])
    pump_state = bool(settings['pump_state'])
    auto_mode = bool(settings['auto_mode'])
    
    # 1. Simulate Moisture Change
    if pump_state:
        # Increase moisture if watering
        change = random.uniform(2.0, 5.0)
        new_moisture = min(100.0, current_moisture + change)
        water_added = random.uniform(0.5, 1.2) # Liters
        update_irrigation_status(username, current_moisture=new_moisture, add_water=water_added)
        current_moisture = new_moisture
    else:
        # Decrease moisture (evaporation)
        change = random.uniform(0.1, 0.4)
        new_moisture = max(0.0, current_moisture - change)
        update_irrigation_status(username, current_moisture=new_moisture)
        current_moisture = new_moisture

    # 2. Auto-Irrigation Logic
    if auto_mode:
        if not pump_state and current_moisture < (target_moisture - 5):
            # Start pump
            update_irrigation_status(username, pump_state=1)
            log_irrigation_event(username, "Auto-Start: Moisture low", source='auto')
        elif pump_state and current_moisture > target_moisture:
            # Stop pump
            update_irrigation_status(username, pump_state=0)
            log_irrigation_event(username, "Auto-Stop: Target reached", source='auto')

    # Re-fetch updated status
    return get_irrigation_status(username)

def get_full_system_status(username):
    """Get the current state of variables and history."""
    return simulate_system_step(username)

def toggle_pump_manual(username, state):
    """Turn pump on or off manually."""
    from db import get_irrigation_status, update_irrigation_status, log_irrigation_event
    status = get_irrigation_status(username)
    if not status or not status['settings']:
        return False
        
    current_state = bool(status['settings']['pump_state'])
    
    if current_state != state:
        update_irrigation_status(username, pump_state=1 if state else 0)
        action = "Pump Started" if state else "Pump Stopped"
        log_irrigation_event(username, action, source='manual')
        return True
    return False

def toggle_auto_mode(username, state):
    """Toggle auto-irrigation mode."""
    from db import update_irrigation_status, log_irrigation_event
    update_irrigation_status(username, auto_mode=1 if state else 0)
    action = "Auto-Mode Enabled" if state else "Auto-Mode Disabled"
    log_irrigation_event(username, action, source='manual')
    return True

def set_target_moisture(username, target):
    """Set the target moisture level."""
    from db import update_irrigation_status
    return update_irrigation_status(username, target_moisture=target)