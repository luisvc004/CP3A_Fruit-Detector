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
        
        # Initialize pygame mixer with specific settings
        print("Initializing pygame...")  # Debug log
        try:
            pygame.init()
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
            print("Pygame initialized successfully")
        except Exception as e:
            print(f"Error initializing pygame: {str(e)}")
            QMessageBox.warning(self, "Audio Error", "Failed to initialize audio system. Audio features will be disabled.")
            return
        
        # Audio state variables
        self.is_playing = False
        self.current_text = ""
        self.audio_timer = QTimer()
        self.audio_timer.timeout.connect(self.start_audio)
        
        self.temp_audio_file = None
        
        # Connect menu actions
        self.ui.actionOpen.triggered.connect(self.getFile)
        self.ui.actionExit.triggered.connect(self.close)
        self.ui.actionAbout.triggered.connect(self.showAbout)
        
        # Connect buttons
        self.ui.btn_browse.clicked.connect(self.getFile)
        self.ui.btn_start.clicked.connect(self.predict)
        
        # Setup audio controls
        self.setup_audio_controls()

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

    def setup_audio_controls(self):
        # Connect button signals
        self.ui.btn_play.clicked.connect(self.play_audio)
        self.ui.btn_pause.clicked.connect(self.pause_audio)
        self.ui.btn_stop.clicked.connect(self.stop_audio)
        
        # Initially show audio buttons
        self.ui.btn_play.show()
        self.ui.btn_pause.show()
        self.ui.btn_stop.show()
        
        # Initially disable pause and stop buttons
        self.ui.btn_pause.setEnabled(False)
        self.ui.btn_stop.setEnabled(False)

    def play_audio(self):
        if not self.is_playing:
            print("Starting audio playback process with 5-second delay...")  # Debug log
            
            # Disable play button and enable pause/stop immediately
            self.ui.btn_play.setEnabled(False)
            self.ui.btn_pause.setEnabled(True)
            self.ui.btn_stop.setEnabled(True)
            
            # Start the 5-second delay timer
            self.audio_timer.start(5000) # 5000 ms = 5 seconds delay before calling start_audio
            
            print("5-second delay started.") # Debug log

    def start_audio(self):
        # This function is called when the 5-second delay timer finishes
        print("Delay finished, starting audio generation and playback...")  # Debug log
        
        self.is_playing = True # Set playing state here
        
        # Ensure audio control buttons are visible and correctly enabled
        if self.current_text:
            try:
                # Create a temporary file for the audio
                if self.temp_audio_file:
                    os.remove(self.temp_audio_file)
                fd, self.temp_audio_file = tempfile.mkstemp(suffix='.mp3')
                os.close(fd)
                print(f"Created temporary file: {self.temp_audio_file}")  # Debug log
                
                # Generate speech
                print("Generating speech...")  # Debug log
                tts = gTTS(text=self.current_text, lang='en')
                tts.save(self.temp_audio_file)
                print("Speech generated and saved")  # Debug log
                
                # Stop any currently playing audio
                pygame.mixer.music.stop()
                
                # Load and play the new audio
                print("Loading audio file...")  # Debug log
                pygame.mixer.music.load(self.temp_audio_file)
                print("Playing audio...")  # Debug log
                pygame.mixer.music.play()
                
                # Wait for the audio to finish
                print("Waiting for audio to finish...")  # Debug log
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    QApplication.processEvents()  # Keep UI responsive
                print("Audio finished playing")  # Debug log
                
            except Exception as e:
                error_msg = f"Error playing audio: {str(e)}"
                print(error_msg)  # Debug log
                QMessageBox.warning(self, "Audio Error", error_msg)
            finally:
                self.stop_audio() # Ensure stop_audio is called when playback finishes
        else:
            print("No text to convert to speech")  # Debug log
            self.stop_audio() # Ensure stop_audio is called if no text

    def pause_audio(self):
        if self.is_playing:
            print("Pausing audio...") # Debug log
            pygame.mixer.music.pause()
            self.is_playing = False
            self.ui.btn_play.setEnabled(True) # Enable Play to resume countdown
            self.ui.btn_pause.setEnabled(False)

    def stop_audio(self):
        print("Stopping audio...")  # Debug log
        self.is_playing = False
        self.audio_timer.stop()
        try:
            pygame.mixer.music.stop()
        except Exception as e:
            print(f"Error stopping audio: {str(e)}")
        
        self.ui.btn_play.setEnabled(True)
        self.ui.btn_pause.setEnabled(False)
        self.ui.btn_stop.setEnabled(False)
        
        # Clean up temporary file if it exists
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
                print(f"Removed temporary file: {self.temp_audio_file}")  # Debug log
            except Exception as e:
                print(f"Error removing temporary file: {str(e)}")  # Debug log
            self.temp_audio_file = None

    def closeEvent(self, event):
        # Clean up temporary file when closing
        if self.temp_audio_file and os.path.exists(self.temp_audio_file):
            try:
                os.remove(self.temp_audio_file)
            except:
                pass
        pygame.mixer.quit()
        pygame.quit()
        event.accept()

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

        # Generate nutritional text using the history for display (HTML)
        nutritional_html = "<h3>Detected Fruits</h3>"
        # Also generate plain text for audio
        plain_audio_text = "Detected Fruits. "
        
        if self.fruit_history:
            for fruit, count in self.fruit_history.items():
                info = get_nutritional_info(fruit)
                
                # Format for display (HTML)
                if info:
                    nutritional_html += f"<div style='margin-bottom: 20px;'>"
                    nutritional_html += f"<b>{fruit.title()} (x{count})</b><br>"
                    nutritional_html += format_nutritional_info(fruit, info)
                    nutritional_html += "</div>"
                else:
                    nutritional_html += f"<div style='margin-bottom: 20px;'>"
                    nutritional_html += f"<b>{fruit.title()} (x{count})</b>: No nutritional information available."
                    nutritional_html += "</div>"

                # Format for audio (Plain Text)
                plain_audio_text += f"{fruit.title()}. Count {count}. "
                if info:
                    plain_audio_text += f"Nutritional Information per 100 grams: "
                    
                    if 'calories' in info and info['calories'] is not None:
                        plain_audio_text += f"Calories: {info['calories']} kcal, "
                    if 'protein' in info and info['protein'] is not None:
                         plain_audio_text += f"Protein: {info['protein']}, "
                    if 'carbs' in info and info['carbs'] is not None:
                        plain_audio_text += f"Carbohydrates: {info['carbs']}, "
                    if 'fiber' in info and info['fiber'] is not None:
                         plain_audio_text += f"Fiber: {info['fiber']}, "
                    
                    if 'vitamins' in info and info['vitamins']:
                        vitamins_text = ', '.join(info['vitamins'])
                        plain_audio_text += f"Vitamins: {vitamins_text}. "
                        
                    if 'minerals' in info and info['minerals']:
                         minerals_text = ', '.join(info['minerals'])
                         plain_audio_text += f"Minerals: {minerals_text}. "

                    if 'benefits' in info and info['benefits']:
                        # Join benefits with periods for better separation in speech
                        # Change to use comma and then period for a slightly longer pause
                        benefits_text = ', '.join(info['benefits']) + '.'
                        plain_audio_text += f"Benefits: {benefits_text} "
                else:
                    plain_audio_text += "No nutritional information available. "
                    
            self.nutritionalInfo.setHtml(nutritional_html)
            
            # Set the plain text for audio playback
            self.current_text = plain_audio_text
            print(f"Text for audio: {self.current_text}") # Debug log
            
            # Enable audio controls after detection
            self.ui.btn_play.setEnabled(True)
            self.ui.btn_pause.setEnabled(False)
            self.ui.btn_stop.setEnabled(False)
        else:
            self.nutritionalInfo.setText("No fruits detected.")
            self.current_text = "No fruits detected." # Set audio text as well
            print(f"Text for audio: {self.current_text}") # Debug log
            
            # Disable audio controls if no fruits detected
            self.ui.btn_play.setEnabled(False)
            self.ui.btn_pause.setEnabled(False)
            self.ui.btn_stop.setEnabled(False)

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
