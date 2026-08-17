import math
import sys

from PySide6.QtCore import (
    QPoint,
    QPointF,
    QTimer,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QPainter,
    QPen,
    QRadialGradient,
)
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
)


class VoiceOrb(QWidget):

    def __init__(self):
        super().__init__()

        self.status = "SLEEPING"
        self.phase = 0.0

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.timer = QTimer(self)

        self.timer.timeout.connect(
            self._animate
        )

        # 30 FPS keeps the animation smooth
        # without continuously hammering the GPU/CPU.
        self.timer.start(33)

    def set_status(
        self,
        status: str,
    ):
        self.status = status.upper()
        self.update()

    def _animate(self):

        if self.status == "SLEEPING":
            speed = 0.015

        elif self.status == "LISTENING":
            speed = 0.045

        elif self.status == "THINKING":
            speed = 0.065

        elif self.status == "WORKING":
            speed = 0.09

        elif self.status == "SPEAKING":
            speed = 0.12

        elif self.status == "WAKING":
            speed = 0.10

        elif self.status == "CONFIRMING":
            speed = 0.07

        else:
            speed = 0.04

        self.phase += speed

        if self.phase > math.tau:
            self.phase -= math.tau

        self.update()

    def _color(self):

        colors = {
            "SLEEPING": QColor(
                95,
                105,
                145,
            ),

            "WAKING": QColor(
                255,
                190,
                80,
            ),

            "LISTENING": QColor(
                70,
                210,
                255,
            ),

            "THINKING": QColor(
                150,
                100,
                255,
            ),

            "WORKING": QColor(
                90,
                150,
                255,
            ),

            "SPEAKING": QColor(
                90,
                255,
                210,
            ),

            "CONFIRMING": QColor(
                255,
                190,
                80,
            ),

            "ERROR": QColor(
                255,
                90,
                110,
            ),

            "OFFLINE": QColor(
                90,
                90,
                105,
            ),
        }

        return colors.get(
            self.status,
            QColor(
                120,
                120,
                140,
            ),
        )

    def _radius(self):

        base = 48.0

        if self.status == "SLEEPING":

            pulse = (
                math.sin(
                    self.phase * 2.0
                )
                + 1.0
            ) * 0.5

            return base + pulse * 2.5

        if self.status == "LISTENING":

            pulse = (
                math.sin(
                    self.phase * 6.0
                )
                + 1.0
            ) * 0.5

            return base + pulse * 7.0

        if self.status == "SPEAKING":

            pulse = (
                math.sin(
                    self.phase * 8.0
                )
                + 1.0
            ) * 0.5

            return base + pulse * 10.0

        if self.status == "WAKING":

            pulse = abs(
                math.sin(
                    self.phase * 5.0
                )
            )

            return base + pulse * 10.0

        if self.status == "CONFIRMING":

            pulse = (
                math.sin(
                    self.phase * 4.0
                )
                + 1.0
            ) * 0.5

            return base + pulse * 5.0

        return base

    def paintEvent(self, event):

        painter = QPainter(self)

        painter.setRenderHint(
            QPainter.RenderHint.Antialiasing,
            True,
        )

        center = QPointF(
            self.width() / 2.0,
            self.height() / 2.0,
        )

        color = self._color()

        radius = self._radius()

        # =========================================================
        # OUTER GLOW
        # =========================================================

        glow = QRadialGradient(
            center,
            radius * 2.0,
        )

        glow.setColorAt(
            0.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                220,
            ),
        )

        glow.setColorAt(
            0.45,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                80,
            ),
        )

        glow.setColorAt(
            1.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                0,
            ),
        )

        painter.setPen(
            Qt.PenStyle.NoPen
        )

        painter.setBrush(
            glow
        )

        painter.drawEllipse(
            center,
            radius * 1.75,
            radius * 1.75,
        )

        # =========================================================
        # CORE
        # =========================================================

        core = QRadialGradient(
            center,
            radius,
        )

        core.setColorAt(
            0.0,
            QColor(
                245,
                255,
                255,
                245,
            ),
        )

        core.setColorAt(
            0.25,
            QColor(
                (
                    color.red()
                    + 255
                ) // 2,

                (
                    color.green()
                    + 255
                ) // 2,

                (
                    color.blue()
                    + 255
                ) // 2,

                245,
            ),
        )

        core.setColorAt(
            1.0,
            QColor(
                color.red(),
                color.green(),
                color.blue(),
                225,
            ),
        )

        painter.setBrush(
            core
        )

        painter.drawEllipse(
            center,
            radius,
            radius,
        )

        # =========================================================
        # ACTIVE RING
        # =========================================================

        if self.status in {
            "LISTENING",
            "THINKING",
            "WORKING",
            "SPEAKING",
            "WAKING",
            "CONFIRMING",
        }:

            pen = QPen(
                QColor(
                    color.red(),
                    color.green(),
                    color.blue(),
                    155,
                )
            )

            pen.setWidth(2)

            painter.setPen(
                pen
            )

            painter.setBrush(
                Qt.BrushStyle.NoBrush
            )

            if self.status in {
                "THINKING",
                "WORKING",
            }:

                painter.save()

                painter.translate(
                    center
                )

                painter.rotate(
                    self.phase * 35.0
                )

                size = (
                    radius * 2.0
                    + 30.0
                )

                painter.drawArc(
                    int(-size / 2),
                    int(-size / 2),
                    int(size),
                    int(size),
                    25 * 16,
                    100 * 16,
                )

                painter.drawArc(
                    int(-size / 2),
                    int(-size / 2),
                    int(size),
                    int(size),
                    210 * 16,
                    55 * 16,
                )

                painter.restore()

            else:

                pulse = (
                    math.sin(
                        self.phase * 3.0
                    )
                    + 1.0
                ) * 0.5

                ring_radius = (
                    radius
                    + 13
                    + pulse * 4
                )

                painter.drawEllipse(
                    center,
                    ring_radius,
                    ring_radius,
                )

        # =========================================================
        # SPEAKING PARTICLES
        # =========================================================

        if self.status == "SPEAKING":

            painter.setBrush(
                QColor(
                    255,
                    255,
                    255,
                    155,
                )
            )

            painter.setPen(
                Qt.PenStyle.NoPen
            )

            for index in range(3):

                angle = (
                    self.phase * 2.0
                    + index * 2.094
                )

                distance = (
                    radius
                    + 16
                )

                x = (
                    center.x()
                    + math.cos(angle)
                    * distance
                )

                y = (
                    center.y()
                    + math.sin(angle)
                    * distance
                )

                painter.drawEllipse(
                    QPointF(
                        x,
                        y,
                    ),
                    2.2,
                    2.2,
                )

        painter.end()


class SundayWindow(QWidget):

    def __init__(self):

        super().__init__()

        self.status_value = "SLEEPING"

        self._drag_position = QPoint()

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.Tool
            | Qt.WindowType.WindowStaysOnTopHint
        )

        self.setAttribute(
            Qt.WidgetAttribute.WA_TranslucentBackground
        )

        self.setFixedSize(
            190,
            190,
        )

        self.orb = VoiceOrb()

        self.orb.setParent(
            self
        )

        self.orb.setGeometry(
            5,
            5,
            180,
            180,
        )

    def set_status(
        self,
        status: str,
        message: str = "",
    ):

        self.status_value = (
            status.upper()
        )

        self.orb.set_status(
            self.status_value
        )

        # Intentionally ignore `message`.
        # No "TO WAKE", "SLEEPING", or other
        # text is displayed under the orb.

        self.show()
        self.raise_()

    def mousePressEvent(
        self,
        event,
    ):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            self._drag_position = (
                event.globalPosition().toPoint()
                - self.frameGeometry().topLeft()
            )

            event.accept()

    def mouseMoveEvent(
        self,
        event,
    ):

        if (
            event.buttons()
            & Qt.MouseButton.LeftButton
        ):

            self.move(
                event.globalPosition().toPoint()
                - self._drag_position
            )

            event.accept()

    def mouseReleaseEvent(
        self,
        event,
    ):

        if (
            event.button()
            == Qt.MouseButton.LeftButton
        ):

            event.accept()


if __name__ == "__main__":

    app = QApplication(
        sys.argv
    )

    window = SundayWindow()

    window.show()

    sys.exit(
        app.exec()
    )