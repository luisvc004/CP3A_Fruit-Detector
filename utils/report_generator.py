from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime
import os
from typing import List, Dict
import cv2
import numpy as np
from .fruit_analysis import FruitQuality

class ReportGenerator:
    def __init__(self):
        self.reports_dir = 'reports'
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
            
        self.styles = getSampleStyleSheet()
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            spaceAfter=30
        )
        self.subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            spaceAfter=20
        )
        self.normal_style = self.styles['Normal']
        
    def generate_report(self, image, detections, qualities, nutritional_info):
        """Generate a PDF report with the analysis results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(self.reports_dir, f'fruit_analysis_{timestamp}.pdf')
        
        doc = SimpleDocTemplate(report_path, pagesize=letter)
        story = []
        
        # Title
        story.append(Paragraph("Fruit Analysis Report", self.title_style))
        story.append(Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", self.normal_style))
        story.append(Spacer(1, 20))
        
        # Analysis Image
        story.append(Paragraph("Analysis Results", self.subtitle_style))
        img_path = os.path.join(self.reports_dir, f'analysis_{timestamp}.jpg')
        cv2.imwrite(img_path, image)
        img = Image(img_path, width=6*inch, height=4*inch)
        story.append(img)
        story.append(Spacer(1, 20))
        
        # Detections Summary
        story.append(Paragraph("Detected Fruits", self.subtitle_style))
        detection_data = [['Fruit', 'Confidence', 'Quality Score', 'Weight (g)', 'Ripeness']]
        
        for det, quality in zip(detections, qualities):
            detection_data.append([
                det['name'],
                f"{det['confidence']:.2f}",
                f"{quality.quality_score:.2f}",
                f"{quality.estimated_weight:.1f}",
                f"{quality.ripeness_level:.2f}"
            ])
            
        table = Table(detection_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(table)
        story.append(Spacer(1, 20))
        
        # Detailed Analysis
        story.append(Paragraph("Detailed Analysis", self.subtitle_style))
        for det, quality in zip(detections, qualities):
            story.append(Paragraph(f"{det['name']} Analysis:", self.styles['Heading3']))
            story.append(Spacer(1, 10))
            
            # Quality information
            quality_text = []
            quality_text.append(f"Quality Score: {quality.quality_score:.2f}")
            quality_text.append(f"Ripeness Level: {quality.ripeness_level:.2f}")
            quality_text.append(f"Estimated Weight: {quality.estimated_weight:.1f}g")
            
            if quality.defects:
                quality_text.append("Defects Detected:")
                for defect in quality.defects:
                    quality_text.append(f"- {defect}")
                    
            if quality.recommendations:
                quality_text.append("Recommendations:")
                for rec in quality.recommendations:
                    quality_text.append(f"- {rec}")
            
            # Add each line as a separate paragraph with proper spacing
            for line in quality_text:
                story.append(Paragraph(line, self.normal_style))
                story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 10))
            
            # Nutritional information
            if det['name'] in nutritional_info:
                nutr = nutritional_info[det['name']]
                if nutr:
                    story.append(Paragraph("Nutritional Information:", self.styles['Heading4']))
                    story.append(Spacer(1, 5))
                    
                    nutr_text = []
                    nutr_text.append(f"Calories: {nutr['calories']} kcal")
                    nutr_text.append(f"Protein: {nutr['protein']}g")
                    nutr_text.append(f"Carbs: {nutr['carbs']}g")
                    nutr_text.append(f"Fiber: {nutr['fiber']}g")
                    nutr_text.append(f"Vitamins: {', '.join(nutr['vitamins'])}")
                    
                    # Add each line as a separate paragraph with proper spacing
                    for line in nutr_text:
                        story.append(Paragraph(line, self.normal_style))
                        story.append(Spacer(1, 5))
            
            story.append(Spacer(1, 20))
        
        # Build the PDF
        doc.build(story)
        
        # Clean up temporary image file
        os.remove(img_path)
        
        return report_path