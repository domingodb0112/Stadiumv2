from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLayout, QSizePolicy
from PyQt5.QtCore import Qt
from config import BG

class BaseScreen(QWidget):
    """Base class para todas las pantallas."""

    def __init__(self, app, **kwargs):
        super().__init__()
        self.app = app
        self.setStyleSheet(f"QWidget {{ background-color: {BG}; }}")
        self.setMinimumSize(360, 640)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if self.layout():
            self.layout().setSizeConstraint(QLayout.SetDefaultConstraint)

    def resizeEvent(self, event):
        """Forward resize to children that implement their own resizeEvent."""
        super().resizeEvent(event)
        for child in self.findChildren(QWidget, options=Qt.FindDirectChildrenOnly):
            if type(child).resizeEvent is not QWidget.resizeEvent:
                child.resizeEvent(event)

    def on_destroy(self):
        pass

    def closeEvent(self, event):
        self.on_destroy()
        super().closeEvent(event)
