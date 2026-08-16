import math

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import QWidget


class SundayWindow(QWidget):

    def __init__(self):
        super().__init__()

        self.setFixedSize(120, 120)

        self.setWindowTitle("SUNDAY")

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.status = "SLEEPING"
        self.message = ""

        self.phase = 0.0
        self.bob = 0.0

        self.drag_position = None

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.animate)
        self.timer.start(30)

    # ---------------------------------------------------------
    # STATE
    # ---------------------------------------------------------

    def set_status(
        self,
        status: str,
        message: str = "",
    ):
        self.status = status.upper()
        self.message = message
        self.update()

    # ---------------------------------------------------------
    # ANIMATION
    # ---------------------------------------------------------

    def animate(self):
        self.phase += 0.10

        if self.status == "LISTENING":
            self.bob += 0.15

        elif self.status == "THINKING":
            self.bob += 0.08

        elif self.status == "SPEAKING":
            self.bob += 0.20

        else:
            self.bob += 0.04

        self.update()

    # ---------------------------------------------------------
    # DRAG
    # ---------------------------------------------------------

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

    def mouseMoveEvent(self, event):
        if (
            self.drag_position is not None
            and event.buttons()
            & Qt.MouseButton.LeftButton
        ):
            self.move(
                event.globalPosition().toPoint()
                - self.drag_position
            )

    def mouseReleaseEvent(self, event):
        self.drag_position = None

    # ---------------------------------------------------------
    # PAINT
    # ---------------------------------------------------------

    def paintEvent(self, event):
        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing
        )

        center_x = self.width() / 2
        center_y = self.height() / 2

        center_y += math.sin(self.bob) * 3

        # -----------------------------------------------------
        # COLORS
        # -----------------------------------------------------

        if self.status == "SLEEPING":
            glow = QColor(120, 90, 220, 70)
            jelly = QColor(95, 65, 170)

        elif self.status == "LISTENING":
            glow = QColor(120, 170, 255, 110)
            jelly = QColor(90, 120, 240)

        elif self.status == "THINKING":
            glow = QColor(180, 100, 255, 120)
            jelly = QColor(150, 80, 230)

        elif self.status == "SPEAKING":
            glow = QColor(80, 220, 190, 120)
            jelly = QColor(55, 190, 160)

        elif self.status == "CONFIRMING":
            glow = QColor(255, 190, 80, 120)
            jelly = QColor(220, 150, 60)

        elif self.status == "WAKING":
            glow = QColor(210, 120, 255, 120)
            jelly = QColor(170, 90, 230)

        else:
            glow = QColor(255, 90, 100, 100)
            jelly = QColor(190, 60, 80)

        # -----------------------------------------------------
        # GLOW
        # -----------------------------------------------------

        painter.setPen(Qt.PenStyle.NoPen)

        for radius, alpha in (
            (48, 15),
            (42, 22),
            (37, 30),
        ):
            painter.setBrush(
                QColor(
                    glow.red(),
                    glow.green(),
                    glow.blue(),
                    alpha,
                )
            )

            painter.drawEllipse(
                int(center_x - radius),
                int(center_y - radius),
                int(radius * 2),
                int(radius * 2),
            )

        # -----------------------------------------------------
        # JELLY SHAPE
        # -----------------------------------------------------

        base_radius = 28

        if self.status == "LISTENING":
            pulse = math.sin(
                self.phase * 1.5
            ) * 2.5

        elif self.status == "SPEAKING":
            pulse = math.sin(
                self.phase * 2.2
            ) * 4.0

        elif self.status == "THINKING":
            pulse = math.sin(
                self.phase
            ) * 2.0

        elif self.status == "WAKING":
            pulse = math.sin(
                self.phase * 2.5
            ) * 3.0

        else:
            pulse = 0.0

        radius = base_radius + pulse

        path = QPainterPath()

        points = 48

        for i in range(points):

            angle = (
                i
                / points
                * math.pi
                * 2
            )

            wobble = math.sin(
                angle * 3
                + self.phase
            ) * 1.8

            current_radius = (
                radius + wobble
            )

            x = (
                center_x
                + math.cos(angle)
                * current_radius
            )

            y = (
                center_y
                + math.sin(angle)
                * current_radius
            )

            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)

        path.closeSubpath()

        painter.setBrush(jelly)
        painter.setPen(Qt.PenStyle.NoPen)

        painter.drawPath(path)