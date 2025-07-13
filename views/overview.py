from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QEvent
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from database import SessionLocal
from logic import get_projects

STAGES = [
    "afterone", "cutting", "laser", "bending",
    "drilling", "welding", "grinding", "coating",
]
WAIT_SET = {"-", "Ootel"}
PROGRESS_VALUE = "Töös"
DONE_VALUE = "Valmis"


class OverviewWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._ui()

    # --------------------------------------------------------------------- UI
    def _ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Ülevaade")
        title.setStyleSheet("font-size:24px;font-weight:bold;margin:10px;")
        root.addWidget(title)

        # KPI-riba
        kpi_row = QHBoxLayout()
        root.addLayout(kpi_row)
        self.lbl_total     = self._kpi("Projektid kokku", kpi_row)
        self.lbl_delivered = self._kpi("Tarnitud",        kpi_row)
        self.lbl_progress  = self._kpi("Töös",            kpi_row)
        self.lbl_waiting   = self._kpi("Ootel",           kpi_row)

        # Staatusediagramm
        self.fig = Figure(figsize=(8, 4))
        self.canvas = FigureCanvas(self.fig)
        root.addWidget(self.canvas)

        self.refresh()

    def _kpi(self, caption: str, layout):
        box = QVBoxLayout()
        val = QLabel("0")
        val.setAlignment(Qt.AlignCenter)
        val.setStyleSheet("font-size:28px;font-weight:bold;")
        box.addWidget(val)
        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignCenter)
        box.addWidget(cap)
        w = QWidget()
        w.setLayout(box)
        layout.addWidget(w)
        return val

    # ----------------------------------------------------------------- events
    def showEvent(self, event: QEvent):
        super().showEvent(event)
        self.refresh()

    # ---------------------------------------------------------------- refresh
    def refresh(self):
        with SessionLocal() as db:
            projs = get_projects(db)

        total = len(projs)
        delivered = sum(p.delivered == DONE_VALUE for p in projs)
        in_progress = 0
        waiting = 0

        for p in projs:
            if p.delivered == DONE_VALUE:
                continue  # delivered overrides other flags
            stage_values = [getattr(p, s) for s in STAGES]
            if any(v == PROGRESS_VALUE for v in stage_values):
                in_progress += 1
            elif all(v in WAIT_SET for v in stage_values):
                waiting += 1

        self.lbl_total.setText(str(total))
        self.lbl_delivered.setText(str(delivered))
        self.lbl_progress.setText(str(in_progress))
        self.lbl_waiting.setText(str(waiting))

        self._draw_chart(projs)

    # ----------------------------------------------------------- chart helper
    def _draw_chart(self, projs):
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        stage_done = []
        stage_progress = []
        stage_wait = []

        for s in STAGES:
            vals = []
            for p in projs:
                v = DONE_VALUE if p.delivered == DONE_VALUE else getattr(p, s)
                vals.append(v)
            stage_done.append(sum(v == DONE_VALUE for v in vals))
            stage_progress.append(sum(v == PROGRESS_VALUE for v in vals))
            stage_wait.append(sum(v in WAIT_SET for v in vals))

        x = range(len(STAGES))
        ax.bar(x, stage_wait, label="Ootel")
        ax.bar(x, stage_progress, bottom=stage_wait, label="Töös")
        ax.bar(
            x,
            stage_done,
            bottom=[w + pr for w, pr in zip(stage_wait, stage_progress)],
            label="Valmis",
        )

        ax.set_xticks(list(x))
        ax.set_xticklabels(
            ["After1", "Lõikus", "Laser", "Painutus", "Puurim.", "Keevitus", "Lihv.", "Pinnat."],
            rotation=30,
            ha="right",
        )
        ax.legend()
        self.fig.tight_layout()
        self.canvas.draw()
