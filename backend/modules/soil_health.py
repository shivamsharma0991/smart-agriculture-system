def analyze_soil(ph_level, soil_type, color, moisture):
    """
    Analyze soil health based on pH level, soil type, color, and moisture.
    Returns analysis with health status, recommendations, and suitable crops.
    """
    analysis = {
        'ph_level': ph_level,
        'soil_type': soil_type,
        'color': color,
        'moisture': moisture,
        'health_status': '',
        'recommendations': [],
        'suitable_crops': [],
        'nutrient_needs': []
    }

    # Analyze pH level
    if ph_level:
        ph = float(ph_level)
        if ph < 6.0:
            analysis['health_status'] = 'Acidic soil'
            analysis['recommendations'].append('Add lime to raise pH level')
            analysis['suitable_crops'] = ['Potato', 'Rhubarb', 'Blueberry']
        elif 6.0 <= ph <= 7.5:
            analysis['health_status'] = 'Neutral to slightly alkaline'
            analysis['recommendations'].append('pH level is optimal for most crops')
            analysis['suitable_crops'] = ['Tomato', 'Pepper', 'Lettuce', 'Carrot']
        else:
            analysis['health_status'] = 'Alkaline soil'
            analysis['recommendations'].append('Add sulfur or organic matter to lower pH')
            analysis['suitable_crops'] = ['Spinach', 'Broccoli', 'Cabbage']

    # Analyze soil type
    if soil_type:
        soil_lower = soil_type.lower()
        if 'clay' in soil_lower:
            analysis['recommendations'].append('Improve drainage by adding organic matter')
            analysis['recommendations'].append('Avoid overwatering')
            analysis['nutrient_needs'].append('Good water retention but poor drainage')
        elif 'sand' in soil_lower:
            analysis['recommendations'].append('Add organic matter to improve water retention')
            analysis['recommendations'].append('Water more frequently')
            analysis['nutrient_needs'].append('Poor nutrient retention, needs frequent fertilization')
        elif 'loam' in soil_lower:
            analysis['recommendations'].append('Excellent soil type, maintain with organic matter')
            analysis['nutrient_needs'].append('Balanced nutrient retention')

    # Analyze soil color
    if color:
        color_lower = color.lower()
        if 'dark' in color_lower or 'black' in color_lower:
            analysis['nutrient_needs'].append('High organic matter content')
        elif 'red' in color_lower:
            analysis['nutrient_needs'].append('May indicate iron content, good for most crops')
        elif 'yellow' in color_lower or 'pale' in color_lower:
            analysis['nutrient_needs'].append('Low organic matter, needs amendment')
            analysis['recommendations'].append('Add compost or manure')

    # Analyze moisture
    if moisture:
        moisture_lower = moisture.lower()
        if 'low' in moisture_lower or 'dry' in moisture_lower:
            analysis['recommendations'].append('Increase watering frequency')
            analysis['recommendations'].append('Add mulch to retain moisture')
        elif 'high' in moisture_lower or 'wet' in moisture_lower:
            analysis['recommendations'].append('Improve drainage')
            analysis['recommendations'].append('Avoid overwatering')
        elif 'medium' in moisture_lower or 'moderate' in moisture_lower:
            analysis['recommendations'].append('Current moisture level is good')

    # Add general recommendations
    analysis['recommendations'].extend([
        'Test soil every 6 months',
        'Add organic matter annually',
        'Rotate crops to maintain soil health'
    ])

    # Remove duplicates
    analysis['recommendations'] = list(set(analysis['recommendations']))

    return analysis

def get_soil_amendments(ph_level, soil_type):
    """Get specific soil amendment recommendations."""
    amendments = []

    if ph_level:
        ph = float(ph_level)
        if ph < 6.0:
            amendments.append('Dolomite lime (6 lbs per 100 sq ft)')
            amendments.append('Wood ash (light application)')
        elif ph > 7.5:
            amendments.append('Elemental sulfur (5 lbs per 100 sq ft)')
            amendments.append('Aluminum sulfate')

    if soil_type and 'sand' in soil_type.lower():
        amendments.append('Organic compost (2-3 inches)')
        amendments.append('Well-aged manure')

    if soil_type and 'clay' in soil_type.lower():
        amendments.append('Gypsum (2 lbs per 100 sq ft)')
        amendments.append('Organic matter for better drainage')

    return amendments

def calculate_soil_quality_score(ph_level, soil_type, color, moisture):
    """Calculate a soil quality score from 0-100."""
    score = 50  # Base score

    # pH contribution
    if ph_level:
        ph = float(ph_level)
        if 6.0 <= ph <= 7.5:
            score += 20
        elif 5.5 <= ph < 6.0 or 7.5 < ph <= 8.0:
            score += 10
        else:
            score += 0

    # Soil type contribution
    if soil_type:
        if 'loam' in soil_type.lower():
            score += 15
        elif 'clay' in soil_type.lower() or 'sand' in soil_type.lower():
            score += 5

    # Color contribution (darker = better organic matter)
    if color:
        if 'dark' in color.lower() or 'black' in color.lower():
            score += 10
        elif 'brown' in color.lower():
            score += 5

    # Moisture contribution
    if moisture:
        if 'medium' in moisture.lower() or 'moderate' in moisture.lower():
            score += 5

    return min(100, max(0, score))