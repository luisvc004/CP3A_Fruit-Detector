"""
Nutritional information for different fruits.
All values are per 100g of edible portion.
"""

FRUIT_NUTRITION = {
    'apple': {
        'calories': 52,
        'protein': '0.3g',
        'carbs': '13.8g',
        'fiber': '2.4g',
        'vitamins': ['Vitamin C', 'Vitamin B6'],
        'minerals': ['Potassium'],
        'benefits': 'Rich in antioxidants and fiber, helps with digestion and heart health'
    },
    'banana': {
        'calories': 89,
        'protein': '1.1g',
        'carbs': '22.8g',
        'fiber': '2.6g',
        'vitamins': ['Vitamin B6', 'Vitamin C'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'Good source of energy, helps with muscle function and blood pressure'
    },
    'orange': {
        'calories': 47,
        'protein': '0.9g',
        'carbs': '11.8g',
        'fiber': '2.4g',
        'vitamins': ['Vitamin C', 'Vitamin A'],
        'minerals': ['Calcium', 'Potassium'],
        'benefits': 'Excellent source of Vitamin C, boosts immune system'
    },
    'strawberry': {
        'calories': 32,
        'protein': '0.7g',
        'carbs': '7.7g',
        'fiber': '2.0g',
        'vitamins': ['Vitamin C', 'Folate'],
        'minerals': ['Manganese', 'Potassium'],
        'benefits': 'High in antioxidants, supports heart health and skin health'
    },
    'grape': {
        'calories': 69,
        'protein': '0.6g',
        'carbs': '18.1g',
        'fiber': '0.9g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Copper', 'Potassium'],
        'benefits': 'Contains resveratrol, good for heart health'
    },
    'watermelon': {
        'calories': 30,
        'protein': '0.6g',
        'carbs': '7.6g',
        'fiber': '0.4g',
        'vitamins': ['Vitamin A', 'Vitamin C'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'High water content, helps with hydration and contains lycopene'
    },
    'pineapple': {
        'calories': 50,
        'protein': '0.5g',
        'carbs': '13.1g',
        'fiber': '1.4g',
        'vitamins': ['Vitamin C', 'Vitamin B6'],
        'minerals': ['Manganese', 'Copper'],
        'benefits': 'Contains bromelain, helps with digestion and inflammation'
    },
    'mango': {
        'calories': 60,
        'protein': '0.8g',
        'carbs': '15.0g',
        'fiber': '1.6g',
        'vitamins': ['Vitamin A', 'Vitamin C'],
        'minerals': ['Potassium', 'Copper'],
        'benefits': 'Rich in Vitamin A, good for eye health and immune system'
    },
    'pear': {
        'calories': 57,
        'protein': '0.4g',
        'carbs': '15.2g',
        'fiber': '3.1g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Potassium', 'Copper'],
        'benefits': 'High in fiber, supports digestive health and immune system'
    },
    'peach': {
        'calories': 39,
        'protein': '0.9g',
        'carbs': '9.5g',
        'fiber': '1.5g',
        'vitamins': ['Vitamin C', 'Vitamin A'],
        'minerals': ['Potassium'],
        'benefits': 'Good for skin health and hydration'
    },
    'cherry': {
        'calories': 50,
        'protein': '1.0g',
        'carbs': '12.2g',
        'fiber': '1.6g',
        'vitamins': ['Vitamin C', 'Vitamin A'],
        'minerals': ['Potassium'],
        'benefits': 'Rich in antioxidants, helps reduce inflammation'
    },
    'kiwi': {
        'calories': 41,
        'protein': '0.8g',
        'carbs': '10.1g',
        'fiber': '2.1g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'Boosts immune system, aids digestion'
    },
    'lemon': {
        'calories': 29,
        'protein': '1.1g',
        'carbs': '9.3g',
        'fiber': '2.8g',
        'vitamins': ['Vitamin C', 'Vitamin B6'],
        'minerals': ['Potassium'],
        'benefits': 'Excellent source of Vitamin C, supports immune function'
    },
    'blueberry': {
        'calories': 57,
        'protein': '0.7g',
        'carbs': '14.5g',
        'fiber': '2.4g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Manganese'],
        'benefits': 'High in antioxidants, supports brain health'
    },
    'plum': {
        'calories': 46,
        'protein': '0.7g',
        'carbs': '11.4g',
        'fiber': '1.4g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Potassium', 'Copper'],
        'benefits': 'Good for digestion and bone health'
    },
    'avocado': {
        'calories': 160,
        'protein': '2.0g',
        'carbs': '8.5g',
        'fiber': '6.7g',
        'vitamins': ['Vitamin K', 'Vitamin E', 'Vitamin C'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'Rich in healthy fats, supports heart health'
    },
    'papaya': {
        'calories': 43,
        'protein': '0.5g',
        'carbs': '10.8g',
        'fiber': '1.7g',
        'vitamins': ['Vitamin C', 'Vitamin A'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'Aids digestion, supports immune system'
    },
    'pomegranate': {
        'calories': 83,
        'protein': '1.7g',
        'carbs': '18.7g',
        'fiber': '4.0g',
        'vitamins': ['Vitamin C', 'Vitamin K', 'Folate'],
        'minerals': ['Potassium'],
        'benefits': 'Rich in antioxidants, supports heart health'
    },
    'fig': {
        'calories': 74,
        'protein': '0.8g',
        'carbs': '19.2g',
        'fiber': '2.9g',
        'vitamins': ['Vitamin B6', 'Vitamin K'],
        'minerals': ['Potassium', 'Magnesium'],
        'benefits': 'Good for digestion and bone health'
    },
    'melon': {
        'calories': 34,
        'protein': '0.8g',
        'carbs': '8.2g',
        'fiber': '0.9g',
        'vitamins': ['Vitamin C', 'Vitamin A'],
        'minerals': ['Potassium'],
        'benefits': 'Hydrating, supports immune system'
    },
    'apricot': {
        'calories': 48,
        'protein': '1.4g',
        'carbs': '11.1g',
        'fiber': '2.0g',
        'vitamins': ['Vitamin A', 'Vitamin C'],
        'minerals': ['Potassium'],
        'benefits': 'Good for skin and eye health'
    },
    'raspberry': {
        'calories': 52,
        'protein': '1.2g',
        'carbs': '11.9g',
        'fiber': '6.5g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Manganese'],
        'benefits': 'High in fiber and antioxidants'
    },
    'blackberry': {
        'calories': 43,
        'protein': '1.4g',
        'carbs': '9.6g',
        'fiber': '5.3g',
        'vitamins': ['Vitamin C', 'Vitamin K'],
        'minerals': ['Manganese'],
        'benefits': 'Supports brain and oral health'
    },
    'coconut': {
        'calories': 354,
        'protein': '3.3g',
        'carbs': '15.2g',
        'fiber': '9.0g',
        'vitamins': ['Vitamin C', 'Folate'],
        'minerals': ['Manganese', 'Copper'],
        'benefits': 'Rich in healthy fats, supports metabolism'
    },
    'lime': {
        'calories': 30,
        'protein': '0.7g',
        'carbs': '10.5g',
        'fiber': '2.8g',
        'vitamins': ['Vitamin C', 'Vitamin B6'],
        'minerals': ['Potassium'],
        'benefits': 'Boosts immunity, aids iron absorption'
    },
}

def get_nutritional_info(fruit_name):
    """
    Get nutritional information for a specific fruit.
    
    Args:
        fruit_name (str): Name of the fruit in lowercase
        
    Returns:
        dict: Nutritional information for the fruit or None if not found
    """
    return FRUIT_NUTRITION.get(fruit_name.lower())

def format_nutritional_info(fruit_name, info):
    """
    Format nutritional information for display (HTML).
    
    Args:
        fruit_name (str): Name of the fruit in lowercase
        info (dict): Nutritional information dictionary
        
    Returns:
        str: Formatted nutritional information
    """
    formatted = f"Nutritional Information for {fruit_name.title()} (per 100g):<br>"
    formatted += f"<b>Calories:</b> {info['calories']} kcal<br>"
    formatted += f"<b>Protein:</b> {info['protein']}<br>"
    formatted += f"<b>Carbohydrates:</b> {info['carbs']}<br>"
    formatted += f"<b>Fiber:</b> {info['fiber']}<br>"
    formatted += f"<b>Vitamins:</b> {', '.join(info['vitamins'])}<br>"
    formatted += f"<b>Minerals:</b> {', '.join(info['minerals'])}<br>"
    formatted += f"<b>Benefits:</b> {info['benefits']}"
    return formatted 