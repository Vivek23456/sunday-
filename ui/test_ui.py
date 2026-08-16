import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import SundayWindow


app = QApplication(sys.argv)

window = SundayWindow()
window.show()

sys.exit(app.exec())

