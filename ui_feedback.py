# ui_feedback.py
from PySide6.QtWidgets import QApplication, QMessageBox

def _main_window():
    win = QApplication.instance().activeWindow()
    return win if win and hasattr(win, "show_status_message") else None

def show_status(message: str, timeout: int = 3000) -> None:
    """Transient message in status bar."""
    win = _main_window()
    if win:
        win.show_status_message(message, timeout)

def show_error(title: str, message: str) -> None:
    """Modal critical error dialog."""
    QMessageBox.critical(_main_window() or None, title, message)
