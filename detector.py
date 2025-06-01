import argparse
import time
from pathlib import Path
import os

import numpy as np
import cv2
import torch
from PySide6.QtCore import QObject, Signal, QThread
from PySide6.QtGui import QImage

from models.experimental import attempt_load
from utils.datasets import letterbox
from utils.general import check_img_size, check_requirements, non_max_suppression, scale_coords
from utils.plots import colors, plot_one_box
from utils.torch_utils import select_device
from utils.nutritional_info import get_nutritional_info
from utils.fruit_analysis import FruitAnalyzer
from utils.report_generator import ReportGenerator
from utils.data_exporter import DataExporter

parser = argparse.ArgumentParser()
parser.add_argument('--weights', nargs='+', type=str, default='weights/Fruits.pt', help='model.pt path(s)')
parser.add_argument('--img-size', type=int, default=640, help='inference size (pixels)')
parser.add_argument('--conf-thres', type=float, default=0.25, help='object confidence threshold')
parser.add_argument('--iou-thres', type=float, default=0.45, help='IOU threshold for NMS')
parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --class 0, or --class 0 2 3')
parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
parser.add_argument('--project', default='runs/detect', help='save results to project/name')
parser.add_argument('--name', default='exp', help='save results to project/name')
parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
args = parser.parse_args()

check_requirements(exclude=('tensorboard', 'pycocotools', 'thop'))

class Detector(QObject):
    signal_frame = Signal(QImage)
    signal_show_analysis = Signal(list)
    signal_show_quality = Signal(list)
    signal_show_nutrition = Signal(dict)
    signal_export_complete = Signal(str, str)  # filename, type

    def __init__(self):
        super().__init__()
        weights, imgsz = args.weights, args.img_size
        self.save_dir = 'output'
        
        # Load model
        self.device = select_device(args.device)
        self.model = attempt_load(weights, map_location=self.device)  # load FP32 model
        self.stride = int(self.model.stride.max())  # model stride
        self.imgsz = check_img_size(imgsz, s=self.stride)  # check img_size
        self.names = self.model.module.names if hasattr(self.model, 'module') else self.model.names  # get class names
        self.last_detections = []  # Store last detections
        self.last_qualities = []   # Store last quality analyses
        self.last_nutritional_info = {}  # Store last nutritional info
        self.last_analysis = []    # Store complete analysis results
        self.last_frame = None
        
        # Initialize analyzers
        self.fruit_analyzer = FruitAnalyzer()
        self.report_generator = ReportGenerator()
        self.data_exporter = DataExporter()
        
        if self.device.type != 'cpu':
            self.model(torch.zeros(1, 3, self.imgsz, self.imgsz).to(self.device).type_as(next(self.model.parameters())))  # run once
    
    def detect(self, img):
        self.last_frame = img
        original_image = img.copy()
        t0 = time.time()
        
        # Preprocess image
        img = letterbox(img)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB, to 3x416x416
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.float()  # uint8 to fp16/32
        img /= 255.0  # 0 - 255 to 0.0 - 1.0
        img = img.unsqueeze(0)

        # Inference
        pred = self.model(img, augment=False)[0]

        # Apply NMS
        pred = non_max_suppression(pred, args.conf_thres, args.iou_thres, classes=args.classes, agnostic=args.agnostic_nms)

        # Store detections
        self.last_detections = pred
        
        # Process detections
        detections_info = []
        fruit_qualities = []
        nutritional_info = {}
        analysis_results = []
        
        for det in pred:  # detections per image
            if len(det):
                # Rescale boxes from img size to original_image size
                det[:, :4] = scale_coords(img.shape[2:], det[:, :4], original_image.shape).round()

                # Process each detection
                for *xyxy, conf, cls in reversed(det):
                    c = int(cls)  # integer class
                    fruit_name = self.names[c]
                    
                    # Convert tensor coordinates to integers
                    x1, y1, x2, y2 = map(int, xyxy)
                    
                    # Get nutritional info
                    if fruit_name not in nutritional_info:
                        nutritional_info[fruit_name] = get_nutritional_info(fruit_name)
                    
                    # Analyze fruit quality
                    quality = self.fruit_analyzer.analyze_fruit(original_image, (x1, y1, x2, y2), fruit_name)
                    fruit_qualities.append(quality)
                    
                    # Create analysis result
                    analysis_result = {
                        'name': fruit_name,
                        'confidence': float(conf),
                        'bbox': [x1, y1, x2, y2],
                        'quality': quality,
                        'nutritional_info': nutritional_info[fruit_name]
                    }
                    analysis_results.append(analysis_result)
                    
                    # Store detection info
                    detections_info.append({
                        'name': fruit_name,
                        'confidence': float(conf),
                        'bbox': [x1, y1, x2, y2],
                        'quality': quality
                    })
                    
                    # Draw box with quality info
                    color = colors(c, True)
                    plot_one_box(xyxy, original_image, label=None, color=color, line_thickness=3)
                    
                    # Add label with confidence and quality
                    label = f"{fruit_name} {conf:.2f}"
                    if quality and hasattr(quality, 'quality_score'):
                        try:
                            quality_score = float(quality.quality_score)
                            label += f" | Quality: {quality_score:.2f}"
                        except (ValueError, TypeError):
                            label += f" | Quality: {quality.quality_score}"
                    
                    # Draw label
                    t_size = cv2.getTextSize(label, 0, fontScale=0.6, thickness=1)[0]
                    c2 = x1 + t_size[0], y1 - t_size[1] - 3
                    cv2.rectangle(original_image, (x1, y1), c2, color, -1, cv2.LINE_AA)  # filled
                    cv2.putText(original_image, label, (x1, y1 - 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, [225, 255, 255], 1, cv2.LINE_AA)
                    
                    # Draw ripeness indicator
                    ripeness_color = (
                        int(255 * (1 - quality.ripeness_level)),  # More red for less ripe
                        int(255 * quality.ripeness_level),        # More green for more ripe
                        0
                    )
                    # Increased circle size and moved it further from text
                    cv2.circle(original_image, (x1 + 30, y1 - t_size[1] - 30), 12, ripeness_color, -1)
        
        # Store results for report generation and UI updates
        self.last_qualities = fruit_qualities
        self.last_nutritional_info = nutritional_info
        self.last_analysis = analysis_results
        
        # Emit signals
        self.signal_show_analysis.emit(detections_info)
        self.signal_show_quality.emit(fruit_qualities)
        self.signal_show_nutrition.emit(nutritional_info)
        
        # Generate report if there are detections
        if detections_info:
            report_path = self.report_generator.generate_report(
                original_image,
                detections_info,
                fruit_qualities,
                nutritional_info
            )
            self.signal_export_complete.emit(report_path, "PDF")
        
        print(f'Done. ({time.time() - t0:.3f}s)')
        return original_image

    def export_data(self, format_type: str):
        """Export data in the specified format."""
        if not self.last_detections:
            return
        
        if format_type == "CSV":
            filename = self.data_exporter.export_to_csv(
                self.last_detections,
                self.last_qualities,
                self.last_nutritional_info
            )
            self.signal_export_complete.emit(filename, "CSV")
        
        elif format_type == "EXCEL":
            filename = self.data_exporter.export_to_excel(
                self.last_detections,
                self.last_qualities,
                self.last_nutritional_info
            )
            self.signal_export_complete.emit(filename, "EXCEL")
        
        elif format_type == "DASHBOARD":
            filename = self.data_exporter.generate_dashboard(
                self.last_detections,
                self.last_qualities,
                self.last_nutritional_info
            )
            self.signal_export_complete.emit(filename, "DASHBOARD")
