from PyQt5.QtWidgets import QPlainTextEdit
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)

    def keyPressEvent(self, event):
        key = event.key()
        char = event.text()
        cursor = self.textCursor()

        pairs = {
            '"': '"',
            "'": "'",
            '(': ')',
            '[': ']',
            '{': '}'
        }

        if key == Qt.Key_Return or key == Qt.Key_Enter:
            # Get current block (line) text without modifying cursor
            current_block = cursor.block()
            current_line = current_block.text()

            # Figure out leading whitespace
            indent = ""
            for c in current_line:
                if c in [' ', '\t']:
                    indent += c
                else:
                    break

            # Add extra indent if line ends in block opener
            if current_line.strip().endswith((':', '{', '[', '(')):
                indent += "\t"

            super().keyPressEvent(event)
            cursor = self.textCursor()
            cursor.insertText(indent)
            return

        # Handle paired characters
        if char in pairs:
            closing = pairs[char]
            super().keyPressEvent(event)
            cursor = self.textCursor()
            cursor.insertText(closing)
            cursor.movePosition(QTextCursor.Left)
            self.setTextCursor(cursor)
            return

        elif char in pairs.values():
            next_char = self.toPlainText()[cursor.position():cursor.position()+1]
            if next_char == char:
                cursor.movePosition(QTextCursor.Right)
                self.setTextCursor(cursor)
                return

        super().keyPressEvent(event)

