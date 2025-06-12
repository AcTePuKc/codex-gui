from __future__ import annotations

from PySide6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor, QRegularExpression


class PythonHighlighter(QSyntaxHighlighter):
    """Basic syntax highlighter for Python code."""

    def __init__(self, document) -> None:
        super().__init__(document)
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("blue"))
        keywords = [
            "and",
            "as",
            "assert",
            "break",
            "class",
            "continue",
            "def",
            "del",
            "elif",
            "else",
            "except",
            "False",
            "finally",
            "for",
            "from",
            "global",
            "if",
            "import",
            "in",
            "is",
            "lambda",
            "None",
            "nonlocal",
            "not",
            "or",
            "pass",
            "raise",
            "return",
            "True",
            "try",
            "while",
            "with",
            "yield",
        ]
        self.rules = [
            (QRegularExpression(fr"\b{kw}\b"), keyword_format) for kw in keywords
        ]

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("darkGreen"))
        self.rules.append((QRegularExpression(r"#[^\n]*"), comment_format))

    def highlightBlock(self, text: str) -> None:  # type: ignore[override]
        for pattern, fmt in self.rules:
            it = pattern.globalMatch(text)
            while it.hasNext():
                match = it.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), fmt)
