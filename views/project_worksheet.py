from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from database import SessionLocal
from logic import get_project_parts, get_projects


class ProjectWorksheetWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Seadistab kasutajaliidese projekti töölehe kuvamiseks ja printimiseks."""
        layout = QVBoxLayout(self)

        # Pealkiri
        title = QLabel("Projekti Tööleht")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Projekti valiku ala
        selection_layout = QHBoxLayout()
        selection_layout.addWidget(QLabel("Vali Projekt:"))
        self.project_combo = QComboBox()
        self.project_combo.currentTextChanged.connect(self.reset_view)
        selection_layout.addWidget(self.project_combo)

        load_btn = QPushButton("Lae Projekti Detailid")
        load_btn.clicked.connect(self.load_project_details)
        selection_layout.addWidget(load_btn)
        layout.addLayout(selection_layout)

        # Projekti number
        self.project_number_label = QLabel("Projekti Number: Puudub")
        self.project_number_label.setAlignment(Qt.AlignCenter)
        self.project_number_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.project_number_label)

        # Osade tabel
        layout.addWidget(QLabel("Vajalikud Osad", alignment=Qt.AlignLeft))

        self.parts_table = QTableWidget()
        self.parts_table.setColumnCount(5)
        self.parts_table.setHorizontalHeaderLabels(
            [
                "Materjali ID",
                "Materjali Nimi",
                "Vajalik Kogus",
                "Tüüp",
                "Materjali Tüüp",
            ]
        )
        layout.addWidget(self.parts_table)
        self.parts_table.resizeColumnsToContents()

        # Printimise nupp
        self.print_btn = QPushButton("Prindi Tööleht")
        self.print_btn.clicked.connect(self.print_worksheet)
        self.print_btn.setEnabled(False)
        layout.addWidget(self.print_btn)

        self.current_project_id = None
        self.refresh_projects()

    def refresh_projects(self):
        """Laeb projektid andmebaasist. Kui pole projekte, kuvab hoiatuse."""
        with SessionLocal() as db:
            projects = get_projects(db)
            self.project_combo.clear()
            if not projects:
                QMessageBox.information(self, "Teade", "Projekte ei leitud.")
                return
            for project in projects:
                self.project_combo.addItem(
                    f"{project.name} - {project.description}", project.id
                )

    def reset_view(self):
        """Tühjendab tabeli ja nupud, kui projekt muutub."""
        self.current_project_id = None
        self.parts_table.setRowCount(0)
        self.project_number_label.setText("Projekti Number: Puudub")
        self.print_btn.setEnabled(False)

    def load_project_details(self):
        """Laeb valitud projekti osade detailid ja kuvab need tabelis."""
        project_id = self.project_combo.currentData()
        if project_id is None:
            QMessageBox.warning(self, "Hoiatus", "Palun vali projekt.")
            return

        self.current_project_id = project_id
        self.project_number_label.setText(f"Projekti Number: {project_id}")

        with SessionLocal() as db:
            parts = get_project_parts(db, project_id)
            self.parts_table.setRowCount(len(parts))

            for i, part in enumerate(parts):
                m = part.material

                def create_item(value):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    return item

                self.parts_table.setItem(i, 0, create_item(m.id))
                self.parts_table.setItem(i, 1, create_item(m.name))
                self.parts_table.setItem(i, 2, create_item(part.quantity_required))
                self.parts_table.setItem(i, 3, create_item(m.type))
                self.parts_table.setItem(i, 4, create_item(m.material_type or "Puudub"))

            self.parts_table.resizeColumnsToContents()
            self.print_btn.setEnabled(True)

    def print_worksheet(self):
        """Prindib töölehe (salvestab tekstifailina)."""
        if self.current_project_id is None:
            QMessageBox.warning(self, "Hoiatus", "Palun lae projekt enne printimist.")
            return

        name, desc = self.project_combo.currentText().split(" - ")
        filename = (
            f"projekti_tööleht_{name.replace(' ', '_')}_{self.current_project_id}.txt"
        )

        header = (
            f"Projekti Number: {self.current_project_id}\n"
            f"Projekti Nimi: {name}\n"
            f"Kirjeldus: {desc}\n\n"
            f"Vajalikud Osad:\n"
            + "-" * 70
            + "\n"
            + f"{'Materjali ID':<15} {'Materjali Nimi':<25} {'Vajalik Kogus':<15} {'Tüüp':<10} {'Materjali Tüüp':<15}\n"
            + "-" * 70
            + "\n"
        )

        with SessionLocal() as db:
            parts = get_project_parts(db, self.current_project_id)
            lines = [
                f"{p.material.id:<15} {p.material.name:<25} {p.quantity_required:<15} {p.material.type:<10} {p.material.material_type or 'Puudub':<15}"
                for p in parts
            ]

        content = header + "\n".join(lines) + "\n" + "-" * 70 + "\n"

        try:
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)
            QMessageBox.information(self, "Edukas", f"Tööleht salvestatud: {filename}")
        except Exception as e:
            QMessageBox.critical(
                self, "Viga", f"Töölehe salvestamine ebaõnnestus: {str(e)}"
            )
