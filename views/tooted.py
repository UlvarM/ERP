from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from logic import (
    assign_product_categories,
    create_product,
    delete_product,
    get_products,
)
from views.product_bom import ProductBOMDialog


class ProductsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._ui()
        self.refresh()

    # ───────── UI ─────────
    def _ui(self):
        root = QVBoxLayout(self)
        title = QLabel("Tooted")
        title.setStyleSheet("font-size:24px;font-weight:bold;margin:10px;")
        root.addWidget(title)

        form = QHBoxLayout()
        root.addLayout(form)

        form.addWidget(QLabel("Nimi:"))
        self.name_edit = QLineEdit()
        form.addWidget(self.name_edit)

        form.addWidget(QLabel("Kategooriad (,):"))
        self.cat_edit = QLineEdit()
        form.addWidget(self.cat_edit)

        form.addWidget(QLabel("Kirjeldus:"))
        self.desc_edit = QTextEdit()
        self.desc_edit.setFixedHeight(40)
        self.desc_edit.setTabChangesFocus(True)
        form.addWidget(self.desc_edit)

        form.addWidget(QLabel("Prod. aeg (min):"))
        self.ptime_spin = QSpinBox()
        self.ptime_spin.setRange(1, 100000)
        form.addWidget(self.ptime_spin)

        add_btn = QPushButton("Lisa")
        add_btn.clicked.connect(self._add_product)
        form.addWidget(add_btn)

        # tabel
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Nimi", "Kategooriad", "ProdTime", "Kirjeldus", "BOM", "Del"]
        )
        root.addWidget(self.table)

    # ───────── data ─────────
    def refresh(self):
        with SessionLocal() as db:
            products = get_products(db)
            self.table.setRowCount(len(products))
            for r, p in enumerate(products):
                self.table.setItem(r, 0, QTableWidgetItem(str(p.id)))
                self.table.setItem(r, 1, QTableWidgetItem(p.name))
                self.table.setItem(
                    r, 2, QTableWidgetItem(", ".join(c.name for c in p.categories))
                )
                self.table.setItem(
                    r,
                    3,
                    QTableWidgetItem(
                        "" if p.production_time is None else str(p.production_time)
                    ),
                )
                self.table.setItem(r, 4, QTableWidgetItem(p.description or ""))

                bom_btn = QPushButton("BOM")
                bom_btn.clicked.connect(
                    lambda _, pid=p.id, pn=p.name: self._open_bom(pid, pn)
                )
                self.table.setCellWidget(r, 5, bom_btn)

                del_btn = QPushButton("X")
                del_btn.clicked.connect(lambda _, pid=p.id: self._delete_product(pid))
                self.table.setCellWidget(r, 6, del_btn)

            self.table.resizeColumnsToContents()

    # ───────── ops ─────────
    def _add_product(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Hoiatus", "Nimi puudub")
            return

        cats = [c.strip() for c in self.cat_edit.text().split(",") if c.strip()]

        with SessionLocal() as db:
            p = create_product(
                db,
                name=name,
                description=self.desc_edit.toPlainText().strip(),
                production_time=self.ptime_spin.value(),
            )
            if cats:
                assign_product_categories(db, p, cats)

        # kohe ava lao-põhine BOM-lisaja
        dlg = ProductBOMDialog(p.id, p.name, self)
        dlg.exec()

        self.name_edit.clear()
        self.cat_edit.clear()
        self.desc_edit.clear()
        self.ptime_spin.setValue(1)
        self.refresh()

    def _delete_product(self, pid: int):
        with SessionLocal() as db:
            delete_product(db, pid)
        self.refresh()

    def _open_bom(self, pid: int, pname: str):
        dlg = ProductBOMDialog(pid, pname, self)
        dlg.exec()
        self.refresh()
