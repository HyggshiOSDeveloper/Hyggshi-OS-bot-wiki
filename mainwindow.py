import sys
import os
import subprocess
import importlib.util
import psutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QTextEdit,
    QVBoxLayout, QHBoxLayout, QMessageBox, QCheckBox,
    QGroupBox, QScrollArea, QLabel, QFrame
)
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtGui import QFont

class WikiBotWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Wiki Bot Manager")
        self.setGeometry(300, 100, 900, 700)
        self.process = None
        self.selected_wikis = set()
        self.dark_mode_enabled = False

        self.create_ui()
        
        # Initialize timer for log updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_log)
        self.timer.start(2000)
        
        # Initial setup
        self.load_log()
        self.check_bot_status()

    def create_ui(self):
        """Create the user interface"""
        # Main control buttons
        self.run_button = QPushButton("▶ Chạy Bot")
        self.run_button.clicked.connect(self.run_bot)
        self.run_button.setMinimumHeight(35)

        self.stop_button = QPushButton("⏹ Dừng Bot")
        self.stop_button.clicked.connect(self.stop_bot)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(35)

        self.refresh_button = QPushButton("🔁 Làm mới log")
        self.refresh_button.clicked.connect(self.load_log)
        self.refresh_button.setMinimumHeight(35)

        # File management buttons
        self.open_config_button = QPushButton("⚙ Mở wikis_config.py")
        self.open_config_button.clicked.connect(self.open_config)
        self.open_config_button.setMinimumHeight(35)

        self.open_env_button = QPushButton("🔐 Mở .env")
        self.open_env_button.clicked.connect(self.open_env)
        self.open_env_button.setMinimumHeight(35)

        # UI options
        self.darkmode_checkbox = QCheckBox("🌙 Dark Mode")
        self.darkmode_checkbox.stateChanged.connect(self.toggle_dark_mode)

        # Status indicator
        self.status_label = QLabel("⚫ Bot không chạy")
        self.status_label.setStyleSheet("font-weight: bold; padding: 5px; color: red;")

        # Wiki selection controls
        self.select_all_checkbox = QCheckBox("Chạy tất cả wiki")
        self.select_all_checkbox.stateChanged.connect(self.toggle_all_wikis)

        # Wiki list container
        self.wiki_groupbox = QGroupBox("📁 Trình Quản Lý Wiki")
        self.wiki_layout = QVBoxLayout()
        self.wiki_checkboxes = []

        # Scrollable area for wiki list
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_widget.setLayout(self.wiki_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(120)
        scroll_area.setMaximumHeight(180)

        # Load available wikis
        self.load_wiki_list()

        # Add scroll area to groupbox
        groupbox_layout = QVBoxLayout()
        groupbox_layout.addWidget(scroll_area)
        self.wiki_groupbox.setLayout(groupbox_layout)

        # Log display
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 9))
        self.log_view.setMinimumHeight(300)

        # Layout assembly
        self._setup_layout()

    def _setup_layout(self):
        """Setup the main layout structure"""
        # Top button row
        top_buttons = QHBoxLayout()
        top_buttons.addWidget(self.run_button)
        top_buttons.addWidget(self.stop_button)
        top_buttons.addWidget(self.refresh_button)
        top_buttons.addStretch()
        top_buttons.addWidget(self.darkmode_checkbox)

        # File management row
        file_buttons = QHBoxLayout()
        file_buttons.addWidget(self.open_config_button)
        file_buttons.addWidget(self.open_env_button)
        file_buttons.addStretch()
        file_buttons.addWidget(self.status_label)

        # Visual separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)

        # Main layout
        layout = QVBoxLayout()
        layout.addLayout(top_buttons)
        layout.addLayout(file_buttons)
        layout.addWidget(separator)
        layout.addWidget(self.select_all_checkbox)
        layout.addWidget(self.wiki_groupbox)
        layout.addWidget(QLabel("📋 Log Output:"))
        layout.addWidget(self.log_view)

        self.setLayout(layout)

    def load_wiki_list(self):
        """Load wiki list from config file with comprehensive error handling"""
        # Clear existing checkboxes
        self._clear_wiki_checkboxes()

        config_path = "wikis_config.py"
        
        if not os.path.exists(config_path):
            self._show_wiki_error("❌ Không tìm thấy file wikis_config.py", "red")
            return

        try:
            # Load config module
            spec = importlib.util.spec_from_file_location("wikis_config", config_path)
            if spec is None or spec.loader is None:
                raise ImportError("Cannot load config module")
                
            wiki_config = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(wiki_config)
            
            # Get wikis list
            wikis = getattr(wiki_config, "WIKIS", [])
            
            if not wikis:
                self._show_wiki_error("⚠️ Không có wiki nào trong config", "orange")
                return

            # Create checkboxes for each wiki
            self._create_wiki_checkboxes(wikis)
            self._show_wiki_success(f"✅ Đã tải {len(wikis)} wiki")

        except Exception as e:
            self._show_wiki_error(f"❌ Lỗi khi tải wiki config:\n{str(e)}", "red")

    def _clear_wiki_checkboxes(self):
        """Clear all existing wiki checkboxes"""
        for cb in self.wiki_checkboxes:
            cb.deleteLater()
        self.wiki_checkboxes.clear()

    def _create_wiki_checkboxes(self, wikis):
        """Create checkboxes for wiki list"""
        for i, wiki in enumerate(wikis):
            if not isinstance(wiki, dict):
                continue
                
            name = (wiki.get("desc") or 
                   wiki.get("hostcheck") or 
                   f"Wiki {i+1}")
            
            cb = QCheckBox(name)
            cb.stateChanged.connect(self.update_selected_wikis)
            self.wiki_layout.addWidget(cb)
            self.wiki_checkboxes.append(cb)

    def _show_wiki_error(self, message, color):
        """Show error message in wiki area"""
        error_label = QLabel(message)
        error_label.setStyleSheet(f"color: {color}; padding: 10px;")
        error_label.setWordWrap(True)
        self.wiki_layout.addWidget(error_label)

    def _show_wiki_success(self, message):
        """Show success message in wiki area"""
        success_label = QLabel(message)
        success_label.setStyleSheet("color: green; font-size: 11px; padding: 5px;")
        self.wiki_layout.addWidget(success_label)

    def update_selected_wikis(self):
        """Update the set of selected wikis"""
        self.selected_wikis = {
            cb.text() for cb in self.wiki_checkboxes if cb.isChecked()
        }

    def toggle_all_wikis(self, state):
        """Toggle all wiki checkboxes on/off"""
        checked = state == Qt.Checked
        for cb in self.wiki_checkboxes:
            cb.setChecked(checked)

    def check_bot_status(self):
        """Check if bot process is currently running"""
        self.process = None
        current_dir = os.getcwd()
        
        try:
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline', [])
                    proc_cwd = proc_info.get('cwd', '')
                    
                    if self._is_bot_process(cmdline, proc_cwd, current_dir):
                        self.process = proc
                        self._update_status(True, "🟢 Bot đang chạy", "green")
                        return
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
                    
        except Exception:
            pass
        
        self._update_status(False, "⚫ Bot không chạy", "red")

    def _is_bot_process(self, cmdline, proc_cwd, current_dir):
        """Check if process matches our bot criteria"""
        return (cmdline and len(cmdline) >= 2 and 
                any(python in cmdline[0].lower() for python in ['python', 'python.exe']) and
                'main.py' in cmdline[1] and
                proc_cwd == current_dir)

    def _update_status(self, running, text, color):
        """Update the bot status display"""
        self.stop_button.setEnabled(running)
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: bold; padding: 5px;")

    def run_bot(self):
        """Start the wiki bot with proper validation"""
        # Check if already running
        self.check_bot_status()
        if self.stop_button.isEnabled():
            QMessageBox.warning(self, "Đang chạy", "Bot đã đang chạy rồi.")
            return

        # Validate selection
        self.update_selected_wikis()
        if not self.select_all_checkbox.isChecked() and not self.selected_wikis:
            QMessageBox.warning(self, "Chưa chọn wiki", 
                              "Vui lòng chọn ít nhất một wiki hoặc bật 'Chạy tất cả wiki'.")
            return

        # Check main.py exists
        if not os.path.exists("main.py"):
            QMessageBox.critical(self, "Lỗi", "Không tìm thấy file main.py")
            return

        try:
            self._start_bot_process()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể chạy bot:\n{str(e)}")

    def _start_bot_process(self):
        """Start the bot process"""
        # Set environment variable for wiki filtering
        wiki_filter = ("ALL" if self.select_all_checkbox.isChecked() 
                      else ",".join(self.selected_wikis))
        os.environ["WIKI_FILTER"] = wiki_filter

        # Create subprocess
        if os.name == 'nt':  # Windows
            self.process = subprocess.Popen(
                ["python", "main.py"],
                creationflags=subprocess.CREATE_NO_WINDOW,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.getcwd()
            )
        else:  # Unix/Linux/Mac
            self.process = subprocess.Popen(
                ["python", "main.py"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.getcwd()
            )
        
        # Convert to psutil Process for better control
        try:
            self.process = psutil.Process(self.process.pid)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        
        self._update_status(True, "🟢 Bot đang chạy", "green")
        QMessageBox.information(self, "Đã chạy", "Wiki Bot đang chạy.")

    def stop_bot(self):
        """Stop the wiki bot with comprehensive process termination"""
        killed_processes = []
        current_dir = os.getcwd()
        
        try:
            # Method 1: Kill stored process
            if self.process:
                killed_processes.extend(self._terminate_process_tree(self.process))

            # Method 2: Search and kill matching processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
                try:
                    proc_info = proc.info
                    cmdline = proc_info.get('cmdline')
                    proc_cwd = proc_info.get('cwd')
                    
                    if (cmdline and proc_cwd and 
                        self._is_bot_process(cmdline, proc_cwd, current_dir)):
                        killed_processes.extend(self._terminate_process_tree(proc))
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue

            # Method 3: Windows fallback
            if not killed_processes and os.name == 'nt':
                self._windows_force_kill()

            # Update UI state
            self._reset_bot_state()
            
            # Show result
            if killed_processes:
                QMessageBox.information(self, "Đã dừng", 
                                      f"Bot đã được dừng hoàn toàn. "
                                      f"Đã dừng {len(killed_processes)} tiến trình.")
            else:
                QMessageBox.information(self, "Không chạy", "Không tìm thấy bot đang chạy.")
                
        except Exception as e:
            self._reset_bot_state()
            QMessageBox.critical(self, "Lỗi", f"Lỗi khi dừng bot:\n{str(e)}")

    def _terminate_process_tree(self, process):
        """Terminate a process and its children"""
        killed = []
        try:
            if hasattr(process, 'is_running') and process.is_running():
                # Kill children first
                try:
                    children = process.children(recursive=True)
                    for child in children:
                        try:
                            child.terminate()
                            killed.append(child.pid)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                    
                    # Wait for children
                    if children:
                        psutil.wait_procs(children, timeout=3)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
                
                # Kill main process
                process.terminate()
                killed.append(process.pid)
                try:
                    process.wait(timeout=3)
                except psutil.TimeoutExpired:
                    process.kill()
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied, AttributeError):
            pass
        
        return killed

    def _windows_force_kill(self):
        """Force kill Python processes on Windows (fallback)"""
        try:
            result = subprocess.run(
                ['tasklist', '/FI', 'IMAGENAME eq python.exe', '/FO', 'CSV'], 
                capture_output=True, text=True, timeout=10
            )
            if result.stdout and 'main.py' in result.stdout:
                subprocess.run(['taskkill', '/F', '/IM', 'python.exe'], 
                             capture_output=True, timeout=10)
        except Exception:
            pass

    def _reset_bot_state(self):
        """Reset bot state after stopping"""
        self.process = None
        self._update_status(False, "⚫ Bot không chạy", "red")

    def load_log(self):
        """Load and display log file content"""
        log_path = "log.txt"
        
        if not os.path.exists(log_path):
            self.log_view.setPlainText("[Thông tin] Chưa có file log.txt")
            return

        try:
            # Try UTF-8 encoding first
            content = self._read_file_with_encoding(log_path, "utf-8")
            if content is None:
                # Fallback to latin1
                content = self._read_file_with_encoding(log_path, "latin-1")
            
            if content is None:
                self.log_view.setPlainText("[Lỗi] Không thể đọc file log với bất kỳ encoding nào")
                return
            
            if content.strip():
                self.log_view.setPlainText(content)
                self._scroll_to_bottom()
            else:
                self.log_view.setPlainText("[Thông tin] File log trống")
                
        except Exception as e:
            self.log_view.setPlainText(f"[Lỗi] Không đọc được log.txt:\n{str(e)}")

    def _read_file_with_encoding(self, filepath, encoding):
        """Try to read file with specific encoding"""
        try:
            with open(filepath, "r", encoding=encoding) as f:
                return f.read()
        except (UnicodeDecodeError, UnicodeError):
            return None

    def _scroll_to_bottom(self):
        """Scroll log view to bottom"""
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.End)
        self.log_view.setTextCursor(cursor)

    def open_config(self):
        """Open wikis_config.py file"""
        self._open_file("wikis_config.py", "wikis_config.py")

    def open_env(self):
        """Open .env file"""
        self._open_file(".env", ".env")

    def _open_file(self, filename, display_name):
        """Generic file opener with cross-platform support"""
        if not os.path.exists(filename):
            QMessageBox.warning(self, "Không tìm thấy", f"File {display_name} không tồn tại")
            return

        try:
            if os.name == 'nt':  # Windows
                os.startfile(filename)
            elif os.name == 'posix':  # Unix/Linux/Mac
                subprocess.run(["xdg-open", filename], check=False)
            else:
                QMessageBox.information(self, "Thông tin", 
                                      f"Vui lòng mở file {display_name} bằng text editor")
                
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không mở được file:\n{str(e)}")

    def toggle_dark_mode(self, state):
        """Toggle between light and dark theme"""
        if state == Qt.Checked:
            self.setStyleSheet(self._get_dark_stylesheet())
            self.dark_mode_enabled = True
        else:
            self.setStyleSheet("")
            self.dark_mode_enabled = False

    def _get_dark_stylesheet(self):
        """Get dark mode stylesheet"""
        return """
            QWidget { 
                background-color: #2d2d2d; 
                color: #dddddd; 
            }
            QPushButton { 
                background-color: #3c3c3c; 
                color: white; 
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #4c4c4c;
            }
            QPushButton:pressed {
                background-color: #2c2c2c;
            }
            QPushButton:disabled {
                background-color: #1c1c1c;
                color: #666;
            }
            QCheckBox { 
                color: #dddddd; 
            }
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #dddddd; 
                border: 1px solid #444;
            }
            QGroupBox { 
                border: 1px solid #444; 
                margin-top: 10px; 
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QScrollArea {
                border: 1px solid #444;
            }
            QLabel {
                color: #dddddd;
            }
        """

    def closeEvent(self, event):
        """Handle application close event"""
        if self._is_bot_running():
            reply = QMessageBox.question(
                self, 'Xác nhận', 
                'Bot đang chạy. Bạn có muốn dừng bot trước khi thoát?',
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Yes:
                self.stop_bot()
                event.accept()
            elif reply == QMessageBox.No:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def _is_bot_running(self):
        """Check if bot is currently running"""
        try:
            return (self.process and 
                   hasattr(self.process, 'is_running') and 
                   self.process.is_running())
        except (psutil.NoSuchProcess, AttributeError):
            return False

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    app.setApplicationName("Wiki Bot Manager")
    
    # Set application icon if available
    if os.path.exists("icon.ico"):
        app.setWindowIcon(app.style().standardIcon(app.style().SP_ComputerIcon))
    
    window = WikiBotWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()