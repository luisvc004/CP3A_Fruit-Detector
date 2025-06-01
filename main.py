import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QFileDialog, QMessageBox, 
                              QTextEdit, QDockWidget, QVBoxLayout, QWidget, QPushButton)
from PySide6.QtCore import QFile, Qt, QTimer
from PySide6.QtUiTools import QUiLoader
from PySide6.QtGui import QPixmap, QImage, QAction
from PySide6.QtCore import QThread, Signal, QDir
import cv2
from detector import Detector
from utils.nutritional_info import get_nutritional_info, format_nutritional_info
from collections import Counter, defaultdict
from gtts import gTTS
import pygame
import tempfile
import time
from googletrans import Translator
import re


def convertCVImage2QtImage(cv_img):
    cv_img = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
    height, width, channel = cv_img.shape
    bytesPerLine = 3 * width
    qimg = QImage(cv_img.data, width, height, bytesPerLine, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg)


class ProcessImage(QThread):
    signal_show_frame = Signal(object)
    signal_show_nutrition = Signal(list)
    signal_show_analysis = Signal(list)
    signal_show_quality = Signal(list)

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
                self.signal_show_analysis.emit(self.detector.last_analysis)
                self.signal_show_quality.emit(self.detector.last_qualities)
                cv2.waitKey(30)
            self.video.release()
        else:
            # Process single image
            self.frame = cv2.imread(self.fileName)
            if self.frame is not None:
                self.frame = self.detector.detect(self.frame)
                self.signal_show_frame.emit(self.frame)
                self.signal_show_nutrition.emit(self.detector.last_detections)
                self.signal_show_analysis.emit(self.detector.last_analysis)
                self.signal_show_quality.emit(self.detector.last_qualities)

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
        super().__init__()
        print("Initializing MainWindow...")
        self.load_ui()
        self.setup_connections()
        
        # Initialize history dictionaries
        self.fruit_history = defaultdict(int)
        self.quality_history = defaultdict(list)
        self.analysis_history = defaultdict(list)
        
        # Initialize pygame for audio
        try:
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            print("Pygame initialized successfully")
        except Exception as e:
            print(f"Error initializing pygame: {str(e)}")
            QMessageBox.warning(self, "Audio Error", "Failed to initialize audio system. Audio features will be disabled.")
        
        self.setup_audio()
        
        # Set initial status
        self.ui.statusbar.showMessage("Ready")
        print("MainWindow initialized successfully")

    def load_ui(self):
        """Load the UI from the form.ui file."""
        try:
            print("Loading UI from form.ui...")
            loader = QUiLoader()
            ui_file = QFile("ui/form.ui")
            if not ui_file.exists():
                print(f"Error: UI file not found at {ui_file.fileName()}")
                return
                
            ui_file.open(QFile.ReadOnly)
            self.ui = loader.load(ui_file)
            ui_file.close()
            
            if not self.ui:
                print("Error: Failed to load UI")
                return
                
            self.setCentralWidget(self.ui)
            print("UI loaded successfully")
        except Exception as e:
            print(f"Error loading UI: {str(e)}")

    def setup_audio(self):
        """Setup audio-related variables and connections."""
        self.current_audio_file = None
        self.is_playing = False
        
        # Connect audio buttons
        self.ui.btn_audio_analysis.clicked.connect(lambda: self.play_audio('analysis'))
        self.ui.btn_audio_nutrition.clicked.connect(lambda: self.play_audio('nutrition'))
        
    def play_audio(self, tab_type):
        """Play audio for the specified tab."""
        print(f"Attempting to play audio for {tab_type} tab...")
        
        if self.is_playing:
            print("Stopping current audio...")
            pygame.mixer.music.stop()
            self.is_playing = False
            return
            
        # Get text from the appropriate tab
        if tab_type == 'analysis':
            text = self.ui.txt_analysis.toPlainText()
        else:
            text = self.ui.txt_nutrition.toPlainText()
            
        if not text:
            print("No text to convert to speech")
            return
            
        try:
            print("Cleaning text for speech...")
            # Clean the text for better speech
            text = self.clean_text_for_speech(text)
            print(f"Text to be spoken: {text[:100]}...")  # Print first 100 chars for debugging
            
            # Create temporary file for audio
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                temp_filename = temp_file.name
                print(f"Created temporary file: {temp_filename}")
                
            # Generate speech
            print("Generating speech...")
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(temp_filename)
            print("Speech generated successfully")
            
            # Play the audio
            print("Loading audio file...")
            pygame.mixer.music.load(temp_filename)
            print("Playing audio...")
            pygame.mixer.music.play()
            self.is_playing = True
            
            # Clean up the temporary file when done
            def cleanup():
                print("Cleaning up audio resources...")
                pygame.mixer.music.unload()
                try:
                    os.unlink(temp_filename)
                    print("Temporary file removed")
                except Exception as e:
                    print(f"Error removing temporary file: {str(e)}")
                self.is_playing = False
                
            # Set up timer to clean up after audio finishes
            # Estimate duration: roughly 0.1 seconds per character
            duration = int(len(text) * 0.1 * 1000)
            print(f"Estimated audio duration: {duration/1000:.1f} seconds")
            QTimer.singleShot(duration, cleanup)
            
        except Exception as e:
            print(f"Error playing audio: {str(e)}")
            self.is_playing = False
            QMessageBox.warning(self, "Audio Error", f"Failed to play audio: {str(e)}")
            
    def clean_text_for_speech(self, text):
        """Clean text for better speech synthesis."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Replace special characters
        text = text.replace('•', '')
        text = text.replace(':', '')
        text = text.replace('-', '')
        text = text.replace('|', '')
        
        # Add pauses for better speech
        text = text.replace('\n', '. ')
        
        # Remove multiple spaces
        text = ' '.join(text.split())
        
        return text

    def setup_connections(self):
        # Connect menu actions
        self.ui.actionOpen.triggered.connect(self.getFile)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        self.ui.actionExport.triggered.connect(self.exportReport)
        
        # Connect buttons
        self.ui.btn_browse.clicked.connect(self.getFile)
        self.ui.btn_start.clicked.connect(self.predict)
        
    def getFile(self):
        # Clear history when loading a new file
        self.fruit_history.clear()
        self.quality_history.clear()
        self.analysis_history.clear()
        self.ui.txt_analysis.clear()
        self.ui.txt_nutrition.clear()
        
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
        self.process_image.signal_show_analysis.connect(self.update_analysis)
        self.process_image.signal_show_quality.connect(self.update_quality)
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
            nutritional_text = "<h3>Detected Fruits:</h3>"
            for fruit, count in self.fruit_history.items():
                info = get_nutritional_info(fruit)
                if info:
                    nutritional_text += f"<b>{fruit} (x{count})</b><br>"
                    nutritional_text += format_nutritional_info(fruit, info) + "<br><br>"
                    
                    # Store the text for audio playback
                    self.current_text = nutritional_text
                else:
                    nutritional_text += f"<b>{fruit} (x{count})</b>: No nutritional information available.<br><br>"
            self.ui.txt_nutrition.setHtml(nutritional_text)
        else:
            self.ui.txt_nutrition.setText("No fruits detected.")

    def update_analysis(self, analysis_list):
        if analysis_list:
            analysis_text = "<h3>Fruit Analysis:</h3>"
            for analysis in analysis_list:
                fruit_name = analysis['name']
                analysis_text += f"<b>{fruit_name}</b><br>"
                analysis_text += f"Confidence: {analysis['confidence']:.2f}<br>"
                
                # Add quality information
                quality = analysis['quality']
                analysis_text += f"Quality Score: {quality.quality_score:.2f}<br>"
                analysis_text += f"Ripeness Level: {quality.ripeness_level:.2f}<br>"
                analysis_text += f"Estimated Weight: {quality.estimated_weight:.1f}g<br>"
                
                if quality.defects:
                    analysis_text += "Defects Detected:<br>"
                    for defect in quality.defects:
                        analysis_text += f"- {defect}<br>"
                
                if quality.recommendations:
                    analysis_text += "Recommendations:<br>"
                    for rec in quality.recommendations:
                        analysis_text += f"- {rec}<br>"
                
                # Add nutritional information
                if analysis['nutritional_info']:
                    nutr = analysis['nutritional_info']
                    analysis_text += "<br>Nutritional Information:<br>"
                    analysis_text += f"Calories: {nutr['calories']} kcal<br>"
                    analysis_text += f"Protein: {nutr['protein']}g<br>"
                    analysis_text += f"Carbs: {nutr['carbs']}g<br>"
                    analysis_text += f"Fiber: {nutr['fiber']}g<br>"
                    analysis_text += f"Vitamins: {', '.join(nutr['vitamins'])}<br>"
                
                analysis_text += "<br>"
            self.ui.txt_analysis.setHtml(analysis_text)
        else:
            self.ui.txt_analysis.setText("No analysis available.")

    def update_quality(self, qualities):
        if qualities:
            quality_text = "<h3>Quality Analysis:</h3>"
            # Get the current detections from the detector
            if hasattr(self, 'process_image') and self.process_image.detector.last_analysis:
                for analysis in self.process_image.detector.last_analysis:
                    fruit_name = analysis['name']
                    quality = analysis['quality']
                    
                    quality_text += f"<b>{fruit_name}</b><br>"
                    quality_text += f"Quality Score: {quality.quality_score:.2f}<br>"
                    quality_text += f"Ripeness Level: {quality.ripeness_level:.2f}<br>"
                    quality_text += f"Estimated Weight: {quality.estimated_weight:.1f}g<br>"
                    
                    if quality.defects:
                        quality_text += "Defects Detected:<br>"
                        for defect in quality.defects:
                            quality_text += f"- {defect}<br>"
                    
                    if quality.recommendations:
                        quality_text += "Recommendations:<br>"
                        for rec in quality.recommendations:
                            quality_text += f"- {rec}<br>"
                    
                    quality_text += "<br>"
            else:
                quality_text += "No fruit analysis available."
            self.ui.txt_analysis.setHtml(quality_text)
        else:
            self.ui.txt_analysis.setText("No quality analysis available.")

    def exportReport(self):
        if not hasattr(self, 'process_image') or not self.process_image.detector.last_detections:
            QMessageBox.warning(self, "Warning", "No analysis results to export!")
            return
            
        # The report is already generated in the detector
        QMessageBox.information(self, "Success", "Report has been generated in the 'reports' directory.")

    def showAbout(self):
        QMessageBox.about(self, "About",
            "Fruit Detection and Analysis System\n\n"
            "This application uses YOLO to detect fruits in images and videos, "
            "analyzes their quality and ripeness, and provides nutritional information.\n\n"
            "Features:\n"
            "- Real-time fruit detection\n"
            "- Quality and ripeness analysis\n"
            "- Nutritional information\n"
            "- Detailed reports\n\n"
            "Version 1.0")


if __name__ == '__main__':
    try:
        print("Starting application...")
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()  # Explicitly show the window
        print("Window shown, entering event loop...")
        sys.exit(app.exec())
    except Exception as e:
        print(f"Error in main: {str(e)}")
