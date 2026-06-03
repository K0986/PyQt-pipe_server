"""
Launcher window — first screen shown on startup.
4-card grid with status badges. Cyberpunk glow border + card hover animation.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy, QApplication
)
from PyQt5.QtCore import Qt, QPoint, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPainter, QColor, QPen, QFont, QLinearGradient, QBrush, QPolygon
from PyQt5.QtCore import QPoint as QP

import os

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

BADGE_STYLES = {
    "ONLINE":  ("#00ffcc", "#002a20"),
    "UPDATED": ("#00d4ff", "#001a25"),
    "BETA":    ("#cc44ff", "#200040"),
}

CARDS = [
    {"name": "CYBER STRIKE",   "badge": "ONLINE"},
    {"name": "NEON RAIDERS",   "badge": "ONLINE"},
    {"name": "GHOST PROTOCOL", "badge": "UPDATED"},
    {"name": "VOID RUNNER",    "badge": "BETA"},
]

STYLE = """
QWidget#launcher {
    background-color: #070b16;
}
QLabel#winTitle {
    color: #e8f0ff;
    font-size: 24px;
    font-weight: bold;
    font-family: 'Segoe UI', Arial;
    letter-spacing: 6px;
    background: transparent;
}
QLabel#winSub {
    color: #3a4a7a;
    font-size: 9px;
    font-family: 'Segoe UI', Arial;
    letter-spacing: 4px;
    background: transparent;
}
QPushButton#btnMinimize {
    color: #00d4ff;
    background: transparent;
    border: 1px solid #00d4ff44;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    min-width: 26px;
    min-height: 22px;
    padding: 0 4px;
}
QPushButton#btnMinimize:hover {
    background-color: #00d4ff22;
    border-color: #00d4ff;
}
QPushButton#btnClose {
    color: #ff2d78;
    background: transparent;
    border: 1px solid #ff2d7844;
    border-radius: 4px;
    font-size: 13px;
    font-weight: bold;
    min-width: 26px;
    min-height: 22px;
    padding: 0 4px;
}
QPushButton#btnClose:hover {
    background-color: #ff2d7822;
    border-color: #ff2d78;
}
QPushButton#btnPlay {
    background: transparent;
    border: 1px solid #00d4ff55;
    border-radius: 6px;
    color: #00d4ff;
    font-size: 14px;
    padding: 9px 0;
    font-weight: bold;
    font-family: 'Segoe UI', Arial;
    letter-spacing: 2px;
}
QPushButton#btnPlay:hover {
    background: #00d4ff18;
    border-color: #00d4ff;
    color: #ffffff;
}
QPushButton#btnPlay:pressed {
    background: #00d4ff30;
}
"""


class LinesPanel(QWidget):
    """Animated vertical-stripe + diamond art panel inside each card."""

    def __init__(self, badge_color="#00d4ff", parent=None):
        super().__init__(parent)
        self._badge_color = badge_color
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumHeight(240)

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        grad = QLinearGradient(0, 0, 0, h)
        grad.setColorAt(0, QColor("#090e20"))
        grad.setColorAt(1, QColor("#050810"))
        p.fillRect(0, 0, w, h, grad)

        pen = QPen(QColor(60, 100, 200, 28))
        pen.setWidth(1)
        p.setPen(pen)
        step = max(14, w // 9)
        for x in range(0, w, step):
            p.drawLine(x, 0, x, h)

        pen2 = QPen(QColor(40, 80, 180, 40))
        pen2.setWidth(1)
        p.setPen(pen2)
        for frac in [0.25, 0.5, 0.75]:
            y = int(h * frac)
            p.drawLine(6, y, w - 6, y)

        # Corner accent marks
        corner_pen = QPen(QColor(self._badge_color), 1)
        corner_pen.setColor(QColor(self._badge_color[0:7] + "66" if len(self._badge_color) == 7 else self._badge_color))
        p.setPen(QPen(QColor(0, 212, 255, 60), 1))
        size = 10
        for cx2, cy2 in [(8, 8), (w-8, 8), (8, h-8), (w-8, h-8)]:
            p.drawLine(cx2 - size, cy2, cx2, cy2)
            p.drawLine(cx2, cy2, cx2, cy2 - size) if cy2 < h // 2 else p.drawLine(cx2, cy2, cx2, cy2 + size)

        # Centre diamond
        cx, cy = w // 2, h // 2
        sz = 16
        diamond = QPolygon([QP(cx, cy-sz), QP(cx+sz, cy), QP(cx, cy+sz), QP(cx-sz, cy)])
        p.setPen(QPen(QColor(0, 212, 255, 80), 1))
        p.setBrush(QBrush(QColor(0, 30, 60, 160)))
        p.drawPolygon(diamond)

        # Inner diamond dot
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255, 120)))
        p.drawEllipse(cx - 3, cy - 3, 6, 6)
        p.end()


class BadgeLabel(QLabel):
    def __init__(self, text: str, fg: str, bg: str, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(18)
        self.setStyleSheet(f"""
            color: {fg};
            background-color: {bg};
            border: 1px solid {fg};
            border-radius: 3px;
            font-size: 8px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial;
            letter-spacing: 1.5px;
            padding: 1px 6px;
        """)
        self.setAlignment(Qt.AlignCenter)


class GameCard(QFrame):
    """Card with animated cyberpunk glow on hover."""

    def __init__(self, name: str, badge: str, on_click, parent=None):
        super().__init__(parent)
        self.setFixedSize(248, 420)
        self._glow  = 0.0
        self._glow_dir = 0
        self._badge = badge
        fg_color = BADGE_STYLES.get(badge, ("#00d4ff", "#001a25"))[0]
        self._glow_color = QColor(fg_color)

        self._glow_timer = QTimer(self)
        self._glow_timer.setInterval(16)
        self._glow_timer.timeout.connect(self._tick_glow)

        self.setStyleSheet(f"""
            QFrame {{
                background-color: #0a0e1e;
                border: 1px solid #1a2a55;
                border-radius: 10px;
            }}
        """)
        self.setCursor(Qt.PointingHandCursor)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        badge_row = QHBoxLayout()
        badge_row.setContentsMargins(0, 0, 0, 0)
        badge_row.addStretch()
        fg, bg = BADGE_STYLES.get(badge, ("#00d4ff", "#001a25"))
        badge_lbl = BadgeLabel(badge, fg, bg)
        badge_row.addWidget(badge_lbl)
        outer.addLayout(badge_row)

        lines = LinesPanel(badge_color=fg)
        outer.addWidget(lines, stretch=1)

        name_lbl = QLabel(name)
        name_lbl.setAlignment(Qt.AlignCenter)
        name_lbl.setStyleSheet("""
            color: #c0d0ff;
            font-size: 10px;
            font-weight: bold;
            font-family: 'Segoe UI', Arial;
            letter-spacing: 3px;
            background: transparent;
            border: none;
        """)
        outer.addWidget(name_lbl)

        play_btn = QPushButton("▶  PLAY")
        play_btn.setObjectName("btnPlay")
        play_btn.setFixedHeight(38)
        play_btn.clicked.connect(on_click)
        outer.addWidget(play_btn)

    def enterEvent(self, e):
        self._glow_dir = 1
        if not self._glow_timer.isActive():
            self._glow_timer.start()

    def leaveEvent(self, e):
        self._glow_dir = -1
        if not self._glow_timer.isActive():
            self._glow_timer.start()

    def _tick_glow(self):
        self._glow += self._glow_dir * 0.08
        self._glow = max(0.0, min(1.0, self._glow))
        if (self._glow <= 0.0 and self._glow_dir < 0) or \
           (self._glow >= 1.0 and self._glow_dir > 0):
            self._glow_timer.stop()
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._glow <= 0:
            return
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        c = self._glow_color

        layers = [
            (3, int(15 * self._glow)),
            (2, int(40 * self._glow)),
            (1, int(80 * self._glow)),
            (0, int(180 * self._glow)),
        ]
        for expand, alpha in layers:
            if alpha <= 0:
                continue
            color = QColor(c.red(), c.green(), c.blue(), alpha)
            pen = QPen(color, 1)
            p.setPen(pen)
            adj = r.adjusted(-expand, -expand, expand, expand)
            p.drawRoundedRect(adj, 10 + expand, 10 + expand)

        accent = QColor(c.red(), c.green(), c.blue(), int(220 * self._glow))
        p.setPen(QPen(accent, 2))
        w, h = self.width(), self.height()
        seg = 12
        for cx2, cy2, dx, dy in [
            (1, 1, seg, 0), (1, 1, 0, seg),
            (w-1, 1, -seg, 0), (w-1, 1, 0, seg),
            (1, h-1, seg, 0), (1, h-1, 0, -seg),
            (w-1, h-1, -seg, 0), (w-1, h-1, 0, -seg),
        ]:
            p.drawLine(cx2, cy2, cx2 + dx, cy2 + dy)

        p.end()


class LauncherWindow(QWidget):
    def __init__(self, on_enter):
        super().__init__()
        self._on_enter = on_enter
        self._drag_pos = QPoint()
        self._pulse    = 0.4
        self._pulse_dir = 1

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

        self._build_ui()

    def _tick_pulse(self):
        self._pulse += self._pulse_dir * 0.018
        if self._pulse >= 1.0:
            self._pulse = 1.0
            self._pulse_dir = -1
        elif self._pulse <= 0.25:
            self._pulse = 0.25
            self._pulse_dir = 1
        self.update()

    def _on_play_clicked(self):
        self._on_enter()

    def _build_ui(self):
        self.setObjectName("launcher")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.setFixedSize(1144, 598)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._title_bar())

        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #00d4ff44; border: none;")
        root.addWidget(sep)

        body = QVBoxLayout()
        body.setContentsMargins(30, 24, 30, 30)
        body.setSpacing(0)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(22)
        cards_row.setAlignment(Qt.AlignCenter)

        for card_def in CARDS:
            card = GameCard(
                name=card_def["name"],
                badge=card_def["badge"],
                on_click=self._on_play_clicked,   # ← hooked here
            )
            cards_row.addWidget(card)

        body.addLayout(cards_row)
        root.addLayout(body)

    def _title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("launcher")
        bar.setFixedHeight(56)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(22, 0, 16, 0)
        layout.setSpacing(0)

        bar_col = QWidget()
        bar_col.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(bar_col)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(2)
        for h2 in (8, 5, 3):
            b = QFrame()
            b.setFixedSize(3, h2)
            b.setStyleSheet("background: #00d4ff;")
            bl.addWidget(b)
        bl.addStretch()
        layout.addWidget(bar_col)
        layout.addSpacing(10)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(0)
        title = QLabel("JACK")
        title.setObjectName("winTitle")
        sub = QLabel("GAME LAUNCHER")
        sub.setObjectName("winSub")
        txt_col.addWidget(title)
        txt_col.addWidget(sub)
        layout.addLayout(txt_col)

        layout.addStretch()

        btn_min = QPushButton("—")
        btn_min.setObjectName("btnMinimize")
        btn_min.setFixedSize(28, 24)
        btn_min.clicked.connect(self.showMinimized)

        btn_close = QPushButton("✕")
        btn_close.setObjectName("btnClose")
        btn_close.setFixedSize(28, 24)
        btn_close.clicked.connect(QApplication.instance().quit)

        layout.addWidget(btn_min)
        layout.addSpacing(6)
        layout.addWidget(btn_close)
        layout.addSpacing(4)
        return bar

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        glow_layers = [
            (0, 212, 255, int(8  * self._pulse)),
            (0, 212, 255, int(18 * self._pulse)),
            (0, 212, 255, int(45 * self._pulse)),
        ]
        for i, (r, g, b, a) in enumerate(glow_layers):
            if a <= 0:
                continue
            pad = (len(glow_layers) - i) * 2
            p.setPen(QPen(QColor(r, g, b, a), 1))
            p.drawRect(pad, pad, w - pad*2, h - pad*2)

        p.setPen(QPen(QColor(123, 47, 255, int(25 * self._pulse)), 1))
        p.drawRect(2, 2, w - 4, h - 4)

        p.setPen(QPen(QColor(0, 212, 255, 160), 1))
        p.drawRect(1, 1, w - 2, h - 2)

        seg = 18
        p.setPen(QPen(QColor(0, 212, 255, int(200 * self._pulse)), 2))
        for cx2, cy2, dx, dy in [
            (0, 0, seg, 0), (0, 0, 0, seg),
            (w, 0, -seg, 0), (w, 0, 0, seg),
            (0, h, seg, 0), (0, h, 0, -seg),
            (w, h, -seg, 0), (w, h, 0, -seg),
        ]:
            p.drawLine(cx2, cy2, cx2 + dx, cy2 + dy)

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)
