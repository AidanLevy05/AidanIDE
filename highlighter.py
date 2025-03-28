from PyQt5.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import QRegExp

class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            'def', 'class', 'if', 'else', 'elif', 'while', 'for', 'in', 'try',
            'except', 'with', 'as', 'import', 'from', 'return', 'pass', 'break',
            'continue', 'True', 'False', 'None', 'and', 'or', 'not', 'is', 'lambda'
        ]

        self.rules = [(QRegExp(r'\b' + kw + r'\b'), keyword_format) for kw in keywords]

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))
        self.rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        self.rules.append((QRegExp(r'#.*'), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

class CHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)

        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Bold)

        keywords = [
            'int', 'float', 'double', 'char', 'bool', 'void', 'if', 'else',
            'while', 'for', 'return', 'switch', 'case', 'break', 'continue',
            'default', 'do', 'struct', 'class', 'public', 'private', 'protected',
            'true', 'false', 'include', 'define', 'namespace', 'using', 'new', 'delete'
        ]

        self.rules = [(QRegExp(r'\b' + kw + r'\b'), keyword_format) for kw in keywords]

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))
        self.rules.append((QRegExp(r'"[^"\\]*(\\.[^"\\]*)*"'), string_format))
        self.rules.append((QRegExp(r"'[^'\\]*(\\.[^'\\]*)*'"), string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        self.rules.append((QRegExp(r'//.*'), comment_format))
        self.rules.append((QRegExp(r'/\*.*\*/'), comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            index = pattern.indexIn(text)
            while index >= 0:
                length = pattern.matchedLength()
                self.setFormat(index, length, fmt)
                index = pattern.indexIn(text, index + length)

class DummyHighlighter(QSyntaxHighlighter):
    def __init__(self, document):
        super().__init__(document)
    def highlightBlock(self, text):
        pass  
