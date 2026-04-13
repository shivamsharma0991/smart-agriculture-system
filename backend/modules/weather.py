import requests
import json
from datetime import datetime, timedelta

def get_forecast(location):
    """
    Get weather forecast for farming decisions.
    Returns weather data with farming recommendations.
    """
    # Mock weather data (in production, use real weather API)
    mock_weather_data = {
        'location': location,
        'current': {
            'temperature': 25,
            'humidity': 65,
            'wind_speed': 10,
            'condition': 'Partly cloudy',
            'precipitation_chance': 20
        },
        'forecast': [
            {
                'date': (datetime.now() + timedelta(days=i)).strftime('%Y-%m-%d'),
                'temperature_max': 28 + i,
                'temperature_min': 18 + i,
                'humidity': 60 + (i * 5),
                'condition': ['Sunny', 'Cloudy', 'Rainy', 'Partly cloudy'][i % 4],
                'precipitation_chance': [10, 30, 80, 20][i % 4],
                'wind_speed': 8 + (i * 2)
            } for i in range(7)
        ]
    }

    # Add farming recommendations based on weather
    recommendations = generate_farming_recommendations(mock_weather_data)

    return {
        'weather_data': mock_weather_data,
        'farming_recommendations': recommendations,
        'alerts': check_weather_alerts(mock_weather_data)
    }

def generate_farming_recommendations(weather_data):
    """Generate farming recommendations based on weather conditions."""
    recommendations = []
    current = weather_data['current']
    forecast = weather_data['forecast']

    # Temperature-based recommendations
    if current['temperature'] > 35:
        recommendations.append("High temperature alert: Provide shade for heat-sensitive crops")
        recommendations.append("Increase irrigation frequency")
    elif current['temperature'] < 10:
        recommendations.append("Cold weather: Protect frost-sensitive plants")
        recommendations.append("Delay planting cold-sensitive crops")

    # Humidity recommendations
    if current['humidity'] > 80:
        recommendations.append("High humidity: Monitor for fungal diseases")
        recommendations.append("Improve air circulation around plants")
    elif current['humidity'] < 40:
        recommendations.append("Low humidity: Increase watering frequency")

    # Precipitation forecast
    upcoming_rain = any(day['precipitation_chance'] > 60 for day in forecast[:3])
    if upcoming_rain:
        recommendations.append("Rain expected: Reduce irrigation to prevent waterlogging")
        recommendations.append("Prepare drainage systems")
    else:
        recommendations.append("Dry spell expected: Plan supplemental irrigation")

    # Wind recommendations
    if current['wind_speed'] > 20:
        recommendations.append("Strong winds: Stake tall plants and protect seedlings")

    # Seasonal recommendations
    current_month = datetime.now().month
    if current_month in [3, 4, 5]:  # Spring
        recommendations.append("Spring planting season: Good time for starting seeds indoors")
    elif current_month in [6, 7, 8]:  # Summer
        recommendations.append("Summer: Focus on pest control and adequate watering")
    elif current_month in [9, 10, 11]:  # Fall
        recommendations.append("Fall harvest season: Monitor for early frosts")
    elif current_month in [12, 1, 2]:  # Winter
        recommendations.append("Winter: Plan for spring planting and protect crops from cold")

    return recommendations

def check_weather_alerts(weather_data):
    """Check for weather alerts that could affect farming."""
    alerts = []
    current = weather_data['current']
    forecast = weather_data['forecast']

    # Extreme temperature alerts
    if current['temperature'] > 40:
        alerts.append({
            'type': 'extreme_heat',
            'severity': 'high',
            'message': 'Extreme heat may damage crops. Provide immediate shade and watering.'
        })
    elif current['temperature'] < 5:
        alerts.append({
            'type': 'frost_warning',
            'severity': 'high',
            'message': 'Frost risk detected. Protect sensitive plants immediately.'
        })

    # Heavy rain alerts
    heavy_rain_days = [day for day in forecast[:3] if day['precipitation_chance'] > 70]
    if heavy_rain_days:
        alerts.append({
            'type': 'heavy_rain',
            'severity': 'medium',
            'message': f'Heavy rain expected in {len(heavy_rain_days)} days. Prepare drainage systems.'
        })

    # Drought alerts
    dry_spell = all(day['precipitation_chance'] < 20 for day in forecast[:5])
    if dry_spell:
        alerts.append({
            'type': 'drought_risk',
            'severity': 'medium',
            'message': 'Extended dry period expected. Plan irrigation accordingly.'
        })

    return alerts

def get_optimal_planting_time(crop_name, location):
    """Get optimal planting times based on crop and location."""
    # Mock planting calendar
    planting_times = {
        'Tomato': {
            'spring': 'March-April',
            'summer': 'May-June',
            'fall': 'August-September'
        },
        'Lettuce': {
            'spring': 'February-April',
            'fall': 'August-October',
            'winter': 'November-December (protected)'
        },
        'Carrot': {
            'spring': 'March-May',
            'fall': 'July-August',
            'winter': 'Not recommended'
        },
        'Spinach': {
            'spring': 'March-April',
            'fall': 'September-October',
            'winter': 'November-December'
        },
        'Pepper': {
            'spring': 'April-May',
            'summer': 'May-June',
            'fall': 'Not recommended'
        }
    }

    crop_times = planting_times.get(crop_name, {
        'spring': 'March-May',
        'summer': 'May-July',
        'fall': 'August-September'
    })

    return {
        'crop': crop_name,
        'location': location,
        'optimal_planting_times': crop_times,
        'current_season': get_current_season(),
        'recommendation': f"Best planting time for {crop_name} in {location} is {crop_times.get(get_current_season(), 'spring')}"
    }

def get_current_season():
    """Get current season based on month."""
    month = datetime.now().month
    if month in [3, 4, 5]:
        return 'spring'
    elif month in [6, 7, 8]:
        return 'summer'
    elif month in [9, 10, 11]:
        return 'fall'
    else:
        return 'winter'

def get_weather_impact_on_crops(weather_data):
    """Analyze weather impact on different crop types."""
    impacts = {
        'leafy_greens': analyze_crop_type_impact(weather_data, 'leafy'),
        'root_vegetables': analyze_crop_type_impact(weather_data, 'root'),
        'fruiting_crops': analyze_crop_type_impact(weather_data, 'fruit'),
        'grains': analyze_crop_type_impact(weather_data, 'grain')
    }

    return impacts

def analyze_crop_type_impact(weather_data, crop_type):
    """Analyze weather impact on specific crop type."""
    current = weather_data['current']

    if crop_type == 'leafy':
        if current['temperature'] > 30:
            return {'impact': 'negative', 'reason': 'Bolting risk increases'}
        elif current['humidity'] > 70:
            return {'impact': 'negative', 'reason': 'Disease risk increases'}
        else:
            return {'impact': 'positive', 'reason': 'Optimal growing conditions'}

    elif crop_type == 'root':
        if current['temperature'] > 25:
            return {'impact': 'negative', 'reason': 'Roots may become woody'}
        elif current['precipitation_chance'] > 50:
            return {'impact': 'negative', 'reason': 'Excess moisture may cause rot'}
        else:
            return {'impact': 'positive', 'reason': 'Good root development conditions'}

    elif crop_type == 'fruit':
        if current['wind_speed'] > 15:
            return {'impact': 'negative', 'reason': 'Fruit damage from wind'}
        elif current['humidity'] < 50:
            return {'impact': 'negative', 'reason': 'Poor fruit set conditions'}
        else:
            return {'impact': 'positive', 'reason': 'Good fruit development conditions'}

    elif crop_type == 'grain':
        if current['precipitation_chance'] < 30:
            return {'impact': 'negative', 'reason': 'Pollination may be affected'}
        elif current['temperature'] > 35:
            return {'impact': 'negative', 'reason': 'Heat stress during grain fill'}
        else:
            return {'impact': 'positive', 'reason': 'Good grain development conditions'}

    return {'impact': 'neutral', 'reason': 'Conditions within normal range'}
