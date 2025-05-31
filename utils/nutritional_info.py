"""
Nutritional information retrieval using Nutritionix API.
All values are per 100g of edible portion.
"""

import os
import json
from typing import Dict, Optional, List
import pickle
from pathlib import Path
import requests

# Nutritionix API credentials from environment variables
APP_ID = os.getenv('NUTRITIONIX_APP_ID')
API_KEY = os.getenv('NUTRITIONIX_API_KEY')

if not APP_ID or not API_KEY:
    raise ValueError("Please set NUTRITIONIX_APP_ID and NUTRITIONIX_API_KEY environment variables")

# Cache file path
CACHE_FILE = Path('utils/nutrition_cache.pkl')

# Load cache if it exists
nutrition_cache = {}
if CACHE_FILE.exists():
    try:
        with open(CACHE_FILE, 'rb') as f:
            nutrition_cache = pickle.load(f)
    except Exception as e:
        print(f"Error loading cache: {str(e)}")

def save_cache():
    """Save the cache to disk"""
    try:
        with open(CACHE_FILE, 'wb') as f:
            pickle.dump(nutrition_cache, f)
    except Exception as e:
        print(f"Error saving cache: {str(e)}")

def get_nutritional_info(fruit_name: str) -> Optional[Dict]:
    """
    Get nutritional information for a specific fruit using Nutritionix API.
    Uses caching to reduce API calls.
    
    Args:
        fruit_name (str): Name of the fruit in lowercase
        
    Returns:
        dict: Nutritional information for the fruit or None if not found
    """
    # Check cache first
    if fruit_name.lower() in nutrition_cache:
        return nutrition_cache[fruit_name.lower()]

    try:
        # Prepare the API request
        headers = {
            'x-app-id': APP_ID,
            'x-app-key': API_KEY,
            'Content-Type': 'application/json'
        }
        
        # Search for the fruit
        search_url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
        search_data = {
            "query": f"{fruit_name} raw"
        }
        
        response = requests.post(search_url, headers=headers, json=search_data)
        response.raise_for_status()
        nutrition_data = response.json()
        
        if not nutrition_data.get('foods'):
            return None
            
        # Get the first result
        food = nutrition_data['foods'][0]
        
        # Convert to our format
        result = {
            'calories': int(food.get('nf_calories', 0)),
            'protein': f"{food.get('nf_protein', 0)}g",
            'carbs': f"{food.get('nf_total_carbohydrate', 0)}g",
            'fiber': f"{food.get('nf_dietary_fiber', 0)}g",
            'vitamins': [],
            'minerals': [],
            'benefits': []
        }
        
        # Add vitamins and minerals based on available nutrients
        if food.get('nf_vitamin_a_dv'):
            result['vitamins'].append('Vitamin A')
        if food.get('nf_vitamin_c_dv'):
            result['vitamins'].append('Vitamin C')
        if food.get('nf_vitamin_d_dv'):
            result['vitamins'].append('Vitamin D')
        if food.get('nf_vitamin_e_dv'):
            result['vitamins'].append('Vitamin E')
        if food.get('nf_vitamin_k_dv'):
            result['vitamins'].append('Vitamin K')
        if food.get('nf_vitamin_b6_dv'):
            result['vitamins'].append('Vitamin B6')
        if food.get('nf_vitamin_b12_dv'):
            result['vitamins'].append('Vitamin B12')
            
        if food.get('nf_calcium_dv'):
            result['minerals'].append('Calcium')
        if food.get('nf_iron_dv'):
            result['minerals'].append('Iron')
        if food.get('nf_potassium_dv'):
            result['minerals'].append('Potassium')
        if food.get('nf_magnesium_dv'):
            result['minerals'].append('Magnesium')
        if food.get('nf_zinc_dv'):
            result['minerals'].append('Zinc')
        
        # Add benefits based on nutrients
        benefits = []
        
        # Add vitamin benefits
        if result['vitamins']:
            benefits.append(f"Rich in {', '.join(result['vitamins'])}")
            
        # Add mineral benefits
        if result['minerals']:
            benefits.append(f"Good source of {', '.join(result['minerals'])}")
            
        # Add fiber benefit
        fiber = food.get('nf_dietary_fiber', 0)
        if fiber > 2:
            benefits.append("High in fiber")
        elif fiber > 0:
            benefits.append("Contains fiber")
            
        # Add protein benefit
        protein = food.get('nf_protein', 0)
        if protein > 2:
            benefits.append("Good source of protein")
        elif protein > 0:
            benefits.append("Contains protein")
            
        # Add calorie benefit
        calories = food.get('nf_calories', 0)
        if calories < 50:
            benefits.append("Low in calories")
        elif calories < 100:
            benefits.append("Moderate in calories")
            
        # Add antioxidant benefit for fruits known to be high in antioxidants
        antioxidant_fruits = ['blueberry', 'strawberry', 'raspberry', 'pomegranate', 'grape']
        if fruit_name.lower() in antioxidant_fruits:
            benefits.append("High in antioxidants")
            
        # If no specific benefits were found, add a generic one
        if not benefits:
            benefits.append("Contains essential nutrients")
            
        result['benefits'] = benefits
        
        # Cache the result
        nutrition_cache[fruit_name.lower()] = result
        save_cache()
        return result

    except Exception as e:
        print(f"Error getting nutritional info for {fruit_name}: {str(e)}")
        # If API call fails, try to use cached data if available
        return nutrition_cache.get(fruit_name.lower())

def format_nutritional_info(fruit_name: str, info: Dict) -> str:
    """
    Format nutritional information for display (HTML).
    
    Args:
        fruit_name (str): Name of the fruit in lowercase
        info (dict): Nutritional information dictionary
        
    Returns:
        str: Formatted nutritional information
    """
    if not info:
        return f"No nutritional information available for {fruit_name}."
        
    formatted = f"Nutritional Information for {fruit_name.title()} (per 100g):<br>"
    formatted += f"<b>Calories:</b> {info['calories']} kcal<br>"
    formatted += f"<b>Protein:</b> {info['protein']}<br>"
    formatted += f"<b>Carbohydrates:</b> {info['carbs']}<br>"
    formatted += f"<b>Fiber:</b> {info['fiber']}<br>"
    formatted += f"<b>Vitamins:</b> {', '.join(info['vitamins']) if info['vitamins'] else 'None'}<br>"
    formatted += f"<b>Minerals:</b> {', '.join(info['minerals']) if info['minerals'] else 'None'}<br>"
    formatted += f"<b>Benefits:</b> {' • '.join(info['benefits'])}"
    return formatted