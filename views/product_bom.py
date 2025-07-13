from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from logic import (
    add_material_to_product,
    get_materials,
    get_product_parts,
    remove_material_from_product,
)


class ProductBOMDialog(QDialog):
    def __init__(
        self, product_id: int, product_name: str, parent: QWidget | None = None
    ):
        super().__init__(parent)
        self.product_id = product_id
        self.setWindowTitle(f"BOM – {product_name}")
        self.setMinimumWidth(600)
        self._ui()
        self._refresh_lists()

    # ───────── UI ─────────
    def _ui(self):
        root = QVBoxLayout(self)

        lists = QHBoxLayout()
        root.addLayout(lists)

        # materials
        left_box = QVBoxLayout()
        lists.addLayout(left_box)

        left_box.addWidget(QLabel("Lao materjalid"))
        self.materials_list = QListWidget()
        left_box.addWidget(self.materials_list)

        qty_row = QHBoxLayout()
        left_box.addLayout(qty_row)
        qty_row.addWidget(QLabel("Kogus:"))
        self.qty_spin = QSpinBox()
        self.qty_spin.setRange(1, 9999)
        qty_row.addWidget(self.qty_spin)

        add_btn = QPushButton("Lisa →")
        add_btn.clicked.connect(self._add_material)
        left_box.addWidget(add_btn)

        # bom parts
        right_box = QVBoxLayout()
        lists.addLayout(right_box)

        right_box.addWidget(QLabel("Toote BOM"))
        self.bom_list = QListWidget()
        right_box.addWidget(self.bom_list)

        del_btn = QPushButton("← Kustuta")
        del_btn.clicked.connect(self._remove_part)
        right_box.addWidget(del_btn)

        close = QPushButton("Sulge")
        close.clicked.connect(self.accept)
        root.addWidget(close)

    # ───────── Data ─────────
    def _refresh_lists(self):
        with SessionLocal() as db:
            # materials
            self.materials_list.clear()
            for m in get_materials(db):
                itm = QListWidgetItem(f"{m.name} (laos {m.stock_qty})")
                itm.setData(0x0100, m.id)  # Qt.UserRole
                self.materials_list.addItem(itm)

            # bom
            self.bom_list.clear()
            for pp in get_product_parts(db, self.product_id):
                itm = QListWidgetItem(f"{pp.material.name}  x {pp.quantity_required}")
                itm.setData(0x0100, pp.id)
                self.bom_list.addItem(itm)

    # ───────── Operations ─────────
    def _add_material(self):
        sel = self.materials_list.currentItem()
        if not sel:
            return
        material_id = sel.data(0x0100)
        qty = self.qty_spin.value()
        with SessionLocal() as db:
            add_material_to_product(db, self.product_id, material_id, qty)
        self._refresh_lists()

    def _remove_part(self):
        sel = self.bom_list.currentItem()
        if not sel:
            return
        pp_id = sel.data(0x0100)
        with SessionLocal() as db:
            remove_material_from_product(db, pp_id)
        self._refresh_lists()
