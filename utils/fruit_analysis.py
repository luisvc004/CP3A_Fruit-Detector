import cv2
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, List

@dataclass
class FruitQuality:
    ripeness_level: float  # 0-1 scale
    quality_score: float   # 0-1 scale
    defects: List[str]
    recommendations: List[str]
    estimated_weight: float  # in grams

class FruitAnalyzer:
    def __init__(self):
        # Define color ranges for different ripeness levels
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
        
        # Adjusted defect patterns with more specific color ranges and higher thresholds
        self.defect_patterns = {
            'bruise': {
                'color': [(0, 0, 0), (180, 50, 50)],  # Darker areas
                'min_area': 100,  # Increased minimum area
                'threshold': 0.15  # Minimum percentage of area
            },
            'mold': {
                'color': [(0, 0, 0), (180, 30, 30)],  # Very dark areas
                'min_area': 50,
                'threshold': 0.05
            },
            'rot': {
                'color': [(0, 0, 0), (180, 40, 40)],  # Dark areas
                'min_area': 75,
                'threshold': 0.10
            }
        }

    def analyze_fruit(self, image: np.ndarray, bbox: Tuple[int, int, int, int], fruit_type: str) -> FruitQuality:
        """Analyze the quality and ripeness of a fruit in the given bounding box."""
        x1, y1, x2, y2 = bbox
        fruit_roi = image[y1:y2, x1:x2]
        
        # Convert to HSV for better color analysis
        hsv = cv2.cvtColor(fruit_roi, cv2.COLOR_BGR2HSV)
        
        # Analyze ripeness
        ripeness = self._analyze_ripeness(hsv, fruit_type)
        
        # Detect defects
        defects = self._detect_defects(hsv, fruit_roi.shape[0] * fruit_roi.shape[1])
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(ripeness, defects)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(ripeness, defects, fruit_type)
        
        # Estimate weight
        estimated_weight = self.estimate_weight(bbox, fruit_type)
        
        return FruitQuality(
            ripeness_level=ripeness,
            quality_score=quality_score,
            defects=defects,
            recommendations=recommendations,
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

    def _detect_defects(self, hsv: np.ndarray, total_area: int) -> List[str]:
        """Detect defects in the fruit."""
        defects = []
        
        for defect_type, pattern in self.defect_patterns.items():
            mask = cv2.inRange(hsv, np.array(pattern['color'][0]), np.array(pattern['color'][1]))
            defect_area = np.sum(mask > 0)
            defect_percentage = defect_area / total_area
            
            if defect_area > pattern['min_area'] and defect_percentage > pattern['threshold']:
                defects.append(defect_type)
                
        return defects

    def _calculate_quality_score(self, ripeness: float, defects: List[str]) -> float:
        """Calculate overall quality score."""
        # Start with ripeness score
        score = ripeness
        
        # Penalize for defects with different weights
        defect_penalties = {
            'bruise': 0.15,
            'mold': 0.4,
            'rot': 0.3
        }
        
        for defect in defects:
            score = max(0, score - defect_penalties.get(defect, 0.2))
        
        return score

    def _generate_recommendations(self, ripeness: float, defects: List[str], fruit_type: str) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Ripeness recommendations
        if ripeness < 0.3:
            recommendations.append("Fruit is underripe - wait a few days before consuming")
        elif ripeness > 0.8:
            recommendations.append("Fruit is very ripe - consume soon")
            
        # Defect recommendations
        if 'bruise' in defects:
            recommendations.append("Bruised area detected - consume soon")
        if 'mold' in defects:
            recommendations.append("Mold detected - do not consume")
        if 'rot' in defects:
            recommendations.append("Rot detected - do not consume")
            
        # Storage recommendations
        if fruit_type.lower() == 'banana':
            if ripeness < 0.5:
                recommendations.append("Store at room temperature to ripen")
            else:
                recommendations.append("Store in refrigerator to slow ripening")
        elif fruit_type.lower() in ['apple', 'orange', 'pomegranate']:
            recommendations.append("Store in refrigerator to maintain freshness")
        elif fruit_type.lower() in ['strawberry', 'grape']:
            recommendations.append("Store in refrigerator and consume within a few days")
                
        return recommendations

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