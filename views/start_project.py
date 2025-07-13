from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from logic import (
    add_history_entry,
    get_project_parts,
    get_projects,
    start_project_deduct_inventory,
)


class StartProjectWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Seadistab kasutajaliidese projekti käivitamiseks ja laoseisu haldamiseks."""
        layout = QVBoxLayout(self)

        # Pealkiri
        title = QLabel("Käivita Projekt")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Projekti valiku sektsioon
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Vali Projekt:"))
        self.project_combo = QComboBox()
        self.project_combo.currentTextChanged.connect(self.on_project_selected)
        selection_layout.addWidget(self.project_combo)

        self.load_project_btn = QPushButton("Lae Projekti Detailid")
        self.load_project_btn.clicked.connect(self.load_project_details)
        selection_layout.addWidget(self.load_project_btn)
        layout.addLayout(selection_layout)

        # Projekti koguse kordaja
        quantity_layout = QHBoxLayout()
        quantity_layout.addWidget(QLabel("Projekti Kogus:"))
        self.project_quantity_spin = QSpinBox()
        self.project_quantity_spin.setMinimum(1)
        self.project_quantity_spin.setMaximum(9999)
        self.project_quantity_spin.setValue(1)
        quantity_layout.addWidget(self.project_quantity_spin)
        layout.addLayout(quantity_layout)

        # Tabel projekti osadega
        details_label = QLabel("Projekti Vajalikud Osad")
        details_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; margin-top: 20px;"
        )
        layout.addWidget(details_label)

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels(
            ["Materjali ID", "Materjali Nimi", "Vajalik Kogus", "Laos Kogus", "Staatus"]
        )
        layout.addWidget(self.parts_table)
        self.parts_table.resizeColumnsToContents()

        # Käivita projekt nupp
        self.start_btn = QPushButton("Käivita Projekt (Vähenda Laoseisu)")
        self.start_btn.clicked.connect(self.start_project)
        self.start_btn.setEnabled(False)
        layout.addWidget(self.start_btn)

        self.current_project_id = None
        self.refresh()

    def refresh(self):
        """Laeb projektide loetelu andmebaasist ja valib automaatselt esimese (kui olemas)."""
        with SessionLocal() as db:
            projects = get_projects(db)
            self.project_combo.clear()
            for project in projects:
                self.project_combo.addItem(
                    f"{project.name} - {project.description}", project.id
                )
        if self.project_combo.count() > 0:
            self.load_project_details()

    def on_project_selected(self):
        """Tühjendab tabeli ja keelab nupu, kui projekt muutub."""
        self.start_btn.setEnabled(False)
        self.parts_table.setRowCount(0)

    def load_project_details(self):
        """Laeb valitud projekti osade detailid ja kontrollib laoseisu."""
        if self.project_combo.currentData() is None:
            QMessageBox.warning(self, "Hoiatus", "Palun vali projekt.")
            return

        self.current_project_id = self.project_combo.currentData()
        multiplier = self.project_quantity_spin.value()

        with SessionLocal() as db:
            project_parts = get_project_parts(db, self.current_project_id)
            self.parts_table.setRowCount(len(project_parts))
            all_available = True

            for i, part in enumerate(project_parts):
                material = part.material
                required_qty = part.quantity_required * multiplier

                # Lahtrite sisu ja lukustamine (mitte muudetavad)
                def create_item(value):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    return item

                self.parts_table.setItem(i, 0, create_item(material.id))
                self.parts_table.setItem(i, 1, create_item(material.name))
                self.parts_table.setItem(i, 2, create_item(required_qty))
                self.parts_table.setItem(i, 3, create_item(material.stock_qty))

                # Laos kontroll ja värvimine
                if material.stock_qty >= required_qty:
                    status_item = QTableWidgetItem("Piisav")
                    status_item.setBackground(Qt.green)
                else:
                    status_item = QTableWidgetItem(
                        f"Puudus ({required_qty - material.stock_qty} puudu)"
                    )
                    status_item.setBackground(Qt.red)
                    all_available = False

                status_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                self.parts_table.setItem(i, 4, status_item)

            self.parts_table.resizeColumnsToContents()
            self.start_btn.setEnabled(all_available)

            if not all_available:
                QMessageBox.warning(
                    self,
                    "Hoiatus",
                    "Mõnel materjalil on puudus. Vaata staatusetabelit.",
                )

    def start_project(self):
        """Käivita projekt ja vähenda laoseisu vastavalt kordajale."""
        if self.current_project_id is None:
            QMessageBox.warning(
                self, "Hoiatus", "Palun vali ja lae projekt enne käivitamist."
            )
            return

        multiplier = self.project_quantity_spin.value()
        reply = QMessageBox.question(
            self,
            "Kinnitus",
            f"Kas oled kindel, et soovid käivitada selle projekti {multiplier} kord(a)? Laos olev kogus väheneb.",
            QMessageBox.Yes | QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            with SessionLocal() as db:
                try:
                    for _ in range(multiplier):
                        start_project_deduct_inventory(db, self.current_project_id)

                    project_name = self.project_combo.currentText().split(" - ")[0]
                    add_history_entry(
                        db,
                        "Projekt Käivitatud",
                        f"Käivitas projekti: {project_name} x{multiplier}",
                    )

                    QMessageBox.information(
                        self,
                        "Edukas",
                        f"Projekt '{project_name}' käivitatud {multiplier} kord(a). Laos olev kogus uuendatud.",
                    )
                    self.load_project_details()
                except ValueError as e:
                    QMessageBox.critical(self, "Viga", str(e))
                except Exception as e:
                    QMessageBox.critical(
                        self, "Viga", f"Projekti käivitamine ebaõnnestus: {str(e)}"
                    )
