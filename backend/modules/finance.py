import json
import os

def load_finance_data():
    try:
        with open('backend/data/finance_data.json', 'r') as f:
            return json.load(f)
    except Exception:
        return {}
        
CROP_FINANCE_DATA = load_finance_data()

def estimate_costs_and_profits(data_payload, legacy_area=None):
    """
    Estimate farming costs and profits for a given crop and area, 
    accounting for 'detailed' mode parameters if provided.
    """
    if isinstance(data_payload, str):
        crop_name = data_payload
        area_sqm = legacy_area or 100
        mode = 'basic'
        data_payload = {}
    else:
        crop_name = data_payload.get('crop_name', 'Tomato')
        area_sqm = float(data_payload.get('area_sqm', 100))
        mode = data_payload.get('mode', 'basic')

    # Base costs per square meter
    base_costs = {
        'seeds': 2.0,  # per sqm
        'soil_preparation': 1.5,
        'fertilizer': 3.0,
        'pesticides': 1.0,
        'irrigation_setup': 2.5,
        'labor': 4.0,
        'miscellaneous': 1.0
    }

    # Load from the 1000 crop dataset dynamically
    crop_info = CROP_FINANCE_DATA.get(crop_name.lower().strip(), {
        'seed_cost_multiplier': 1.0, 'yield_per_sqm': 3.0, 'market_price_per_kg': 2.0, 'growing_period_months': 4, 'labor_multiplier': 1.0
    })

    costs_breakdown = {}
    total_cost = 0

    if mode == 'detailed':
        cost_fixed = float(data_payload.get('cost_fixed', 0))
        cost_variable = float(data_payload.get('cost_variable', 0))
        costs_breakdown['Manual Fixed Costs'] = cost_fixed
        costs_breakdown['Manual Variable Costs'] = cost_variable
        total_cost = cost_fixed + cost_variable
    else:
        for cost_type, base_cost in base_costs.items():
            if cost_type == 'seeds':
                cost = base_cost * crop_info['seed_cost_multiplier'] * area_sqm
            elif cost_type == 'labor':
                cost = base_cost * crop_info['labor_multiplier'] * area_sqm
            else:
                cost = base_cost * area_sqm

            costs_breakdown[cost_type] = round(cost, 2)
            total_cost += cost

    # Yield adjustments based on scenario
    yield_scenario = data_payload.get('yield_scenario', 'realistic') if mode == 'detailed' else 'realistic'
    yield_multiplier = 0.8
    if yield_scenario == 'optimistic': yield_multiplier = 1.0
    elif yield_scenario == 'pessimistic': yield_multiplier = 0.5
        
    expected_yield_kg = crop_info['yield_per_sqm'] * area_sqm * yield_multiplier
    
    # Target price override
    market_price_per_kg = crop_info['market_price_per_kg']
    if mode == 'detailed' and data_payload.get('target_price'):
        market_price_per_kg = float(data_payload['target_price'])

    expected_revenue = expected_yield_kg * market_price_per_kg
    gross_profit = expected_revenue - total_cost
    profit_margin = (gross_profit / total_cost * 100) if total_cost > 0 else 0
    roi = (gross_profit / total_cost * 100) if total_cost > 0 else 0

    months = crop_info['growing_period_months']
    monthly_cost = total_cost / months if months > 0 else 0
    monthly_revenue = expected_revenue / months if months > 0 else 0
    
    result = {
        'crop_name': crop_name,
        'area_sqm': area_sqm,
        'costs_breakdown': costs_breakdown,
        'total_cost': round(total_cost, 2),
        'expected_yield_kg': round(expected_yield_kg, 2),
        'market_price_per_kg': market_price_per_kg,
        'expected_revenue': round(expected_revenue, 2),
        'gross_profit': round(gross_profit, 2),
        'profit_margin_percent': round(profit_margin, 2),
        'roi_percent': round(roi, 2),
        'growing_period_months': months,
        'monthly_cost': round(monthly_cost, 2),
        'monthly_revenue': round(monthly_revenue, 2),
        'break_even_point': round(total_cost / market_price_per_kg, 2) if market_price_per_kg > 0 else 0
    }
    
    if mode == 'detailed':
        loan_amount = float(data_payload.get('loan_amount', 0))
        loan_interest = float(data_payload.get('loan_interest', 0))
        loan_duration = int(data_payload.get('loan_duration', 12))
        
        if loan_amount > 0 and loan_duration > 0:
            r = (loan_interest / 100) / 12
            n = loan_duration
            if r > 0:
                emi = loan_amount * r * ((1+r)**n) / (((1+r)**n) - 1)
            else:
                emi = loan_amount / n
            
            total_interest = (emi * n) - loan_amount
            result['monthly_emi'] = round(emi, 2)
            result['net_profit'] = round(gross_profit - total_interest, 2)
            
    return result

def get_finance_recommendations(crop_name, area_sqm, budget=None):
    """Get financial recommendations for farming."""
    estimation = estimate_costs_and_profits(crop_name, area_sqm)

    recommendations = []

    if estimation['profit_margin_percent'] > 50:
        recommendations.append("High profit potential - consider scaling up production")
    elif estimation['profit_margin_percent'] > 20:
        recommendations.append("Good profit potential - monitor costs carefully")
    else:
        recommendations.append("Low profit margin - consider cost optimization or alternative crops")

    if budget and estimation['total_cost'] > budget:
        excess = estimation['total_cost'] - budget
        recommendations.append(f"Budget exceeded by ${excess:.2f} - consider reducing area or finding cost savings")

    if estimation['growing_period_months'] > 5:
        recommendations.append("Long growing period - ensure adequate cash flow for extended investment")

    recommendations.append(f"Expected break-even yield: {estimation['break_even_point']} kg")

    return recommendations

def compare_crop_profitability(crop_list, area_sqm):
    """Compare profitability of different crops."""
    comparisons = []

    for crop in crop_list:
        estimation = estimate_costs_and_profits(crop, area_sqm)
        comparisons.append({
            'crop': crop,
            'total_cost': estimation['total_cost'],
            'expected_revenue': estimation['expected_revenue'],
            'gross_profit': estimation['gross_profit'],
            'profit_margin_percent': estimation['profit_margin_percent'],
            'roi_percent': estimation['roi_percent']
        })

    # Sort by profit margin
    comparisons.sort(key=lambda x: x['profit_margin_percent'], reverse=True)

    return comparisons