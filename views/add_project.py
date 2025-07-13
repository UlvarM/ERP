from PySide6.QtCore import QEvent
from PySide6.QtWidgets import (QApplication, QComboBox, QHBoxLayout, QLabel,
                               QLineEdit, QMessageBox, QPushButton, QSpinBox,
                               QTabWidget, QTextEdit, QVBoxLayout, QWidget)

from database import SessionLocal
from logic import (add_history_entry, create_project, get_product_parts,
                   get_products)
from models import Product


class AddProjectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._ui()

    # ───────── UI ─────────
    def _ui(self):
        root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs)

        tab_main = QWidget()
        self.tabs.addTab(tab_main, "Lisa Projekt")
        lay = QVBoxLayout(tab_main)

        title = QLabel("Lisa Uus Projekt")
        title.setStyleSheet("font-size:24px;font-weight:bold;margin:10px;")
        lay.addWidget(title)

        self.delivery = self._line(lay, "Tarne:")
        self.customer = self._line(lay, "Tellija:")
        # värskenda alles pärast sisestuse lõpetamist,
        # mitte iga klahvivajutuse järel
        self.customer.editingFinished.connect(self._refresh_products)

        self.order_nr = self._line(lay, "Tellimuse nr:")

        row = QHBoxLayout()
        lay.addLayout(row)
        row.addWidget(QLabel("Toode:"))
        self.product_combo = QComboBox()
        row.addWidget(self.product_combo)

        self.notes = self._line(lay, "Märkused:")
        self.quantity = self._spin(lay, "Kogus:", 1, 9999)
        self.pname = self._line(lay, "Projekti nimi:")
        self.desc = self._text(lay, "Kirjeldus:")

        save = QPushButton("Salvesta")
        save.clicked.connect(self._save)
        lay.addWidget(save)

        self._refresh_products()

    def showEvent(self, event: QEvent):
        super().showEvent(event)
        self._refresh_products()

    # ───────── Layout helpers ─────────
    def _line(self, parent, lbl):
        row = QHBoxLayout()
        parent.addLayout(row)
        row.addWidget(QLabel(lbl))
        edit = QLineEdit()
        row.addWidget(edit)
        return edit

    def _spin(self, parent, lbl, mn, mx):
        row = QHBoxLayout()
        parent.addLayout(row)
        row.addWidget(QLabel(lbl))
        sp = QSpinBox()
        sp.setRange(mn, mx)
        row.addWidget(sp)
        return sp

    def _text(self, parent, lbl):
        row = QHBoxLayout()
        parent.addLayout(row)
        row.addWidget(QLabel(lbl))
        te = QTextEdit()
        te.setMaximumHeight(80)
        row.addWidget(te)
        return te

    # ───────── Data helpers ─────────
    def _refresh_products(self):
        cust = self.customer.text().strip()
        with SessionLocal() as db:
            products = (
                get_products(db, category_names=[cust]) if cust else get_products(db)
            )
            # kui filtriga ei leitud midagi, näita kõiki,
            # et valik ei muutuks kasutamise käigus tühjaks
            if cust and not products:
                products = get_products(db)

        current_name = self.product_combo.currentText()
        self.product_combo.blockSignals(True)
        self.product_combo.clear()
        for p in products:
            self.product_combo.addItem(p.name, p.id)
        # proovi säilitada kasutaja eelnev valik
        idx = self.product_combo.findText(current_name)
        if idx != -1:
            self.product_combo.setCurrentIndex(idx)
        self.product_combo.blockSignals(False)

    # ───────── Save ─────────
    def _save(self):
        if not self.pname.text().strip():
            QMessageBox.warning(self, "Hoiatus", "Nimi puudub.")
            return

        selected_product_name = self.product_combo.currentText().strip()
        parts_to_use = []

        with SessionLocal() as db:
            if selected_product_name:
                prod: Product | None = (
                    db.query(Product).filter_by(name=selected_product_name).first()
                )
                if prod:
                    prod_parts = get_product_parts(db, prod.id)
                    parts_to_use = [
                        {
                            "material_id": pp.material_id,
                            "quantity_required": pp.quantity_required
                            * self.quantity.value(),
                        }
                        for pp in prod_parts
                    ]

            create_project(
                db,
                name=self.pname.text().strip(),
                description=self.desc.toPlainText().strip(),
                parts=parts_to_use,
                delivery=self.delivery.text().strip(),
                customer=self.customer.text().strip(),
                order_number=self.order_nr.text().strip(),
                product=selected_product_name,
                notes=self.notes.text().strip(),
                quantity=self.quantity.value(),
            )
            add_history_entry(db, "Projekt loodud", self.pname.text().strip())

        main_win = QApplication.instance().activeWindow()
        if hasattr(main_win, "views") and "production_plan" in main_win.views:
            main_win.views["production_plan"].refresh()

        self._reset()

    # ───────── Reset ─────────
    def _reset(self):
        for w in [
            self.delivery,
            self.customer,
            self.order_nr,
            self.notes,
            self.pname,
        ]:
            w.clear()
        self.quantity.setValue(1)
        self.desc.clear()
        self.product_combo.setCurrentIndex(0)
