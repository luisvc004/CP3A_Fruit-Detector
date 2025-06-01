import os
import csv
import pandas as pd
from datetime import datetime
from typing import List, Dict
import matplotlib.pyplot as plt
import seaborn as sns
from .fruit_analysis import FruitQuality

class DataExporter:
    def __init__(self):
        self.reports_dir = 'reports'
        self.data_dir = 'data'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def export_to_csv(self, detections: List[Dict], qualities: List[FruitQuality], nutritional_info: Dict) -> str:
        """Export detection and analysis data to CSV."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.data_dir, f'fruit_analysis_{timestamp}.csv')
        
        # Prepare data for CSV
        data = []
        for det, quality in zip(detections, qualities):
            row = {
                'Fruit': det['name'],
                'Confidence': det['confidence'],
                'Quality_Score': quality.quality_score,
                'Ripeness_Level': quality.ripeness_level,
                'Estimated_Weight': quality.estimated_weight,
                'Defects': ', '.join(quality.defects) if quality.defects else 'None',
                'Recommendations': ', '.join(quality.recommendations)
            }
            
            # Add nutritional information
            if det['name'] in nutritional_info:
                nutr = nutritional_info[det['name']]
                row.update({
                    'Calories': nutr['calories'],
                    'Protein': nutr['protein'],
                    'Carbs': nutr['carbs'],
                    'Fiber': nutr['fiber'],
                    'Vitamins': ', '.join(nutr['vitamins'])
                })
            
            data.append(row)
        
        # Write to CSV
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        return filename

    def export_to_excel(self, detections: List[Dict], qualities: List[FruitQuality], nutritional_info: Dict) -> str:
        """Export detection and analysis data to Excel with multiple sheets."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.data_dir, f'fruit_analysis_{timestamp}.xlsx')
        
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
            # Detection and Quality sheet
            detection_data = []
            for det, quality in zip(detections, qualities):
                row = {
                    'Fruit': det['name'],
                    'Confidence': det['confidence'],
                    'Quality_Score': quality.quality_score,
                    'Ripeness_Level': quality.ripeness_level,
                    'Estimated_Weight': quality.estimated_weight,
                    'Defects': ', '.join(quality.defects) if quality.defects else 'None',
                    'Recommendations': ', '.join(quality.recommendations)
                }
                detection_data.append(row)
            
            df_detection = pd.DataFrame(detection_data)
            df_detection.to_excel(writer, sheet_name='Detection_Analysis', index=False)
            
            # Nutritional Information sheet
            nutritional_data = []
            for fruit, info in nutritional_info.items():
                if info:
                    row = {
                        'Fruit': fruit,
                        'Calories': info['calories'],
                        'Protein': info['protein'],
                        'Carbs': info['carbs'],
                        'Fiber': info['fiber'],
                        'Vitamins': ', '.join(info['vitamins'])
                    }
                    nutritional_data.append(row)
            
            df_nutrition = pd.DataFrame(nutritional_data)
            df_nutrition.to_excel(writer, sheet_name='Nutritional_Info', index=False)
            
            # Statistics sheet
            stats_data = {
                'Metric': [
                    'Total Fruits Detected',
                    'Average Quality Score',
                    'Average Ripeness Level',
                    'Total Weight (g)',
                    'Most Common Fruit',
                    'Highest Quality Fruit',
                    'Most Ripe Fruit'
                ],
                'Value': [
                    len(detections),
                    df_detection['Quality_Score'].mean(),
                    df_detection['Ripeness_Level'].mean(),
                    df_detection['Estimated_Weight'].sum(),
                    df_detection['Fruit'].mode()[0],
                    df_detection.loc[df_detection['Quality_Score'].idxmax(), 'Fruit'],
                    df_detection.loc[df_detection['Ripeness_Level'].idxmax(), 'Fruit']
                ]
            }
            
            df_stats = pd.DataFrame(stats_data)
            df_stats.to_excel(writer, sheet_name='Statistics', index=False)
        
        return filename

    def generate_dashboard(self, detections: List[Dict], qualities: List[FruitQuality], nutritional_info: Dict) -> str:
        """Generate a dashboard with visualizations."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.reports_dir, f'dashboard_{timestamp}.png')
        
        # Create figure with subplots
        fig = plt.figure(figsize=(15, 10))
        fig.suptitle('Fruit Analysis Dashboard', fontsize=16)
        
        # Prepare data
        fruits = [det['name'] for det in detections]
        quality_scores = [q.quality_score for q in qualities]
        ripeness_levels = [q.ripeness_level for q in qualities]
        weights = [q.estimated_weight for q in qualities]
        
        # 1. Quality Scores by Fruit
        plt.subplot(2, 2, 1)
        sns.barplot(x=fruits, y=quality_scores)
        plt.title('Quality Scores by Fruit')
        plt.xticks(rotation=45)
        plt.ylabel('Quality Score')
        
        # 2. Ripeness Levels
        plt.subplot(2, 2, 2)
        sns.barplot(x=fruits, y=ripeness_levels)
        plt.title('Ripeness Levels by Fruit')
        plt.xticks(rotation=45)
        plt.ylabel('Ripeness Level')
        
        # 3. Weight Distribution
        plt.subplot(2, 2, 3)
        sns.barplot(x=fruits, y=weights)
        plt.title('Estimated Weights by Fruit')
        plt.xticks(rotation=45)
        plt.ylabel('Weight (g)')
        
        # 4. Nutritional Comparison
        plt.subplot(2, 2, 4)
        calories = [nutritional_info[f]['calories'] for f in fruits if f in nutritional_info]
        sns.barplot(x=fruits, y=calories)
        plt.title('Calories by Fruit')
        plt.xticks(rotation=45)
        plt.ylabel('Calories (kcal)')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig(filename)
        plt.close()
        
        return filename 