#!/usr/bin/env python3
import os
import subprocess
import sys
import time
import shutil
import vlc
from datetime import datetime
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QFileDialog, QListWidgetItem, QMessageBox, QProgressBar
from PyQt5.QtCore import QTimer

def run_cmd(cmd, timeout=5):
    """Run shell command with timeout"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, 
                              shell=False, timeout=timeout)
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return 1, "", "Timeout"
    except Exception as e:
        return 1, "", str(e)

class VirtualMicManager:
    """Manages virtual microphone"""
    
    def __init__(self):
        self.mic_name = "Real4n54n"
        self.vlc_instance = None
        self.vlc_player = None
        self.current_process = None
    
    def cleanup_all(self):
        """Clean up ALL virtual audio devices"""
        print("Cleaning up virtual audio devices...")
        
        # Stop any playback
        self.stop_playback()
        
        # Unload ALL modules related to virtual mics
        rc, out, err = run_cmd(["pactl", "list", "modules", "short"])
        if rc == 0:
            modules_to_remove = []
            
            for line in out.split('\n'):
                if not line.strip():
                    continue
                
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                module_id = parts[0]
                module_info = ' '.join(parts[1:])
                
                # Remove any virtual audio modules
                if any(keyword in module_info.lower() for keyword in 
                      ['null-sink', 'virtual', 'mic', 'real4n54n', 'remap', 'loopback']):
                    modules_to_remove.append((module_id, module_info))
            
            # Remove in reverse order
            for module_id, module_info in sorted(modules_to_remove, 
                                               key=lambda x: int(x[0]), reverse=True):
                print(f"Removing: {module_id} - {module_info}")
                run_cmd(["pactl", "unload-module", module_id])
                time.sleep(0.1)
        
        time.sleep(2)
    
    def setup(self):
        """Create virtual microphone"""
        print(f"Creating virtual microphone: {self.mic_name}")
        
        # Clean up everything first
        self.cleanup_all()
        time.sleep(2)
        
        # Create simple null-sink
        rc, out, err = run_cmd([
            "pactl", "load-module", "module-null-sink",
            f"sink_name={self.mic_name}",
            "sink_properties=device.description=Virtual_Microphone_Real4n54n",
            "format=s16le",
            "rate=48000",
            "channels=2"
        ])
        
        if rc != 0 or not out.isdigit():
            return False, f"Failed to create virtual microphone: {err}"
        
        print(f"Created virtual microphone: {out}")
        
        # Set monitor as default source
        monitor_name = f"{self.mic_name}.monitor"
        run_cmd(["pactl", "set-default-source", monitor_name])
        
        # Wait and verify
        time.sleep(2)
        
        # Check if created
        rc, sources, err = run_cmd(["pactl", "list", "sources", "short"])
        
        if monitor_name in sources:
            return True, f"Virtual Microphone Created '{self.mic_name}'"
        else:
            return False, f"Failed to create virtual microphone"
    
    def play_audio_vlc(self, audio_path):
        """Play audio using VLC"""
        if not os.path.exists(audio_path):
            return False, "File not found"
        
        # Stop any existing playback
        self.stop_playback()
        
        try:
            # Initialize VLC
            if not self.vlc_instance:
                self.vlc_instance = vlc.Instance('--no-video', '--quiet')
            
            # Create media player
            self.vlc_player = self.vlc_instance.media_player_new()
            
            # Set output to our virtual microphone
            self.vlc_player.audio_output_set("pulse")
            self.vlc_player.audio_output_device_set(None, self.mic_name)
            
            # Load media
            media = self.vlc_instance.media_new(audio_path)
            self.vlc_player.set_media(media)
            
            # Play
            if self.vlc_player.play() == -1:
                return False, "Failed to play audio with VLC"
            
            return True, f"Sending audio '{os.path.basename(audio_path)}'"
            
        except Exception as e:
            return False, f"VLC error: {str(e)}"
    
    def stop_playback(self):
        """Stop audio playback"""
        # Stop VLC player
        if self.vlc_player:
            try:
                self.vlc_player.stop()
                self.vlc_player.release()
            except:
                pass
            self.vlc_player = None
        
        # Stop any other processes
        if self.current_process:
            try:
                self.current_process.terminate()
                self.current_process.wait(timeout=1)
            except:
                try:
                    self.current_process.kill()
                except:
                    pass
            self.current_process = None
    
    def get_playback_time(self):
        """Get current playback time in milliseconds"""
        if self.vlc_player:
            return self.vlc_player.get_time()
        return 0
    
    def get_media_length(self):
        """Get total media length in milliseconds"""
        if self.vlc_player:
            return self.vlc_player.get_length()
        return 0
    
    def is_playing(self):
        """Check if audio is playing"""
        if self.vlc_player:
            return self.vlc_player.is_playing()
        return False

class VirtualMicApp(QtWidgets.QWidget):
    """Virtual Microphone Simulator"""
    
    def __init__(self):
        super().__init__()
        self.mic = VirtualMicManager()
        self.setup_ui()
        
        # Setup virtual microphone
        QtCore.QTimer.singleShot(1000, self.setup_mic)
        
        # Setup progress timer
        self.progress_timer = QTimer()
        self.progress_timer.timeout.connect(self.update_progress)
        self.progress_timer.start(100)  # Update every 100ms
        
        # File count
        self.file_count = 0
    
    def setup_ui(self):
        """Setup UI with clean, professional design"""
        self.setWindowTitle("Virtual Microphone Simulator for Firefox by 4n54n")
        self.resize(750, 650)
        
        # Set window background
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
                font-family: 'Segoe UI', 'Arial', sans-serif;
            }
        """)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        self.setLayout(main_layout)
        
        # ==================== TERMINAL-LIKE STATUS DISPLAY ====================
        status_group = QtWidgets.QGroupBox("Status Console")
        status_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                color: #333333;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f5f5f5;
            }
        """)
        
        status_layout = QtWidgets.QVBoxLayout()
        status_layout.setContentsMargins(12, 20, 12, 12)
        
        # Terminal-like text display
        self.terminal_display = QtWidgets.QTextEdit()
        self.terminal_display.setReadOnly(True)
        self.terminal_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3c3c3c;
                border-radius: 4px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 12px;
                padding: 10px;
                selection-background-color: #264f78;
            }
        """)
        self.terminal_display.setMinimumHeight(120)
        self.terminal_display.setMaximumHeight(120)
        
        status_layout.addWidget(self.terminal_display)
        status_group.setLayout(status_layout)
        main_layout.addWidget(status_group)
        
        # ==================== CONTROL BUTTONS ====================
        control_frame = QtWidgets.QFrame()
        control_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.setSpacing(12)
        
        self.restart_btn = QtWidgets.QPushButton("Restart Virtual Mic")
        self.restart_btn.setFixedHeight(40)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border: 1px solid #444444;
                border-radius: 4px;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #666666;
                border: 1px solid #555555;
            }
            QPushButton:disabled {
                background-color: #aaaaaa;
                color: #777777;
                border: 1px solid #999999;
            }
        """)
        self.restart_btn.clicked.connect(self.setup_mic)
        
        self.browse_btn = QtWidgets.QPushButton("Browse Folder")
        self.browse_btn.setFixedHeight(40)
        self.browse_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
        """)
        self.browse_btn.clicked.connect(self.browse_folder)
        
        self.add_btn = QtWidgets.QPushButton("Add Files")
        self.add_btn.setFixedHeight(40)
        self.add_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 13px;
                padding: 8px 16px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
        """)
        self.add_btn.clicked.connect(self.add_files)
        
        control_layout.addWidget(self.restart_btn)
        control_layout.addWidget(self.browse_btn)
        control_layout.addWidget(self.add_btn)
        control_layout.addStretch()
        
        control_frame.setLayout(control_layout)
        main_layout.addWidget(control_frame)
        
        # ==================== AUDIO FILES SECTION ====================
        files_group = QtWidgets.QGroupBox("Audio Files")
        files_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 13px;
                border: 2px solid #cccccc;
                border-radius: 6px;
                margin-top: 5px;
                padding-top: 12px;
                color: #333333;
                background-color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                background-color: #f5f5f5;
            }
        """)
        
        files_layout = QtWidgets.QVBoxLayout()
        files_layout.setContentsMargins(12, 20, 12, 12)
        
        # File list with scroll
        self.file_list = QtWidgets.QListWidget()
        self.file_list.setSelectionMode(QtWidgets.QListWidget.SingleSelection)
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #dddddd;
                border-radius: 4px;
                font-size: 13px;
                color: #333333;
                outline: none;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:selected {
                background-color: #e8e8e8;
                color: #333333;
                border-left: 3px solid #555555;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QScrollBar:vertical {
                border: none;
                background-color: #f0f0f0;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #cccccc;
                border-radius: 6px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #aaaaaa;
            }
        """)
        self.file_list.setMinimumHeight(200)
        
        files_layout.addWidget(self.file_list)
        
        # File management buttons
        file_btn_layout = QtWidgets.QHBoxLayout()
        file_btn_layout.setSpacing(10)
        
        self.remove_btn = QtWidgets.QPushButton("Remove Selected")
        self.remove_btn.setFixedHeight(35)
        self.remove_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 12px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
        """)
        self.remove_btn.clicked.connect(self.remove_files)
        
        self.clear_btn = QtWidgets.QPushButton("Clear All")
        self.clear_btn.setFixedHeight(35)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffffff;
                color: #333333;
                border: 1px solid #cccccc;
                border-radius: 4px;
                font-size: 12px;
                padding: 6px 12px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border: 1px solid #bbbbbb;
            }
        """)
        self.clear_btn.clicked.connect(self.clear_files)
        
        file_btn_layout.addWidget(self.remove_btn)
        file_btn_layout.addWidget(self.clear_btn)
        file_btn_layout.addStretch()
        
        files_layout.addLayout(file_btn_layout)
        files_group.setLayout(files_layout)
        main_layout.addWidget(files_group)
        
        # ==================== PLAYBACK CONTROLS ====================
        playback_frame = QtWidgets.QFrame()
        playback_frame.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #dddddd;
                border-radius: 6px;
                padding: 15px;
            }
        """)
        
        playback_layout = QtWidgets.QVBoxLayout()
        playback_layout.setSpacing(12)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
                height: 20px;
                background-color: #f0f0f0;
            }
            QProgressBar::chunk {
                background-color: #4a90e2;
                border-radius: 4px;
            }
        """)
        self.progress_bar.setTextVisible(False)
        playback_layout.addWidget(self.progress_bar)
        
        # Control buttons
        control_btn_layout = QtWidgets.QHBoxLayout()
        control_btn_layout.setSpacing(15)
        
        self.play_btn = QtWidgets.QPushButton("Send Audio")
        self.play_btn.setFixedHeight(45)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: 1px solid #3a80d2;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #3a80d2;
                border: 1px solid #2a70c2;
            }
            QPushButton:disabled {
                background-color: #aaaaaa;
                color: #777777;
                border: 1px solid #999999;
            }
        """)
        self.play_btn.clicked.connect(self.play_audio)
        self.play_btn.setEnabled(False)
        
        self.stop_btn = QtWidgets.QPushButton("Stop")
        self.stop_btn.setFixedHeight(45)
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: 1px solid #d73c2c;
                border-radius: 4px;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #d73c2c;
                border: 1px solid #c72c1c;
            }
            QPushButton:disabled {
                background-color: #aaaaaa;
                color: #777777;
                border: 1px solid #999999;
            }
        """)
        self.stop_btn.clicked.connect(self.stop_audio)
        self.stop_btn.setEnabled(False)
        
        control_btn_layout.addWidget(self.play_btn)
        control_btn_layout.addWidget(self.stop_btn)
        control_btn_layout.addStretch()
        
        playback_layout.addLayout(control_btn_layout)
        playback_frame.setLayout(playback_layout)
        main_layout.addWidget(playback_frame)
        
        # ==================== STATUS BAR ====================
        status_bar = QtWidgets.QFrame()
        status_bar.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border-top: 1px solid #dddddd;
                padding: 8px;
            }
        """)
        
        status_layout = QtWidgets.QHBoxLayout()
        
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
            }
        """)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        
        # File count label
        self.file_count_label = QtWidgets.QLabel("Files: 0")
        self.file_count_label.setStyleSheet("""
            QLabel {
                color: #666666;
                font-size: 12px;
                font-style: italic;
            }
        """)
        
        status_layout.addWidget(self.file_count_label)
        status_bar.setLayout(status_layout)
        main_layout.addWidget(status_bar)
        
        # Current playback state
        self.current_file = None
        self.is_playing = False
    
    def log_to_terminal(self, message):
        """Add message to terminal-like display"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}"
        
        # Add to terminal display
        self.terminal_display.append(formatted_message)
        
        # Scroll to bottom
        self.terminal_display.verticalScrollBar().setValue(
            self.terminal_display.verticalScrollBar().maximum()
        )
        
        # Update status bar
        self.status_label.setText(message)
    
    def update_file_count(self):
        """Update file count display"""
        self.file_count = self.file_list.count()
        self.file_count_label.setText(f"Files: {self.file_count}")
    
    def setup_mic(self):
        """Setup virtual microphone"""
        self.log_to_terminal("Initializing virtual microphone 'Real4n54n'...")
        self.restart_btn.setEnabled(False)
        self.play_btn.setEnabled(False)
        
        # Run in thread to avoid freezing
        self.setup_thread = QtCore.QThread()
        self.setup_worker = SetupWorker(self.mic)
        self.setup_worker.moveToThread(self.setup_thread)
        
        self.setup_thread.started.connect(self.setup_worker.run)
        self.setup_worker.finished.connect(self.on_setup_complete)
        self.setup_worker.finished.connect(self.setup_thread.quit)
        self.setup_worker.finished.connect(self.setup_worker.deleteLater)
        self.setup_thread.finished.connect(self.setup_thread.deleteLater)
        
        self.setup_thread.start()
    
    def on_setup_complete(self, success, message):
        """Handle setup completion"""
        self.restart_btn.setEnabled(True)
        self.play_btn.setEnabled(success)
        
        if success:
            self.log_to_terminal(message)
            self.log_to_terminal("Virtual microphone ready for use")
            self.log_to_terminal("Select 'Real4n54n.monitor' as microphone input in other applications")
        else:
            self.log_to_terminal(f"ERROR: {message}")
    
    def browse_folder(self):
        """Browse folder and add all audio files"""
        folder = QFileDialog.getExistingDirectory(self, "Select Folder with Audio Files")
        if not folder:
            return
        
        # Supported audio extensions
        audio_extensions = {
            '.mp3', '.wav', '.ogg', '.flac', '.m4a', '.aac', '.wma',
            '.mp4', '.m4v', '.mkv', '.avi', '.mov', '.wmv'
        }
        
        added_count = 0
        for root, dirs, files in os.walk(folder):
            for file in files:
                if os.path.splitext(file)[1].lower() in audio_extensions:
                    file_path = os.path.join(root, file)
                    
                    # Check if already in list
                    existing = False
                    for i in range(self.file_list.count()):
                        item = self.file_list.item(i)
                        if item.data(QtCore.Qt.UserRole) == file_path:
                            existing = True
                            break
                    
                    if not existing:
                        item = QtWidgets.QListWidgetItem(file)
                        item.setData(QtCore.Qt.UserRole, file_path)
                        self.file_list.addItem(item)
                        added_count += 1
        
        if added_count > 0:
            self.log_to_terminal(f"Listed {added_count} audio files from folder")
            self.update_file_count()
        else:
            self.log_to_terminal("No audio files found in selected folder")
    
    def add_files(self):
        """Add individual audio files"""
        files, _ = QFileDialog.getOpenFileNames(
            self, "Select Audio Files", "",
            "Audio Files (*.mp3 *.wav *.ogg *.flac *.m4a *.aac *.wma *.mp4 *.m4v *.mkv *.avi *.mov *.wmv);;All Files (*)"
        )
        
        added_count = 0
        for file_path in files:
            if os.path.exists(file_path):
                # Check if already in list
                existing = False
                for i in range(self.file_list.count()):
                    item = self.file_list.item(i)
                    if item.data(QtCore.Qt.UserRole) == file_path:
                        existing = True
                        break
                
                if not existing:
                    item = QtWidgets.QListWidgetItem(os.path.basename(file_path))
                    item.setData(QtCore.Qt.UserRole, file_path)
                    self.file_list.addItem(item)
                    added_count += 1
        
        if added_count > 0:
            self.log_to_terminal(f"Added {added_count} audio files")
            self.update_file_count()
    
    def remove_files(self):
        """Remove selected files"""
        items = self.file_list.selectedItems()
        if not items:
            return
        
        for item in items:
            filename = item.text()
            self.file_list.takeItem(self.file_list.row(item))
            self.log_to_terminal(f"Removed '{filename}'")
        
        self.update_file_count()
    
    def clear_files(self):
        """Clear all files"""
        if self.file_list.count() > 0:
            self.file_list.clear()
            self.log_to_terminal("Cleared all audio files")
            self.update_file_count()
    
    def play_audio(self):
        """Play selected audio"""
        items = self.file_list.selectedItems()
        if not items:
            self.log_to_terminal("Please select an audio file first")
            return
        
        self.current_file = items[0].data(QtCore.Qt.UserRole)
        filename = os.path.basename(self.current_file)
        
        # Update UI
        self.play_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.log_to_terminal(f"Sending audio '{filename}'")
        
        # Start playback
        success, message = self.mic.play_audio_vlc(self.current_file)
        
        if success:
            self.is_playing = True
            self.play_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2a70c2;
                    color: white;
                    border: 1px solid #1a60b2;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 14px;
                    padding: 10px 20px;
                }
            """)
            
            # Check for playback completion
            self.check_playback_timer = QTimer()
            self.check_playback_timer.timeout.connect(self.check_playback_completion)
            self.check_playback_timer.start(500)
        else:
            self.log_to_terminal(f"ERROR: {message}")
            self.play_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
    
    def check_playback_completion(self):
        """Check if playback has completed"""
        if not self.mic.is_playing():
            self.check_playback_timer.stop()
            self.on_playback_finished()
    
    def on_playback_finished(self):
        """Handle playback finished"""
        self.is_playing = False
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: 1px solid #3a80d2;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #3a80d2;
                border: 1px solid #2a70c2;
            }
            QPushButton:disabled {
                background-color: #aaaaaa;
                color: #777777;
                border: 1px solid #999999;
            }
        """)
        
        if self.current_file:
            filename = os.path.basename(self.current_file)
            self.log_to_terminal(f"Finished sending '{filename}'")
            self.progress_bar.setValue(100)
    
    def stop_audio(self):
        """Stop audio playback"""
        self.mic.stop_playback()
        self.is_playing = False
        self.play_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: 1px solid #3a80d2;
                border-radius: 4px;
                font-weight: bold;
                font-size: 14px;
                padding: 10px 20px;
            }
            QPushButton:hover {
                background-color: #3a80d2;
                border: 1px solid #2a70c2;
            }
            QPushButton:disabled {
                background-color: #aaaaaa;
                color: #777777;
                border: 1px solid #999999;
            }
        """)
        self.log_to_terminal("Stopping audio...")
        self.progress_bar.setValue(0)
        
        if hasattr(self, 'check_playback_timer'):
            self.check_playback_timer.stop()
    
    def update_progress(self):
        """Update progress bar"""
        if self.is_playing and self.mic.is_playing():
            current_time = self.mic.get_playback_time()
            total_time = self.mic.get_media_length()
            
            if total_time > 0:
                progress = int((current_time / total_time) * 100)
                self.progress_bar.setValue(progress)
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.mic.stop_playback()
        self.mic.cleanup_all()
        event.accept()

class SetupWorker(QtCore.QObject):
    """Worker for setup"""
    finished = QtCore.pyqtSignal(bool, str)
    
    def __init__(self, mic):
        super().__init__()
        self.mic = mic
    
    def run(self):
        success, message = self.mic.setup()
        self.finished.emit(success, message)

def main():
    app = QtWidgets.QApplication(sys.argv)
    
    # Check requirements
    if not shutil.which("pactl"):
        QMessageBox.critical(None, "Error",
                           "pactl not found.\nInstall: sudo apt install pulseaudio-utils")
        return 1
    
    # Check if VLC is available
    try:
        import vlc
    except ImportError:
        QMessageBox.critical(None, "Error",
                           "python-vlc not found.\nInstall: pip install python-vlc\n"
                           "Also install VLC: sudo apt install vlc")
        return 1
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create and show window
    window = VirtualMicApp()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()