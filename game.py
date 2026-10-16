import hashlib
from html import escape

from PySide6.QtCore import QUrl
from PySide6.QtGui import QColor, QKeySequence, QShortcut
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QDialog, QLabel, QPushButton, QVBoxLayout, QWidget

from progress_widget import SegmentedProgressBar
from questions import load_questions


def category_color(category: str) -> QColor:
    digest = hashlib.sha256(category.encode()).digest()

    # Generate RGB values in the range 80–220.
    r, g, b = (80 + value * 140 // 255 for value in digest[:3])

    return QColor(r, g, b)


class QuestionDialog(QDialog):
    def __init__(self, question, parent=None):
        super().__init__(parent)

        self.setWindowTitle("Question")
        self.setMinimumSize(720, 480)

        layout = QVBoxLayout(self)

        label = QLabel(question)
        label.setWordWrap(True)
        font = label.font()
        font.setPointSize(16)
        label.setFont(font)
        layout.addWidget(label)


class Game:
    POINTS_VALUES = (100, 200, 300, 400, 500)
    CATEGORY_COUNT = 5

    DOUBLE_POINTS_OFF_STYLE = """
        QPushButton {
            background-color: #454545;
            color: #dddddd;
            border: 2px solid #ffffff;
            border-radius: 5px;
            padding: 6px 12px;
            font-size: 24px;
        }
        QPushButton:hover {
            background-color: #555555;
        }
    """

    DOUBLE_POINTS_ON_STYLE = """
        QPushButton {
            background-color: #a855f7;
            color: white;
            border: 2px solid #d8b4fe;
            border-radius: 5px;
            padding: 6px 12px;
            font-size: 24px;
        }
        QPushButton:hover {
            background-color: #9333ea;
        }
    """

    def __init__(self, config_path="questions.toml"):
        loader = QUiLoader()
        self.window = loader.load("ui/board.ui")

        self.toml_import = load_questions(config_path)
        self.categories = self.toml_import["categories"]

        self.max_questions = self.toml_import.get(
            "max_questions",
            len(self.categories) * len(self.POINTS_VALUES),
        )
        self.questions_remaining = self.max_questions

        self.question_history = []
        self.undo_shortcut = QShortcut(
            QKeySequence.StandardKey.Undo,
            self.window,
        )
        self.undo_shortcut.activated.connect(self.undo_last_question)

        # Replace the placeholder with the custom progress bar.
        placeholder = self.window.findChild(QWidget, "progressBar")

        self.progress_bar = SegmentedProgressBar(placeholder.parentWidget())
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, self.max_questions)

        layout = placeholder.parentWidget().layout()
        layout.replaceWidget(placeholder, self.progress_bar)
        placeholder.deleteLater()

        self.update_progress()

        self.click_sound = QSoundEffect()
        self.click_sound.setSource(QUrl.fromLocalFile("ui/kwahmah_02__click.wav"))
        self.click_sound.setVolume(0.5)

        self.double_points_active = False
        self.double_button = self.window.findChild(QPushButton, "doubleButton")
        self.double_button.setStyleSheet(self.DOUBLE_POINTS_OFF_STYLE)
        self.double_button.clicked.connect(self.double_points)

        self.setup_board()

    def setup_board(self):
        for category_index in range(0, len(self.categories)):
            category_number = category_index + 1
            catgeory_name = self.categories[category_index].get("name", "MISSING")
            category_questions = self.categories[category_index].get("questions", {})

            category_label = self.window.findChild(QLabel, f"cat_{category_number}")

            if category_index >= len(self.categories):
                category_label.setText("MISSING")
                category_available = False
                color = QColor(70, 70, 70, 128)
            else:
                category_label.setText(catgeory_name)
                category_available = True
                color = category_color(catgeory_name)

            for i, points in enumerate(self.POINTS_VALUES):
                button = self.window.findChild(
                    QPushButton,
                    f"cat_{category_number}_{points}",
                )
                button.setStyleSheet(
                    f"""
                    QPushButton {{
                        background-color: {color.name(QColor.NameFormat.HexArgb)};
                    }}
                    QPushButton[used="true"] {{
                        background-color: {QColor(70, 70, 70, 128).name(QColor.NameFormat.HexArgb)};
                    }}
                    """
                )

                if not category_available:
                    button.setText("—")
                    button.setEnabled(False)
                    continue

                button.setText(str(points))
                button.setEnabled(True)

                button.clicked.connect(
                    lambda checked=False, button=button, question=category_questions[
                        i
                    ].get("question", "MISSING"), answer=category_questions[i].get(
                        "answer", "MISSING"
                    ): self.question_clicked(
                        button, question, answer
                    )
                )

    def question_clicked(self, button, question, answer):
        if button in self.question_history:
            return

        self.click_sound.play()
        self.question_history.append(button)

        # Give the button a disabled appearance.
        button.setProperty("used", True)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

        self.questions_remaining = max(0, self.questions_remaining - 1)
        self.update_progress()

        dialog = QuestionDialog(
            f"<b>{escape(question)}</b><br><br>▶ {escape(answer)}",
            self.window,
        )

        dialog.exec()

    def double_points(self):
        self.double_points_active = not self.double_points_active

        multiplier = 1 + self.double_points_active

        for category_index in range(min(len(self.categories), self.CATEGORY_COUNT)):
            category_number = category_index + 1

            for points in self.POINTS_VALUES:
                button = self.window.findChild(
                    QPushButton,
                    f"cat_{category_number}_{points}",
                )
                button.setText(str(points * multiplier))

        self.double_button.setText("🔥" if self.double_points_active else "x2")

        self.double_button.setStyleSheet(
            self.DOUBLE_POINTS_ON_STYLE
            if self.double_points_active
            else self.DOUBLE_POINTS_OFF_STYLE
        )

    def update_progress(self):
        self.progress_bar.setValue(self.questions_remaining)

    def undo_last_question(self):
        if not self.question_history:
            return

        button = self.question_history.pop()

        button.setProperty("used", False)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

        self.questions_remaining = min(
            self.max_questions,
            self.questions_remaining + 1,
        )
        self.update_progress()
