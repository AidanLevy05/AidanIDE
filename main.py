import sys
from pathlib import Path
from datetime import datetime
import subprocess 
import os 
import shlex
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPlainTextEdit, QLabel, QFileDialog, QTreeWidget, QTreeWidgetItem,
    QSplitter, QMessageBox, QAction, QMenuBar, QLineEdit, QPushButton,
    QTabWidget
)
from PyQt5.QtCore import Qt, QProcess, QIODevice, QByteArray
from highlighter import PythonHighlighter, CHighlighter, DummyHighlighter
from codeeditor import CodeEditor

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AidanIDE")
        self.showMaximized()
        self.default_save_load_path = str(Path.home())
        self.process = None
        self.current_dir = os.getcwd()
        self.env = os.environ.copy()
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_layout = QHBoxLayout()

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)

        self.toggle_sidebar_btn = QPushButton("☰")
        self.toggle_sidebar_btn.setFixedWidth(30)
        self.toggle_sidebar_btn.setCheckable(True)
        self.toggle_sidebar_btn.setChecked(True)
        self.toggle_sidebar_btn.clicked.connect(self.toggle_sidebar)
        self.toggle_sidebar_btn.setStyleSheet("""
            QPushButton {
                background-color: #44475a;
                color: white;
                font-weight: bold;
                border: none;
                font-size: 18px;
            }
            QPushButton:hover {
                background-color: #6272a4;
            }
            QPushButton:checked {
                background-color: #50fa7b;
                color: black;
            }
        """)

        self.sidebar = QTreeWidget()
        self.sidebar.setHeaderHidden(True)
        self.sidebar.setFixedWidth(250)
        self.sidebar.itemDoubleClicked.connect(self.load_file_from_tree)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addWidget(self.toggle_sidebar_btn)
        sidebar_layout.addWidget(self.sidebar)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(sidebar_layout)

        self.label = QLabel("Untitled")
        self.current_file = None

        # Create the first text edit when initializing
        self.text_edit = CodeEditor()
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                background-color: #282a36;
                color: #f8f8f2;
                font-family: Consolas, Courier, monospace;
                font-size: 14px;
                padding: 10px;
            }
        """)

        self.syntax_toggle = QPushButton("✓ Syntax Highlighting")
        self.syntax_toggle.setCheckable(True)
        self.syntax_toggle.setChecked(True)
        self.syntax_toggle.setStyleSheet("""
            QPushButton {
                background-color: #6272a4;
                color: white;
                font-weight: bold;
                border: none;
                padding: 4px;
            }
            QPushButton:checked {
                background-color: #50fa7b;
                color: black;
            }
        """)
        self.syntax_toggle.clicked.connect(self.toggle_syntax)

        label_layout = QHBoxLayout()
        label_layout.addWidget(self.label)
        label_layout.addStretch()
        label_layout.addWidget(self.syntax_toggle)

        editor_layout = QVBoxLayout()
        editor_layout.addLayout(label_layout)
        editor_layout.addWidget(self.text_edit)

        editor_widget = QWidget()
        editor_widget.setLayout(editor_layout)

        self.pwd_label = QLabel(f"PWD: {os.getcwd()}")
        self.pwd_label.setStyleSheet("""
            color: #50fa7b;
            font-family: Consolas, Courier, monospace;
            font-size: 13px;
            padding: 5px;
        """)

        self.close_terminal = QPushButton("x")
        self.close_terminal.setFixedWidth(25)
        self.close_terminal.setStyleSheet("""
            QPushButton {
                background-color: #ff5555;
                color: white;
                border: none;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #ff4444;
            }
        """)
        self.close_terminal.clicked.connect(self.toggle_terminal)

        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(self.pwd_label)
        pwd_layout.addStretch()
        pwd_layout.addWidget(self.close_terminal)

        self.terminal = QPlainTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1f29;
                color: #50fa7b;
                font-family: Consolas, Courier, monospace;
                font-size: 13px;
                padding: 10px;
            }
        """)

        self.terminal_input = QLineEdit()
        self.terminal_input.returnPressed.connect(self.execute_command)

        terminal_layout = QVBoxLayout()
        terminal_layout.addLayout(pwd_layout)
        terminal_layout.addWidget(self.terminal)
        terminal_layout.addWidget(self.terminal_input)

        terminal_widget = QWidget()
        terminal_widget.setLayout(terminal_layout)
        terminal_widget.hide()
        self.terminal_widget = terminal_widget

        vertical_splitter = QSplitter(Qt.Vertical)
        vertical_splitter.addWidget(editor_widget)
        vertical_splitter.addWidget(terminal_widget)
        vertical_splitter.setSizes([800, 200])
        self.vertical_splitter = vertical_splitter

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(sidebar_widget)
        splitter.addWidget(vertical_splitter)
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)

        menu_bar = QMenuBar(self)
        file_menu = menu_bar.addMenu("File")
        terminal_menu = menu_bar.addMenu("Terminal")
        help_menu = menu_bar.addMenu("Help")

        open_folder_action = QAction("Open Folder", self)
        open_folder_action.setShortcut("Ctrl+Shift+O")
        open_folder_action.triggered.connect(self.open_folder)

        save_action = QAction("Save Note", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self.save_note)

        load_action = QAction("Load Note", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self.load_note)

        new_file_action = QAction("New File", self)
        new_file_action.setShortcut("Ctrl+N")
        new_file_action.triggered.connect(self.new_file)

        terminal_action = QAction("Open Terminal", self)
        terminal_action.setShortcut("Ctrl+T")
        terminal_action.triggered.connect(self.toggle_terminal)

        help_action = QAction("Show shortcuts", self)
        help_action.setShortcut("Ctrl+H")
        help_action.triggered.connect(self.show_shortcuts)

        file_menu.addAction(open_folder_action)
        file_menu.addAction(save_action)
        file_menu.addAction(load_action)
        file_menu.addAction(new_file_action)
        terminal_menu.addAction(terminal_action)
        help_menu.addAction(help_action)

        self.setMenuBar(menu_bar)

    def closeEvent(self, event):
        editor = self.tabs.currentWidget()
        
        if editor is None:
            event.accept() 
            return

        current_file = editor.property("file_path")
        is_modified = editor.toPlainText() != editor.document().originalPlainText()

        if current_file is None and is_modified:
            # If no filename, prompt to save
            reply = QMessageBox.question(
                self,
                "Save File",
                "You have unsaved changes. Do you want to save the file?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )
            
            if reply == QMessageBox.Save:
                self.save_note()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()

        elif current_file is not None:
            # If file already has a name, auto-save
            self.save_note()
            event.accept()

        else:
            # No changes to save, just close
            event.accept()

    def toggle_sidebar(self):
        self.sidebar.setVisible(self.toggle_sidebar_btn.isChecked())

    def new_file(self):
        current_editor = self.tabs.currentWidget()
        if current_editor and current_editor.toPlainText():
            reply = QMessageBox.question(
                self,
                "Confirm",
                "Discard current note and start a new one?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        editor = CodeEditor()
        editor.setPlaceholderText("Start typing your note here...")
        editor.setProperty("file_path", None)
        PythonHighlighter(editor.document())

        index = self.tabs.addTab(editor, "Untitled")
        self.tabs.setCurrentIndex(index)
        self.label.setText("Untitled")

    def toggle_terminal(self):
        if self.terminal_widget.isVisible():
            self.last_splitter_sizes = self.vertical_splitter.sizes()
            self.terminal_widget.hide()
        else:
            self.terminal_widget.show()
            if hasattr(self, "last_splitter_sizes"):
                self.vertical_splitter.setSizes(self.last_splitter_sizes)

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
            editor = self.text_edit
            if not editor:
                return

            file_path = self.current_file
            content = editor.toPlainText()

            if not file_path:
                timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
                suggested_filename = f"note_{timestamp}.txt"
                options = QFileDialog.Options()
                options |= QFileDialog.DontUseNativeDialog

                file_path, _ = QFileDialog.getSaveFileName(
                    self,
                    "Save Note",
                    str(Path(self.default_save_load_path) / suggested_filename),
                    "All Files (*);;Text Files (*.txt);;Python Files (*.py);;C/C++ Files (*.c *.cpp *.h)",
                    options=options
                )

                if not file_path:
                    return

                self.current_file = file_path

            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)

                self.label.setText(Path(file_path).name)
                editor.document().setModified(False)

            except Exception as e:
                QMessageBox.critical(self, "Error Saving File", str(e))

    def load_note(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Note",
            self.default_save_load_path,
            "All Files (*);;C/C++ Files (*.c *.cpp *.h);;Python Files (*.py);;Text Files (*.txt)",
            options=options
        )

        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            editor = CodeEditor()
            editor.setPlainText(content)
            editor.setProperty("file_path", file_path)
            PythonHighlighter(editor.document())

            index = self.tabs.addTab(editor, Path(file_path).name)
            self.tabs.setCurrentIndex(index)
            self.label.setText(Path(file_path).name)
            self.toggle_syntax()

    def show_shortcuts(self):
        shortcuts = [
            "Ctrl+S — Save Note",
            "Ctrl+O — Load Note",
            "Ctrl+N — New File",
            "Ctrl+H — Show Shortcuts",
            "Ctrl+T — Toggle Terminal",
        ]
        QMessageBox.information(
            self,
            "Keyboard Shortcuts",
            "\n".join(shortcuts)
        )

    def toggle_syntax(self):
        if not self.syntax_toggle.isChecked():
            self.highlighter = DummyHighlighter(self.text_edit.document())
            return

        if self.current_file:
            file_ext = Path(self.current_file).suffix.lower()
        else:
            file_ext = ''

        if file_ext in [".py"]:
            self.highlighter = PythonHighlighter(self.text_edit.document())
        elif file_ext in [".c", ".cpp", ".h"]:
            self.highlighter = CHighlighter(self.text_edit.document())
        else:
            self.highlighter = DummyHighlighter(self.text_edit.document())

    def open_folder(self):
        dialog = QFileDialog(self, "Open Folder")
        dialog.setDirectory(str(Path.home()))
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setOption(QFileDialog.DontUseCustomDirectoryIcons, True)

        def reject_external_navigation():
            current = Path(dialog.directory().absolutePath())
            if not str(current).startswith(str(Path.home())):
                dialog.setDirectory(str(Path.home()))

        dialog.directoryEntered.connect(lambda _: reject_external_navigation())

        if dialog.exec_() == QFileDialog.Accepted:
            folder_path = dialog.selectedFiles()[0]
            self.sidebar.clear()
            self.build_tree(folder_path)

    def build_tree(self, root_path):
        def add_items(parent_item, path):
            for entry in sorted(os.listdir(path)):
                full_path = os.path.join(path, entry)
                item = QTreeWidgetItem([entry])
                item.setData(0, Qt.UserRole, full_path)
                parent_item.addChild(item)
                if os.path.isdir(full_path):
                    add_items(item, full_path)
        root_item = QTreeWidgetItem([os.path.basename(root_path)])
        root_item.setData(0, Qt.UserRole, root_path)
        self.sidebar.addTopLevelItem(root_item)
        add_items(root_item, root_path)
        root_item.setExpanded(True)

    def load_file_from_tree(self, item, column):
        path = item.data(0, Qt.UserRole)
        if os.path.isfile(path):
            with open(path, 'r') as f:
                self.text_edit.setPlainText(f.read())
            self.current_file = path
            self.label.setText(Path(path).name)
            self.toggle_syntax()

    def close_tab(self, index):
        tab_widget = self.tabs.widget(index) 
        current_file = tab_widget.property("file_path")

        if tab_widget.toPlainText() != tab_widget.document().originalPlainText():
            reply = QMessageBox.question(
                self,
                "Save File",
                "You have unsaved changes. Do you want to save the file?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save_note()
            elif reply == QMessageBox.Cancel:
                return

        self.tabs.removeTab(index) 


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
        QFileDialog {
            background-color: #282a36;
            color: #f8f8f2;
        }
        QPushButton {
            background-color: #282a36;
            color: #f8f8f2;
            border: none;
            padding: 5px;
        }
        QPushButton:hover {
            background-color: #7080d0;
        }
        QListView, QTreeView {
            background-color: #1e1f29;
            color: #f8f8f2;
            selection-background-color: #44475a;
            selection-color: #f8f8f2;
        }
    """)

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
