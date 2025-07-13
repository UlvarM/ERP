# app.py

from database import init_db

init_db()

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QMainWindow,
                               QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget)

from database import init_db
from views.add_details import AddDetailsWidget  # ladu
from views.history import HistoryWidget  # ajalugu
from views.manage_projects import ManageProjectsWidget  # tootmisplaan
# vaated
from views.overview import OverviewWidget
from views.tooted import ProductsWidget  # tooted


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ulvari MRP")
        self.setWindowState(Qt.WindowMaximized)

        # ---------- põhilayout ----------
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)

        # NAV – 25 % laiem (u 275 px)
        nav_widget = QWidget()
        nav_widget.setFixedWidth(245)
        nav = QVBoxLayout(nav_widget)
        root.addWidget(nav_widget, 0)

        # CONTENT
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        # ---------- vaated ----------
        self.views = {
            "overview": OverviewWidget(),
            "production_plan": ManageProjectsWidget(),
            "products": ProductsWidget(),
            "warehouse": AddDetailsWidget(),
            "history": HistoryWidget(),
        }

        # ---------- nupud ----------
        buttons = [
            ("Ülevaade", "overview"),
            ("Tootmisplaan", "production_plan"),
            ("Tooted", "products"),
            ("Ladu", "warehouse"),
            ("Ajalugu", "history"),
        ]

        for label, key in buttons:
            btn = QPushButton(label)
            btn.setMinimumHeight(50)
            btn.setStyleSheet("font-size:16px;")
            btn.clicked.connect(lambda _, k=key: self.show_view(k))
            nav.addWidget(btn)

        nav.addStretch()

        # lisa vaated pinu
        for w in self.views.values():
            self.stack.addWidget(w)

        self.show_view("overview")

    # ---------- helper ----------
    def show_view(self, key: str):
        widget = self.views[key]
        self.stack.setCurrentWidget(widget)
        getattr(widget, "refresh", lambda: None)()


def main():
    init_db()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()  # kuva aken
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
