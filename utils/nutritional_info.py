"""
Nutritional information retrieval using Ollama API (Mistral model).
All values are per 100g of edible portion.
"""

import os
import json
from typing import Dict, Optional, List
import pickle
from pathlib import Path
import requests

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
    Get nutritional information for a specific fruit using Ollama API (Mistral model).
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
        # Prepare the prompt for Ollama
        prompt = f"""You are a nutrition expert. Provide detailed nutritional information for {fruit_name} per 100g of edible portion.
        Include:
        - Calories (kcal)
        - Protein (g)
        - Carbohydrates (g)
        - Fiber (g)
        - Key vitamins
        - Key minerals
        - Health benefits
        
        Format the response as a JSON object with these exact keys:
        {{
            "calories": number,
            "protein": "Xg",
            "carbs": "Xg",
            "fiber": "Xg",
            "vitamins": ["Vitamin A", "Vitamin C", etc],
            "minerals": ["Calcium", "Iron", etc],
            "benefits": ["Benefit 1", "Benefit 2", etc]
        }}
        """

        # Call Ollama API
        response = requests.post(
            'http://localhost:11435/api/generate',
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        
        # Parse the response
        result = json.loads(response.json()['response'])
        
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