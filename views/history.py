from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem
from database import SessionLocal
from logic import get_history
from PySide6.QtCore import Qt

class HistoryWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Seadistab kasutajaliidese ajaloo kuvamiseks."""
        layout = QVBoxLayout(self)

        # Pealkiri
        title = QLabel("Tegevuste Ajalugu")
        title.setStyleSheet("font-size: 24px; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        # Ajaloo tabel
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels(
            ["ID", "Aeg", "Projekti ID", "Tegevus", "Detailid"]
        )
        layout.addWidget(self.history_table)

        self.refresh()

    def refresh(self):
        """Laeb tegevuste ajaloo andmebaasist ja kuvab tabelis."""
        with SessionLocal() as db:
            history_entries = get_history(db)
            self.history_table.setRowCount(len(history_entries))

            for i, entry in enumerate(history_entries):
                def create_item(value):
                    item = QTableWidgetItem(str(value))
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
                    return item

                self.history_table.setItem(i, 0, create_item(entry.id))
                self.history_table.setItem(i, 1, create_item(entry.timestamp.strftime("%Y-%m-%d %H:%M:%S")))
                self.history_table.setItem(i, 2, create_item(entry.project_id if entry.project_id else "Puudub"))
                self.history_table.setItem(i, 3, create_item(entry.action))
                self.history_table.setItem(i, 4, create_item(entry.details))

            self.history_table.resizeColumnsToContents()
