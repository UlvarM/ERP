from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from logic import (
    add_history_entry,
    create_material,
    delete_material,
    get_material_by_name,
    get_materials,
    update_material_details,
)


class AddDetailsWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    # ---------- UI ----------
    def init_ui(self):
        root = QVBoxLayout(self)
        root.addWidget(self._title("Material Management"))

        tabs = QTabWidget()
        tabs.addTab(self._build_add_tab(), "Add")
        tabs.addTab(self._build_manage_tab(), "Manage")
        root.addWidget(tabs)

        self.refresh()

    def _title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size:24px;font-weight:bold;margin:10px;")
        return lbl

    # ---------- helpers ----------
    def _row(self, parent_layout):
        container = QWidget()
        row = QHBoxLayout(container)
        row.setContentsMargins(0, 0, 0, 0)
        parent_layout.addWidget(container)
        return container, row

    def _labeled_line(self, layout, label):
        cont, row = self._row(layout)
        row.addWidget(QLabel(label))
        line = QLineEdit()
        row.addWidget(line)
        return cont, line

    def _labeled_spin(self, layout, label, maximum):
        cont, row = self._row(layout)
        row.addWidget(QLabel(label))
        spin = QSpinBox()
        spin.setMaximum(maximum)
        row.addWidget(spin)
        return cont, spin

    # ---------- ADD TAB ----------
    def _build_add_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        _, row = self._row(lay)
        row.addWidget(QLabel("Type:"))
        self.type_combo = QComboBox()
        self.type_combo.addItems(["General", "Tube"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        row.addWidget(self.type_combo)

        self.material_type_container, mt_row = self._row(lay)
        mt_row.addWidget(QLabel("Material:"))
        self.material_type_combo = QComboBox()
        self.material_type_combo.addItems(["Aluminium", "Steel", "Stainless"])
        mt_row.addWidget(self.material_type_combo)

        self.profile_container, pr_row = self._row(lay)
        pr_row.addWidget(QLabel("Profile:"))
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Nelikanttoru", "Ümartoru"])
        pr_row.addWidget(self.profile_combo)

        _, self.name_edit = self._labeled_line(lay, "Name:")
        _, self.stock_spin = self._labeled_spin(lay, "Stock qty:", 99999)

        self.tube_group = QWidget()
        g = QVBoxLayout(self.tube_group)
        _, self.tube_len_spin = self._labeled_spin(g, "Length (mm):", 10000)
        _, self.tube_qty_spin = self._labeled_spin(g, "Qty per item:", 10000)
        _, self.tube_dim_edit = self._labeled_line(g, "Dimension:")
        _, self.tube_thick_edit = self._labeled_line(g, "Wall thickness:")
        lay.addWidget(self.tube_group)

        add_btn = QPushButton("Add")
        add_btn.clicked.connect(self.add_material)
        lay.addWidget(add_btn)
        lay.addStretch()

        self._on_type_changed(self.type_combo.currentText())
        return w

    # ---------- MANAGE TAB ----------
    def _build_manage_tab(self):
        w = QWidget()
        lay = QVBoxLayout(w)

        _, row = self._row(lay)
        row.addWidget(QLabel("Search:"))
        self.search_edit = QLineEdit()
        self.search_edit.textChanged.connect(self.update_table)
        row.addWidget(self.search_edit)

        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels(
            [
                "ID",
                "Name",
                "Stock",
                "Mat.",
                "Profile",
                "Len",
                "Qty",
                "Dim",
                "Thick",
                "Del",
            ]
        )
        lay.addWidget(self.table)
        return w

    # ---------- logic ----------
    def _on_type_changed(self, text):
        tube = text == "Tube"
        self.tube_group.setVisible(tube)
        self.material_type_container.setVisible(tube)
        self.profile_container.setVisible(tube)

    def refresh(self):
        self.update_table()

    def add_material(self):
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Warn", "Name missing")
            return

        with SessionLocal() as db:
            if get_material_by_name(db, name):
                QMessageBox.warning(self, "Warn", "Duplicate")
                return

            tube = self.type_combo.currentText() == "Tube"
            create_material(
                db,
                name=name,
                stock_qty=self.stock_spin.value(),
                type="tube" if tube else "general",
                material_type=(
                    self.material_type_combo.currentText().lower() if tube else None
                ),
                tube_profile=self.profile_combo.currentText().lower() if tube else None,
                tube_length=self.tube_len_spin.value() if tube else None,
                tube_quantity=self.tube_qty_spin.value() if tube else None,
                tube_dimension=self.tube_dim_edit.text().strip() if tube else None,
                tube_thickness=self.tube_thick_edit.text().strip() if tube else None,
            )
            add_history_entry(db, "Add", name)
        self.refresh()

    def update_table(self):
        with SessionLocal() as db:
            data = get_materials(db)
            term = self.search_edit.text().lower().strip()
            if term:
                data = [m for m in data if term in m.name.lower()]

            self.table.setRowCount(len(data))
            for r, m in enumerate(data):
                self.table.setItem(r, 0, QTableWidgetItem(str(m.id)))
                self.table.setItem(r, 1, QTableWidgetItem(m.name))

                stock_spin = QSpinBox()
                stock_spin.setMaximum(99999)
                stock_spin.setValue(m.stock_qty)
                self.table.setCellWidget(r, 2, stock_spin)

                mat_combo = QComboBox()
                mat_combo.addItems(["aluminium", "steel", "stainless"])
                if m.material_type:
                    mat_combo.setCurrentText(m.material_type)
                self.table.setCellWidget(r, 3, mat_combo)

                prof_combo = QComboBox()
                prof_combo.addItems(["nelikanttoru", "ümartoru"])
                if m.tube_profile:
                    prof_combo.setCurrentText(m.tube_profile)
                self.table.setCellWidget(r, 4, prof_combo)

                len_spin = QSpinBox()
                len_spin.setMaximum(10000)
                len_spin.setValue(m.tube_length or 0)
                qty_spin = QSpinBox()
                qty_spin.setMaximum(10000)
                qty_spin.setValue(m.tube_quantity or 0)
                dim_edit = QLineEdit(m.tube_dimension or "")
                thick_edit = QLineEdit(m.tube_thickness or "")

                self.table.setCellWidget(r, 5, len_spin)
                self.table.setCellWidget(r, 6, qty_spin)
                self.table.setCellWidget(r, 7, dim_edit)
                self.table.setCellWidget(r, 8, thick_edit)

                del_btn = QPushButton("X")
                del_btn.clicked.connect(partial(self._delete, m.id))
                self.table.setCellWidget(r, 9, del_btn)

                save = lambda *_, mid=m.id, s=stock_spin, l=len_spin, q=qty_spin, d=dim_edit, t=thick_edit, ma=mat_combo, pr=prof_combo: self._save(
                    mid,
                    s.value(),
                    l.value(),
                    q.value(),
                    d.text(),
                    t.text(),
                    ma.currentText(),
                    pr.currentText(),
                )
                stock_spin.editingFinished.connect(save)
                len_spin.editingFinished.connect(save)
                qty_spin.editingFinished.connect(save)
                dim_edit.editingFinished.connect(save)
                thick_edit.editingFinished.connect(save)
                mat_combo.currentTextChanged.connect(save)
                prof_combo.currentTextChanged.connect(save)

    def _save(self, mid, stock, length, qty, dim, thick, mat, prof):
        with SessionLocal() as db:
            update_material_details(db, mid, stock, length, qty, dim, thick, prof, mat)
            add_history_entry(db, "Edit", f"id {mid}")

    def _delete(self, mid):
        with SessionLocal() as db:
            m = delete_material(db, mid)
            if m:
                add_history_entry(db, "Delete", m.name)
        self.refresh()
