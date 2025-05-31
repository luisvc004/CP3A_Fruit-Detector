import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, 
                              QTextEdit, QDockWidget, QVBoxLayout, QWidget)
from PySide6.QtCore import QFile, Qt
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QImage, QAction
from PySide6.QtCore import QThread, Signal, QDir
import cv2
from detector import Detector
from utils.nutritional_info import get_nutritional_info, format_nutritional_info
from collections import Counter, defaultdict


def convertCVImage2QtImage(cv_img):
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    height, width, channel = cv_img.shape
    bytesPerLine = 3 * width
    qimg = QImage(cv_img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class ProcessImage(QThread):
    signal_show_frame = Signal(object)
    signal_show_nutrition = Signal(list)

    def __init__(self, fileName):
        QThread.__init__(self)
        self.fileName = fileName
        self.detector = Detector()

    def run(self):
        if self.fileName.lower().endswith(('.mp4', '.avi')):
            self.video = cv2.VideoCapture(self.fileName)
            while True:
                valid, self.frame = self.video.read()
                if valid is not True:
                    break
                self.frame = self.detector.detect(self.frame)
                self.signal_show_frame.emit(self.frame)
                self.signal_show_nutrition.emit(self.detector.last_detections)
                cv2.waitKey(30)
            self.video.release()
        else:
            # Process single image
            self.frame = cv2.imread(self.fileName)
            if self.frame is not None:
                self.frame = self.detector.detect(self.frame)
                self.signal_show_frame.emit(self.frame)
                self.signal_show_nutrition.emit(self.detector.last_detections)

    def stop(self):
        try:
            self.video.release()
        except:
            pass


class show(QThread):
    signal_show_image = Signal(object)

    def __init__(self, fileName):
        QThread.__init__(self)
        self.fileName = fileName
        if self.fileName.lower().endswith(('.mp4', '.avi')):
            self.video = cv2.VideoCapture(self.fileName)
        else:
            self.video = None

    def run(self): 
        if self.video is not None:
            while True:
                valid, self.frame = self.video.read()
                if valid is not True:
                    break
                self.signal_show_image.emit(self.frame)
                cv2.waitKey(30)
            self.video.release()
        else:
            self.frame = cv2.imread(self.fileName)
            if self.frame is not None:
                self.signal_show_image.emit(self.frame)

    def stop(self):
        try:
            if self.video is not None:
                self.video.release()
        except:
            pass


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loader = QUiLoader()
        self.ui = loader.load("ui/form.ui")
        
        # Connect menu actions
        self.ui.actionOpen.triggered.connect(self.getFile)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        
        # Connect buttons
        self.ui.btn_browse.clicked.connect(self.getFile)
        self.ui.btn_start.clicked.connect(self.predict)

        # Create and setup nutritional info dock widget
        self.nutritionalInfo = QTextEdit()
        self.nutritionalInfo.setReadOnly(True)
        self.nutritionalInfo.setStyleSheet("""
            QTextEdit {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 4px;
                padding: 15px;
                font-size: 14px;
                line-height: 1.6;
            }
            QTextEdit h3 {
                color: #2c3e50;
                margin-bottom: 15px;
                border-bottom: 2px solid #3498db;
                padding-bottom: 5px;
            }
            QTextEdit b {
                color: #2980b9;
            }
        """)
        
        dock = QDockWidget("Nutritional Information", self.ui)
        dock.setWidget(self.nutritionalInfo)
        dock.setFeatures(QDockWidget.DockWidgetMovable | QDockWidget.DockWidgetFloatable)
        self.ui.addDockWidget(Qt.RightDockWidgetArea, dock)
        
        # Initialize fruit history
        self.fruit_history = defaultdict(int)
        
        # Set initial status
        self.ui.statusbar.showMessage("Ready")
        self.ui.show()

    def getFile(self):
        # Clear fruit history when loading a new file
        self.fruit_history.clear()
        self.nutritionalInfo.clear()
        
        self.fileName = QFileDialog.getOpenFileName(
            self,
            'Select Image or Video',
            QDir.homePath(),
            'Media Files (*.jpg *.jpeg *.png *.mp4 *.avi)'
        )[0]
        
        if self.fileName:
            self.ui.txt_address.setText(str(self.fileName))
            self.ui.statusbar.showMessage(f"Loaded: {os.path.basename(self.fileName)}")
            self.show = show(self.fileName)
            self.show.signal_show_image.connect(self.show_input)
            self.show.start()
        
    def predict(self):
        if not hasattr(self, 'fileName') or not self.fileName:
            QMessageBox.warning(self, "Warning", "Please select an image or video first!")
            return

        self.ui.statusbar.showMessage("Processing...")
        self.process_image = ProcessImage(self.fileName)
        self.process_image.signal_show_frame.connect(self.show_output)
        self.process_image.signal_show_nutrition.connect(self.update_nutritional_info)
        self.process_image.start()

    def show_input(self, image):
        pixmap = convertCVImage2QtImage(image)
        self.ui.lbl_input.setPixmap(pixmap.scaled(
            self.ui.lbl_input.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))

    def show_output(self, image):
        pixmap = convertCVImage2QtImage(image)
        self.ui.lbl_output.setPixmap(pixmap.scaled(
            self.ui.lbl_output.size(),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        ))
        self.ui.statusbar.showMessage("Detection complete")

    def update_nutritional_info(self, detections):
        # Update current frame detections
        current_fruits = Counter()
        for det in detections:
            if len(det):
                for *_, cls in reversed(det):
                    fruit_name = self.process_image.detector.names[int(cls)]
                    current_fruits[fruit_name] += 1
                    # Update history with new detections
                    self.fruit_history[fruit_name] = max(self.fruit_history[fruit_name], current_fruits[fruit_name])

        # Generate nutritional text using the history
        if self.fruit_history:
            nutritional_text = "<h3>Detected Fruits</h3>"
            for fruit, count in self.fruit_history.items():
                info = get_nutritional_info(fruit)
                if info:
                    nutritional_text += f"<div style='margin-bottom: 20px;'>"
                    nutritional_text += f"<b>{fruit.title()} (x{count})</b><br>"
                    nutritional_text += format_nutritional_info(fruit, info)
                    nutritional_text += "</div>"
                else:
                    nutritional_text += f"<div style='margin-bottom: 20px;'>"
                    nutritional_text += f"<b>{fruit.title()} (x{count})</b>: No nutritional information available."
                    nutritional_text += "</div>"
            self.nutritionalInfo.setHtml(nutritional_text)
        else:
            self.nutritionalInfo.setText("No fruits detected.")

    def showAbout(self):
        QMessageBox.about(self, "About Fruit Detection System",
            "Fruit Detection System\n\n"
            "A computer vision application that detects fruits in images and videos "
            "and provides nutritional information.\n\n"
            "Version 1.0")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')  # Use Fusion style for a modern look
    widget = MainWindow()
    sys.exit(app.exec())
