import hashlib


from PySide6.QtWidgets import (
    QPushButton,
    QMessageBox,
    QLabel,
    QWidget,
)
from PySide6.QtUiTools import QUiLoader
from PySide6.QtMultimedia import QSoundEffect
from PySide6.QtCore import QUrl
from PySide6.QtGui import QKeySequence, QShortcut, QColor

from progress_widget import SegmentedProgressBar
from questions import load_questions

def category_color(category: str) -> QColor:
    digest = hashlib.sha256(category.encode()).digest()

    # Generate RGB values in the range 80–220.
    r, g, b = (80 + value * 140 // 255 for value in digest[:3])

    return QColor(r, g, b)

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

    def __init__(self, config_path="config.toml"):
        loader = QUiLoader()
        self.window = loader.load("ui/board.ui")

        self.config = load_questions(config_path)
        self.categories = self.config["categories"]

        self.max_questions = self.config.get(
            "max_questions",
            len(self.categories) * len(self.POINTS_VALUES),
        )
        self.questions_remaining = self.max_questions

        self.question_history = []
        self.undo_shortcut = QShortcut(
            QKeySequence.StandardKey.Undo,
            self.window,
        )
        self.undo_shortcut.activated.connect(
            self.undo_last_question
        )

        # Replace the placeholder with the custom progress bar.
        placeholder = self.window.findChild(
            QWidget, "progressBar"
        )

        self.progress_bar = SegmentedProgressBar(
            placeholder.parentWidget()
        )
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, self.max_questions)

        layout = placeholder.parentWidget().layout()
        layout.replaceWidget(placeholder, self.progress_bar)
        placeholder.deleteLater()

        self.update_progress()

        self.click_sound = QSoundEffect()
        self.click_sound.setSource(
            QUrl.fromLocalFile("kwahmah_02__click.wav")
        )
        self.click_sound.setVolume(0.5)

        self.double_points_active = False
        self.double_button = self.window.findChild(
            QPushButton, "doubleButton"
        )
        self.double_button.setStyleSheet(
            self.DOUBLE_POINTS_OFF_STYLE
        )
        self.double_button.clicked.connect(self.double_points)

        self.setup_board()

    def setup_board(self):
        for category_index in range(self.CATEGORY_COUNT):
            category_number = category_index + 1

            category_label = self.window.findChild(
                QLabel, f"cat_{category_number}"
            )

            if category_index >= len(self.categories):
                category_label.setText("MISSING")
                category_available = False
                color = QColor(70, 70, 70, 128)
            else:
                category_label.setText(
                    self.categories[category_index]
                )
                category_available = True
                color = category_color(self.categories[category_index])

            for points in self.POINTS_VALUES:
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
                    lambda checked=False, button=button:
                        self.question_clicked(button)
                )

    def question_clicked(self, button):
        if button in self.question_history:
            return

        self.click_sound.play()
        self.question_history.append(button)

        # Give the button a disabled appearance.
        button.setProperty("used", True)
        button.style().unpolish(button)
        button.style().polish(button)
        button.update()

        self.questions_remaining = max(
            0, self.questions_remaining - 1
        )
        self.update_progress()

    def double_points(self):
        self.double_points_active = not self.double_points_active

        multiplier = 1 + self.double_points_active

        for category_index in range(
            min(len(self.categories), self.CATEGORY_COUNT)
        ):
            category_number = category_index + 1

            for points in self.POINTS_VALUES:
                button = self.window.findChild(
                    QPushButton,
                    f"cat_{category_number}_{points}",
                )
                button.setText(str(points * multiplier))

        self.double_button.setText(
            "🔥"
            if self.double_points_active
            else "x2"
        )

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