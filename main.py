import sys
from pathlib import Path
from datetime import datetime
import subprocess 
import os 
import shlex
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QLabel, QFileDialog, QListWidget,
    QSplitter, QMessageBox, QAction, QMenuBar, QLineEdit
)
from PyQt5.QtCore import Qt, QProcess, QIODevice, QByteArray
from highlighter import PythonHighlighter

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AidanIDE")
        self.showMaximized()
        self.init_ui()
        self.default_save_load_path = str(Path(__file__).resolve().parent.parent / "data" / "notes")
        self.process = None
        self.current_dir = os.getcwd()
        self.env = os.environ.copy()

    def init_ui(self):
        # Central widget and layout
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        # Sidebar
        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(200)

        # Editor layout
        editor_layout = QVBoxLayout()
        self.label = QLabel("Untitled")
        self.current_file = None
        self.text_edit = QPlainTextEdit()
        self.text_edit.setPlaceholderText("Start typing your note here...")

        # Syntax highlighting
        PythonHighlighter(self.text_edit.document())

        # Editor stylesheet
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #282a36;
                color: #f8f8f2;
                font-family: Consolas, Courier, monospace;
                font-size: 14px;
                padding: 10px;
            }
        """)

        editor_layout.addWidget(self.label)
        editor_layout.addWidget(self.text_edit)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        # PWD label
        self.pwd_label = QLabel(f"PWD: {os.getcwd()}")
        self.pwd_label.setStyleSheet("""
            color: #50fa7b;
            font-family: Consolas, Courier, monospace;
            font-size: 13px;
            padding: 5px;
        """)

        # Terminal widget setup
        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.execute_command)

        terminal_layout = QVBoxLayout()
        terminal_layout.addWidget(self.pwd_label)
        terminal_layout.addWidget(self.terminal)
        terminal_layout.addWidget(self.terminal_input)

        terminal_widget = QWidget()
        terminal_widget.setLayout(terminal_layout)

        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1f29;
                color: #50fa7b;
                font-family: Consolas, Courier, monospace;
                font-size: 13px;
                padding: 10px;
            }
        """)
        terminal_widget.hide()
        self.terminal_widget = terminal_widget

        # Vertical splitter for editor and terminal
        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(editor_widget)
        vertical_splitter.addWidget(terminal_widget)
        vertical_splitter.setSizes([800, 200])

        # Splitter layout
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.sidebar)
        splitter.addWidget(vertical_splitter)
        splitter.setStretchFactor(1, 1)

        # Add to main layout
        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        # Menu Bar
        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("File")
        terminal_menu = menu_bar.addMenu("Terminal")

        save_action = QAction("Save Note", self)
        save_action.triggered.connect(self.save_note)

        load_action = QAction("Load Note", self)
        load_action.triggered.connect(self.load_note)

        new_file_action = QAction("New File", self)
        new_file_action.triggered.connect(self.new_file)

        terminal_action = QAction("Open Terminal", self)
        terminal_action.triggered.connect(self.toggle_terminal)

        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addAction(new_file_action)
        terminal_menu.addAction(terminal_action)

        self.setMenuBar(menu_bar)

    def new_file(self):
        if self.text_edit.toPlainText():
            reply = QMessageBox.question(
                self,
                "Confirm",
                "Discard current note and start a new one?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        self.text_edit.clear()
        self.label.setText("Untitled")
        self.current_file = None

    def toggle_terminal(self):
        if self.terminal_widget.isVisible():
            self.terminal_widget.hide()
        else:
            self.terminal_widget.show()

    def execute_command(self):
        command = self.terminal_input.text()
        self.terminal.appendPlainText(f"$ {command}")
        self.terminal_input.clear()

        # Special handling for directory change
        if command.startswith('cd '):
            try:
                new_dir = command.split(' ', 1)[1]
                new_path = os.path.expanduser(new_dir)
                os.chdir(new_path)
                current_dir = os.getcwd()

                self.pwd_label.setText(f"PWD: {current_dir}")
                return
            except Exception as e:
                self.terminal.appendPlainText(f"Error changing directory: {str(e)}")
                return

        # Existing QProcess setup
        if self.process is None:
            self.process = QProcess()
            self.process.readyReadStandardOutput.connect(self.handle_stdout)
            self.process.readyReadStandardError.connect(self.handle_stderr)
            self.process.finished.connect(self.process_finished)

        # Start the process with shell=True to handle complex commands
        self.process.start('bash', ['-c', command])

    def handle_stdout(self):
        data = self.process.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.terminal.appendPlainText(stdout)

    def handle_stderr(self):
        data = self.process.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        self.terminal.appendPlainText(stderr)

    def process_finished(self):
        self.process = None

    def save_note(self):
        suggested_filename = f"note_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Note", 
            str(Path(self.default_save_load_path) / suggested_filename), 
            "Text Files (*.txt)"
        )
        if file_path:
            with open(file_path, 'w') as f:
                f.write(self.text_edit.toPlainText())
            self.current_file = file_path 
            self.label.setText(Path(file_path).name)

    def load_note(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open Note", self.default_save_load_path, "Text Files (*.txt)")
        if file_path:
            with open(file_path, 'r') as f:
                self.text_edit.setPlainText(f.read())
            self.current_file = file_path 
            self.label.setText(Path(file_path).name)

if __name__ == "__main__":
    app = QApplication(sys.argv)

    app.setStyleSheet("""
        QWidget {
            background-color: #282a36;
            color: #f8f8f2;
            font-family: Consolas;
            font-size: 13px;
        }
        QListWidget {
            background-color: #1e1f29;
            border: none;
        }
        QLabel {
            color: #f8f8f2;
        }
        QMenuBar::item:selected {
            background-color: #44475a;
        }
        QMenu::item:selected {
            background-color: #6272a4;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())