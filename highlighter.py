from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
        self.rules = []

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            "def", "class", "if", "elif", "else", "try", "except", "finally",
            "while", "for", "in", "return", "import", "from", "as", "with",
            "pass", "break", "continue", "raise", "lambda", "yield", "assert",
            "True", "False", "None"
        ]

        for word in keywords:
            pattern = QRegExp(rf"\b{word}\b")
            self.rules.append((pattern, keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))
        self.rules.append((QRegExp(r'"[^"]*"'), string_format))
        self.rules.append((QRegExp(r"'[^']*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        comment_format.setFontItalic(True)
        self.rules.append((QRegExp(r"#.*"), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)
