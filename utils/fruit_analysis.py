import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List
import requests
import json
import os

@dataclass
class FruitQuality:
    ripeness_level: float  # 0-1 scale
    quality_score: float   # 0-1 scale
    defects: List[str]
    recommendations: List[str]
    estimated_weight: float  # in grams

class FruitAnalyzer:
    def __init__(self):
        # Define the environment variable name for the Ollama API base URL
        self.OLLAMA_API_BASE_URL = os.getenv('OLLAMA_API_BASE_URL', 'http://localhost:11434')
        
        # Keep the color ranges for basic ripeness detection
        self.color_ranges = {
            'apple': {
                'green': [(35, 50, 50), (85, 255, 255)],    # HSV ranges
                'red': [(0, 50, 50), (10, 255, 255)],
                'yellow': [(20, 50, 50), (35, 255, 255)]
            },
            'banana': {
                'green': [(35, 50, 50), (85, 255, 255)],
                'yellow': [(20, 50, 50), (35, 255, 255)],
                'brown': [(10, 50, 50), (20, 255, 255)]
            },
            'orange': {
                'green': [(35, 50, 50), (85, 255, 255)],
                'orange': [(10, 50, 50), (25, 255, 255)],
                'yellow': [(20, 50, 50), (35, 255, 255)]
            },
            'strawberry': {
                'green': [(35, 50, 50), (85, 255, 255)],
                'red': [(0, 50, 50), (10, 255, 255)],
                'pink': [(150, 50, 50), (180, 255, 255)]
            },
            'grape': {
                'green': [(35, 50, 50), (85, 255, 255)],
                'purple': [(130, 50, 50), (170, 255, 255)],
                'red': [(0, 50, 50), (10, 255, 255)]
            },
            'pomegranate': {
                'red': [(0, 50, 50), (10, 255, 255)],
                'pink': [(150, 50, 50), (180, 255, 255)],
                'brown': [(10, 50, 50), (20, 255, 255)]
            }
        }

    def analyze_fruit(self, image: np.ndarray, bbox: Tuple[int, int, int, int], fruit_type: str) -> FruitQuality:
        """Analyze the quality and ripeness of a fruit in the given bounding box."""
        x1, y1, x2, y2 = bbox
        fruit_roi = image[y1:y2, x1:x2]
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(fruit_roi, cv2.COLOR_BGR2HSV)
        
        # Get basic ripeness from color analysis
        ripeness = self._analyze_ripeness(hsv, fruit_type)
        
        # Get detailed analysis from Ollama
        analysis = self._get_ollama_analysis(fruit_type, ripeness)
        
        # Estimate weight
        estimated_weight = self.estimate_weight(bbox, fruit_type)
        
        return FruitQuality(
            ripeness_level=ripeness,
            quality_score=analysis['quality_score'],
            defects=analysis['defects'],
            recommendations=analysis['recommendations'],
            estimated_weight=estimated_weight
        )

    def _analyze_ripeness(self, hsv: np.ndarray, fruit_type: str) -> float:
        """Analyze the ripeness level based on color."""
        if fruit_type.lower() not in self.color_ranges:
            return 0.5  # Default middle value if fruit type not known
            
        color_ranges = self.color_ranges[fruit_type.lower()]
        ripeness_scores = []
        
        for color, (lower, upper) in color_ranges.items():
            mask = cv2.inRange(hsv, np.array(lower), np.array(upper))
            percentage = np.sum(mask > 0) / (mask.shape[0] * mask.shape[1])
            ripeness_scores.append(percentage)
            
        # Weight the scores based on color importance
        if fruit_type.lower() == 'banana':
            weights = [0.2, 0.6, 0.2]  # green, yellow, brown
        elif fruit_type.lower() == 'orange':
            weights = [0.1, 0.7, 0.2]  # green, orange, yellow
        elif fruit_type.lower() == 'strawberry':
            weights = [0.1, 0.7, 0.2]  # green, red, pink
        elif fruit_type.lower() == 'grape':
            weights = [0.2, 0.6, 0.2]  # green, purple, red
        elif fruit_type.lower() == 'pomegranate':
            weights = [0.6, 0.3, 0.1]  # red, pink, brown
        else:
            weights = [0.3, 0.4, 0.3]  # default weights
            
        return np.average(ripeness_scores, weights=weights)

    def _get_ollama_analysis(self, fruit_type: str, ripeness: float) -> Dict:
        """Get detailed fruit analysis from Ollama."""
        try:
            # Prepare the prompt for Ollama
            prompt = f"""You are a fruit quality expert. Analyze a {fruit_type} with a ripeness level of {ripeness:.2f} (0-1 scale, where 1 is fully ripe).
            Provide a detailed analysis including:
            - Quality score (0-1 scale)
            - Potential defects based on ripeness level
            - Specific recommendations for consumption and storage
            
            Format the response as a JSON object with these exact keys:
            {{
                "quality_score": number between 0 and 1,
                "defects": ["defect1", "defect2", etc],
                "recommendations": ["recommendation1", "recommendation2", etc]
            }}
            """

            # Call Ollama API
            response = requests.post(
                f'{self.OLLAMA_API_BASE_URL}/api/generate',
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False
                }
            )
            response.raise_for_status()
            
            # Parse the response
            result = json.loads(response.json()['response'])
            return result

        except Exception as e:
            print(f"Error getting Ollama analysis for {fruit_type}: {str(e)}")
            # Return default values if API call fails
            return {
                "quality_score": ripeness,
                "defects": [],
                "recommendations": ["Unable to generate specific recommendations"]
            }

    def estimate_weight(self, bbox: Tuple[int, int, int, int], fruit_type: str) -> float:
        """Estimate the weight of the fruit based on its size."""
        x1, y1, x2, y2 = bbox
        area = (x2 - x1) * (y2 - y1)
        
        # Approximate weight based on area (these are rough estimates)
        weight_factors = {
            'apple': 0.0001,    # grams per pixel
            'banana': 0.00008,
            'orange': 0.00012,
            'strawberry': 0.00005,
            'grape': 0.00003,
            'pomegranate': 0.00015,
            'default': 0.0001
        }
        
        factor = weight_factors.get(fruit_type.lower(), weight_factors['default'])
        return area * factor