from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import QWidget


class SegmentedProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.maximum = 25
        self.value = 0

        self.active_color = QColor("#45B7D1")
        self.inactive_color = QColor("#444444")
        self.border_color = QColor("#ffffff")
        self.border_width = 2

        self.setMinimumHeight(50)

    def setRange(self, minimum, maximum):
        self.maximum = maximum
        self.value = min(self.value, maximum)
        self.update()

    def setValue(self, value):
        self.value = max(0, min(value, self.maximum))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if self.maximum <= 0:
            return

        gap = 4
        segment_width = (self.width() - gap * (self.maximum - 1)) / self.maximum

        for i in range(self.maximum):
            x = round(i * (segment_width + gap))
            width = round(segment_width)

            color = self.active_color if i < self.value else self.inactive_color

            pen = painter.pen()
            pen.setColor(self.border_color)
            pen.setWidth(self.border_width)
            painter.setPen(pen)
            painter.setBrush(color)
            inset = self.border_width / 2
            painter.drawRoundedRect(
                x + inset,
                inset,
                width - self.border_width,
                self.height() - self.border_width,
                5,
                5,
            )
