# views/manage_projects.py
from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QComboBox, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QTableWidget,
                               QTableWidgetItem, QTabWidget, QVBoxLayout,
                               QWidget)

from database import SessionLocal
from logic import delete_project, get_projects, update_project_field
from views.add_project import AddProjectWidget

STATUS_VALUES = ["-", "Ootel", "Töös", "Valmis"]
FIELDS = [
    "delivery",
    "customer",
    "order_number",
    "product",
    "notes",
    "quantity",
    "afterone",
    "cutting",
    "laser",
    "bending",
    "drilling",
    "welding",
    "grinding",
    "coating",
    "delivered",
]
DEL_COL = len(FIELDS) + 1
IND_COL = len(FIELDS) + 2
COLOR_MAP = {
    "Valmis": "#8BC34A",
    "Töös": "#FFEB3B",
    "Ootel": "#F44336",
    "-": "#F44336",
}


class ManageProjectsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._building = False
        self._ui()

    # ---------- UI ----------
    def _ui(self):
        root = QVBoxLayout(self)

        self.tabs = QTabWidget()
        # 25 % suuremad sakid
        self.tabs.setStyleSheet(
            "QTabBar::tab { font-size:15px; min-height:40px; padding:6px 24px; }"
        )
        root.addWidget(self.tabs)

        # ---- PLAAN ---------------------------------------------------------
        plan_tab = QWidget()
        self.tabs.addTab(plan_tab, "Plaan")
        lay = QVBoxLayout(plan_tab)

        filters = QHBoxLayout()
        lay.addLayout(filters)
        filters.addWidget(QLabel("Otsi:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.refresh)
        filters.addWidget(self.search_edit)

        filters.addWidget(QLabel("Staatus:"))
        self.status_filter = QComboBox()
        self.status_filter.addItems(["Kõik"] + STATUS_VALUES)
        self.status_filter.currentTextChanged.connect(self.refresh)
        filters.addStretch()

        self.table = QTableWidget()
        self.table.setColumnCount(len(FIELDS) + 3)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Tarne",
                "Tellija",
                "Tellimuse nr",
                "Toode",
                "Märkus",
                "Kogus",
                "Afterone",
                "Lõikus",
                "Laser",
                "Painutus",
                "Puurimine",
                "Keevitus",
                "Lihvimine",
                "Pinnatöötlus",
                "Tarnitud",
                "Del",
                "Ind",
            ]
        )
        self.table.itemChanged.connect(self._on_item_changed)
        lay.addWidget(self.table)

        # ---- LISA TELLIMUS -------------------------------------------------
        add_tab = AddProjectWidget()
        self.tabs.addTab(add_tab, "Lisa tellimus")
        self.tabs.currentChanged.connect(
            lambda idx: self.refresh() if idx == 0 else None
        )

        self.refresh()

    # ---------- data -------------------------------------------------------
    def refresh(self):
        if self.tabs.currentIndex() != 0:
            return
        self._building = True
        with SessionLocal() as db:
            projects = get_projects(db)

        term = self.search_edit.text().lower().strip()
        need = self.status_filter.currentText()

        def show(p):
            if (
                term
                and term not in (p.customer or "").lower()
                and term not in (p.product or "").lower()
            ):
                return False
            if need != "Kõik":
                if need not in (
                    p.afterone,
                    p.cutting,
                    p.laser,
                    p.bending,
                    p.drilling,
                    p.welding,
                    p.grinding,
                    p.coating,
                    p.delivered,
                ):
                    return False
            return True

        rows = [p for p in projects if show(p)]
        self.table.setRowCount(len(rows))

        for r, p in enumerate(rows):
            self._set(r, 0, p.id, lock=True)
            plain = [
                p.delivery,
                p.customer,
                p.order_number,
                p.product,
                p.notes,
                p.quantity,
            ]
            for i, v in enumerate(plain, 1):
                self._set(r, i, v)

            stats = [
                p.afterone,
                p.cutting,
                p.laser,
                p.bending,
                p.drilling,
                p.welding,
                p.grinding,
                p.coating,
                p.delivered,
            ]
            for i, v in enumerate(stats, 7):
                self._status(r, i, v)

            d = QPushButton("X")
            d.setFixedSize(28, 28)  # väiksem del-nupp
            d.clicked.connect(lambda _, pid=p.id: self._delete(pid))
            self.table.setCellWidget(r, DEL_COL, d)

            self._indicator(r, p.delivered)

        self.table.resizeColumnsToContents()
        self._building = False

    # ---------- helpers ----------------------------------------------------
    def _set(self, row, col, val, *, lock=False):
        it = QTableWidgetItem("" if val is None else str(val))
        if lock:
            it.setFlags(it.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(row, col, it)

    def _status(self, row, col, val):
        cmb = QComboBox()
        cmb.addItems(STATUS_VALUES)
        if val in STATUS_VALUES:
            cmb.setCurrentText(val)
        cmb.currentTextChanged.connect(
            lambda v, r=row, c=col: self._commit_status(r, c, v)
        )
        cmb.setMinimumHeight(28)
        self.table.setCellWidget(row, col, cmb)

    def _indicator(self, row, delivered):
        it = QTableWidgetItem("")
        it.setFlags(it.flags() & ~Qt.ItemIsEditable)
        it.setBackground(QtGui.QColor(COLOR_MAP.get(delivered, "#F44336")))
        self.table.setItem(row, IND_COL, it)

    # ---------- events -----------------------------------------------------
    def _on_item_changed(self, it):
        if self._building or it.column() in (0, DEL_COL, IND_COL):
            return
        field = FIELDS[it.column() - 1]
        pid = int(self.table.item(it.row(), 0).text())
        with SessionLocal() as db:
            update_project_field(db, pid, field, it.text())

    def _commit_status(self, row, col, val):
        field = FIELDS[col - 1]
        pid = int(self.table.item(row, 0).text())
        with SessionLocal() as db:
            update_project_field(db, pid, field, val)
        if field == "delivered":
            self._indicator(row, val)

    def _delete(self, pid):
        if (
            QMessageBox.question(
                self, "Kinnitus", "Kustuta projekt?", QMessageBox.Yes | QMessageBox.No
            )
            != QMessageBox.Yes
        ):
            return
        with SessionLocal() as db:
            delete_project(db, pid)
        self.refresh()
