import os
from collections import deque

import psutil
from PySide6.QtCore import Qt, QTimer, QPointF
from PySide6.QtGui import QColor, QPainter, QPen, QPainterPath
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGraphicsDropShadowEffect,
)
from pathlib import Path


# ─────────────────────────────────────────
#  THEMES (kept identical in spirit to Home_GUI.py)
# ─────────────────────────────────────────
THEMES = {
    "dark": dict(
        BG_DEEP="#0D1B2A",
        BG_SURFACE="#1C2E42",
        ACCENT="#4A9EBF",
        ACCENT_DARK="#2E7A9A",
        TEXT_PRI="#F0F4F8",
        TEXT_SEC="#8FA8BF",
        BORDER="#2A4059",
        GRID="#2A4059",
    ),
    "light": dict(
        BG_DEEP="#EEF2F6",
        BG_SURFACE="#FFFFFF",
        ACCENT="#2E7A9A",
        ACCENT_DARK="#1F5C77",
        TEXT_PRI="#16232F",
        TEXT_SEC="#51697E",
        BORDER="#D7E0E8",
        GRID="#E3E9EF",
    ),
}


def _shadow(blur=24, alpha=90, y_offset=6):
    effect = QGraphicsDropShadowEffect()
    effect.setBlurRadius(blur)
    c = QColor("#000000")
    c.setAlpha(alpha)
    effect.setColor(c)
    effect.setOffset(0, y_offset)
    return effect


def _format_speed(bytes_per_sec: float) -> str:
    if bytes_per_sec >= 1024 * 1024:
        return f"{bytes_per_sec / (1024 * 1024):.2f} MB/s"
    return f"{bytes_per_sec / 1024:.1f} KB/s"


# ─────────────────────────────────────────
#  KPI STAT CARD
# ─────────────────────────────────────────
class StatCard(QWidget):

    def __init__(self, title: str, theme):
        super().__init__()
        self.setGraphicsEffect(_shadow())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(6)

        self._title_label = QLabel(title.upper())
        self.value_label = QLabel("—")

        layout.addWidget(self._title_label)
        layout.addWidget(self.value_label)

        self.apply_theme(theme)

    def apply_theme(self, theme):
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['BG_SURFACE']};
                border: 1px solid {theme['BORDER']};
                border-radius: 10px;
            }}
        """)
        self._title_label.setStyleSheet(f"""
            color: {theme['TEXT_SEC']}; font-size: 10px; font-weight: 600;
            letter-spacing: 1px; background: transparent; border: none;
        """)
        self.value_label.setStyleSheet(f"""
            color: {theme['TEXT_PRI']}; font-size: 24px; font-weight: 700;
            background: transparent; border: none;
        """)

    def set_value(self, text: str):
        self.value_label.setText(text)


# ─────────────────────────────────────────
#  LINE / AREA CHART (Task-Manager-style)
# ─────────────────────────────────────────
class LineChart(QWidget):

    def __init__(self, theme, max_points=60, max_value=100):
        super().__init__()
        self.max_points = max_points
        self.max_value = max_value
        self.data = deque([0] * max_points, maxlen=max_points)
        self.setMinimumHeight(220)
        self.apply_theme(theme)

    def apply_theme(self, theme):
        self.theme = theme
        self.update()

    def add_point(self, value):
        self.data.append(max(0, min(value, self.max_value)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # background
        painter.fillRect(self.rect(), QColor(self.theme["BG_SURFACE"]))

        # gridlines (horizontal, 4 divisions)
        grid_pen = QPen(QColor(self.theme["GRID"]))
        grid_pen.setWidth(1)
        painter.setPen(grid_pen)
        for i in range(1, 4):
            y = h * i / 4
            painter.drawLine(0, int(y), w, int(y))

        n = len(self.data)
        if n < 2:
            return

        step_x = w / (n - 1)
        points = []
        for i, v in enumerate(self.data):
            x = i * step_x
            y = h - (v / self.max_value) * h
            points.append(QPointF(x, y))

        # area fill under the line
        path = QPainterPath()
        path.moveTo(points[0].x(), h)
        for p in points:
            path.lineTo(p)
        path.lineTo(points[-1].x(), h)
        path.closeSubpath()

        fill_color = QColor(self.theme["ACCENT"])
        fill_color.setAlpha(70)
        painter.fillPath(path, fill_color)

        # line stroke
        line_pen = QPen(QColor(self.theme["ACCENT"]))
        line_pen.setWidth(2)
        painter.setPen(line_pen)
        for i in range(len(points) - 1):
            painter.drawLine(points[i], points[i + 1])


class ChartPanel(QWidget):
    """Chart with a title/current-value header and axis labels, like Task Manager."""

    def __init__(self, title, theme, max_points=60, max_value=100, unit="%"):
        super().__init__()
        self.unit = unit

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(8)

        header_row = QHBoxLayout()
        self._title_label = QLabel(title)
        self._value_label = QLabel(f"0{unit}")
        header_row.addWidget(self._title_label)
        header_row.addStretch()
        header_row.addWidget(self._value_label)
        outer.addLayout(header_row)

        chart_row = QHBoxLayout()
        chart_row.setSpacing(6)

        self._top_axis = QLabel(f"{max_value}{unit}")
        self._bottom_axis = QLabel(f"0{unit}")

        axis_col = QVBoxLayout()
        axis_col.addWidget(self._top_axis, alignment=Qt.AlignTop)
        axis_col.addStretch()
        axis_col.addWidget(self._bottom_axis, alignment=Qt.AlignBottom)

        self.chart = LineChart(theme, max_points=max_points, max_value=max_value)

        chart_row.addLayout(axis_col)
        chart_row.addWidget(self.chart, stretch=1)
        outer.addLayout(chart_row)

        self._footer_label = QLabel(f"last {max_points} seconds")
        outer.addWidget(self._footer_label, alignment=Qt.AlignLeft)

        self.apply_theme(theme)

    def add_point(self, value):
        self.chart.add_point(value)
        self._value_label.setText(f"{value:.0f}{self.unit}")

    def apply_theme(self, theme):
        self._title_label.setStyleSheet(f"""
            color: {theme['TEXT_PRI']}; font-size: 14px; font-weight: 700;
            background: transparent; border: none;
        """)
        self._value_label.setStyleSheet(f"""
            color: {theme['ACCENT']}; font-size: 14px; font-weight: 700;
            background: transparent; border: none;
        """)
        for lbl in (self._top_axis, self._bottom_axis, self._footer_label):
            lbl.setStyleSheet(f"""
                color: {theme['TEXT_SEC']}; font-size: 10px;
                background: transparent; border: none;
            """)
        self.chart.apply_theme(theme)


# ─────────────────────────────────────────
#  MONITOR PAGE
# ─────────────────────────────────────────
class MonitorPage(QWidget):

    def __init__(self):
        super().__init__()
        self.theme_name = "dark"

        outer = QVBoxLayout(self)
        outer.setContentsMargins(40, 32, 40, 40)
        outer.setSpacing(20)

        self._heading = QLabel("System & Network Monitor")
        outer.addWidget(self._heading)

        # ── KPI row ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)

        self.download_card = StatCard("Download Speed", THEMES["dark"])
        self.upload_card = StatCard("Upload Speed", THEMES["dark"])
        self.ram_card = StatCard("RAM Usage", THEMES["dark"])
        self.disk_card = StatCard("Disk Activity", THEMES["dark"])

        for card in (self.download_card, self.upload_card, self.ram_card, self.disk_card):
            kpi_row.addWidget(card)

        outer.addLayout(kpi_row)

        # ── CPU chart panel (statistics-page centerpiece) ──
        self._cpu_panel_frame = QWidget()
        self._cpu_panel_frame.setGraphicsEffect(_shadow())
        panel_layout = QVBoxLayout(self._cpu_panel_frame)
        panel_layout.setContentsMargins(20, 16, 20, 16)

        self.cpu_chart = ChartPanel("CPU Usage", THEMES["dark"], max_points=60, max_value=100, unit="%")
        panel_layout.addWidget(self.cpu_chart)

        outer.addWidget(self._cpu_panel_frame)
        outer.addStretch()

        # baseline counters for network + disk I/O speed calculation
        counters = psutil.net_io_counters()
        self._last_bytes_sent = counters.bytes_sent
        self._last_bytes_recv = counters.bytes_recv

        disk_io = psutil.disk_io_counters()
        self._last_disk_read = disk_io.read_bytes
        self._last_disk_write = disk_io.write_bytes

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(1000)  # poll every second

        self.apply_theme("dark")

    def _refresh(self):
        # network speed (delta over ~1s interval)
        counters = psutil.net_io_counters()

        sent_delta = counters.bytes_sent - self._last_bytes_sent
        recv_delta = counters.bytes_recv - self._last_bytes_recv

        self._last_bytes_sent = counters.bytes_sent
        self._last_bytes_recv = counters.bytes_recv

        self.upload_card.set_value(_format_speed(sent_delta))
        self.download_card.set_value(_format_speed(recv_delta))

        # disk I/O speed (read + write combined, delta over ~1s interval)
        disk_io = psutil.disk_io_counters()

        read_delta = disk_io.read_bytes - self._last_disk_read
        write_delta = disk_io.write_bytes - self._last_disk_write

        self._last_disk_read = disk_io.read_bytes
        self._last_disk_write = disk_io.write_bytes

        self.disk_card.set_value(_format_speed(read_delta + write_delta))

        # system resource usage
        cpu_percent = psutil.cpu_percent(interval=None)
        ram_percent = psutil.virtual_memory().percent

        self.ram_card.set_value(f"{ram_percent:.0f}%")

        self.cpu_chart.add_point(cpu_percent)

    def showEvent(self, event):
        # reset psutil's internal cpu_percent sampling window each time the
        # page becomes visible so the first reading after switching tabs
        # isn't stale
        psutil.cpu_percent(interval=None)
        super().showEvent(event)

    # ── theming ──

    def apply_theme(self, theme_name: str):
        self.theme_name = theme_name
        theme = THEMES[theme_name]

        self.setStyleSheet("background: transparent;")

        self._heading.setStyleSheet(f"""
            color: {theme['TEXT_PRI']}; font-size: 22px; font-weight: 700;
            background: transparent; border: none;
        """)

        for card in (self.download_card, self.upload_card, self.ram_card, self.disk_card):
            card.apply_theme(theme)

        self._cpu_panel_frame.setStyleSheet(f"""
            QWidget {{
                background-color: {theme['BG_SURFACE']};
                border: 1px solid {theme['BORDER']};
                border-radius: 12px;
            }}
        """)
        self.cpu_chart.apply_theme(theme)