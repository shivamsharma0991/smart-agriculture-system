import os
import json
import cv2
import numpy as np

def predict_disease_from_image(crop_name, image_path):
    """
    CNN Architecture Stub:
    This function currently simulates a CNN model using OpenCV computer vision.
    When a PyTorch (.pt) or TensorFlow (.h5) model is ready, drop it here.
    """
    if not os.path.exists(image_path):
        return _fallback_predict(crop_name, "Image not found.")

    # 1. Image Loading (Simulating Data Loader)
    img = cv2.imread(image_path)
    if img is None:
        return _fallback_predict(crop_name, "Invalid image format.")

    # 2. Preprocessing (Standard CNN resize - e.g., ResNet/MobileNet)
    input_size = (224, 224)
    img_resized = cv2.resize(img, input_size)
    
    # 3. Dummy Feature Extraction (Simulating Convolutional Layers)
    # We analyze the HSV color space to look for damage (yellowing/browning/spots)
    hsv = cv2.cvtColor(img_resized, cv2.COLOR_BGR2HSV)
    
    # Healthy Green Range
    lower_green = np.array([35, 40, 40])
    upper_green = np.array([85, 255, 255])
    green_mask = cv2.inRange(hsv, lower_green, upper_green)
    green_ratio = cv2.countNonZero(green_mask) / (input_size[0] * input_size[1])

    # Yellow/Brown (Damage) Range
    lower_damage = np.array([10, 40, 40])
    upper_damage = np.array([35, 255, 255])
    damage_mask = cv2.inRange(hsv, lower_damage, upper_damage)
    damage_ratio = cv2.countNonZero(damage_mask) / (input_size[0] * input_size[1])

    # 4. Inference Mapping
    # Based on the simulated visual features, generate structural symptom keywords
    synthetic_symptoms = []
    
    if damage_ratio > 0.3:
        synthetic_symptoms.extend(["blight", "rot", "severe damage", "brown", "dead"])
    elif damage_ratio > 0.1:
        synthetic_symptoms.extend(["yellowing", "spots", "deficiency", "mildew"])
    elif green_ratio > 0.5:
        synthetic_symptoms.extend(["healthy", "minor issues", "aphid"]) # Healthy plants mostly get pests if anything
    else:
        synthetic_symptoms.extend(["discolored", "stunted", "powdery"])
        
    keyword_string = " ".join(synthetic_symptoms)
    
    print(f"CNN CV Analysis for {crop_name}: Green Ratio={green_ratio:.2f}, Damage Ratio={damage_ratio:.2f} -> {keyword_string}")

    return _fallback_predict(crop_name, keyword_string)


def _fallback_predict(crop_name, symptoms):
    """Keyword-based DB mapping."""
    symptoms_lower = symptoms.lower()
    crop_lower = crop_name.lower()

    try:
        with open('backend/data/disease_data.json', 'r') as f:
            generated_diseases = json.load(f)
    except Exception:
        generated_diseases = {}
        
    DISEASE_DB = [
        {
            'disease': 'Powdery Mildew', 'crop': 'General',
            'keywords': ['white', 'powdery', 'coating', 'mildew'],
            'treatment': 'Spray with diluted baking soda solution',
            'prevention': 'Improve air circulation; reduce humidity'
        },
        {
            'disease': 'Root Rot', 'crop': 'General',
            'keywords': ['rot', 'soft', 'base', 'smell', 'odor'],
            'treatment': 'Improve drainage; reduce watering frequency',
            'prevention': 'Never let roots sit in waterlogged soil'
        },
        {
            'disease': 'Aphid Infestation', 'crop': 'General',
            'keywords': ['curling', 'sticky', 'small insects', 'aphid', 'healthy'],
            'treatment': 'Blast with water; apply insecticidal soap',
            'prevention': 'Encourage ladybugs; avoid excess nitrogen fertilizer'
        },
        {
            'disease': 'Nutrient Deficiency', 'crop': 'General',
            'keywords': ['yellow', 'pale', 'stunted', 'discolored', 'yellowing'],
            'treatment': 'Test soil; apply balanced fertilizer',
            'prevention': 'Regular soil testing and amendment'
        },
        {
            'disease': 'Blight / Burn', 'crop': 'General',
            'keywords': ['blight', 'dead', 'brown', 'severe damage'],
            'treatment': 'Remove affected parts immediately. Apply fungicide.',
            'prevention': 'Avoid overhead watering.'
        }
    ]
    
    # Append the dynamically generated databases if available
    if crop_lower in generated_diseases:
        for dg in generated_diseases[crop_lower]:
            DISEASE_DB.append({
                'disease': dg['disease'],
                'crop': crop_name,
                'keywords': [dg['disease'].lower().split(' ')[-1], 'spots', 'wilting', 'yellowing', 'blight', 'rot'],
                'treatment': dg['treatment'],
                'prevention': 'Regular monitoring and environmental control'
            })

    results = []
    for entry in DISEASE_DB:
        if entry['crop'] not in ('General', crop_name):
            continue
        matches = sum(1 for kw in entry['keywords'] if kw in symptoms_lower)
        if matches > 0:
            confidence = min(98, 50 + matches * 18)
            results.append({
                'rank': len(results) + 1,
                'disease': entry['disease'],
                'confidence': confidence,
                'crop': entry['crop'] if entry['crop'] != 'General' else crop_name,
                'symptoms': "Visual match (image analysis)",
                'treatment': entry['treatment'],
                'prevention': entry['prevention']
            })

    if not results:
        results = [{
            'rank': 1,
            'disease': 'Unknown physical condition',
            'confidence': 45,
            'crop': crop_name,
            'symptoms': "Unidentified visual anomalies",
            'treatment': 'Consult a local agricultural extension service',
            'prevention': 'Practice regular plant monitoring and good hygiene',
        }]

    results.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Deduplicate by disease name
    seen = set()
    final_results = []
    for r in results:
        if r['disease'] not in seen:
            seen.add(r['disease'])
            final_results.append(r)
            
    for i, r in enumerate(final_results[:3], 1):
        r['rank'] = i
        
    return final_results[:3]

class _DiseaseModelShim:
    def predict_disease_from_image(self, crop_name, image_path):
        return predict_disease_from_image(crop_name, image_path)

disease_model = _DiseaseModelShim()
