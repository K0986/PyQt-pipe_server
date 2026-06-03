"""
Auth window — Login / Register with KeyAuth.
Left: animated stripe panel. Right: Sign In / Login tabs + form.
Cyberpunk glow border + pulse animation. 30% larger.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFrame, QApplication, QSizePolicy
)
from PyQt5.QtCore import Qt, QPoint, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPainter, QColor, QPen, QLinearGradient, QBrush, QPolygon
from PyQt5.QtCore import QPoint as QP

import os

ASSETS = os.path.join(os.path.dirname(__file__), "assets")

STYLE = """
QWidget#auth {
    background-color: #070b16;
}
QWidget#leftPanel {
    background-color: transparent;
}
QWidget#rightPanel {
    background-color: #090e1e;
    border-left: 1px solid #1a3a66;
}
QLabel#winTitle {
    color: #e8f0ff;
    font-size: 22px;
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
QPushButton#tabBtn {
    background: transparent;
    border: none;
    border-bottom: 2px solid transparent;
    color: #3a3a6a;
    font-size: 14px;
    font-family: 'Segoe UI', Arial;
    padding: 8px 22px 10px 22px;
    font-weight: bold;
    letter-spacing: 1px;
}
QPushButton#tabBtn[active="true"] {
    color: #e8f0ff;
    border-bottom: 2px solid #7b2fff;
}
QPushButton#tabBtn:hover { color: #9090cc; }
QLineEdit#field {
    background-color: #0c1020;
    border: 1px solid #1e2a55;
    border-radius: 8px;
    color: #d8e0ff;
    font-size: 13px;
    font-family: 'Segoe UI', Arial;
    padding: 11px 14px 11px 38px;
    selection-background-color: #3344aa;
    min-height: 20px;
}
QLineEdit#field:focus {
    border: 1px solid #5566dd;
    background-color: #0e1428;
}
QLineEdit#field::placeholder { color: #2a2a55; }
QPushButton#btnSubmit {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #4422cc, stop:1 #7733ff);
    color: #ffffff;
    border: none;
    border-radius: 8px;
    font-size: 13px;
    font-weight: bold;
    font-family: 'Segoe UI', Arial;
    padding: 13px 0;
    letter-spacing: 3px;
    min-height: 20px;
}
QPushButton#btnSubmit:hover {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5533dd, stop:1 #8844ff);
}
QPushButton#btnSubmit:pressed {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #3311aa, stop:1 #5522cc);
}
QPushButton#btnBack {
    background: transparent;
    color: #3a3a6a;
    border: 1px solid #252555;
    border-radius: 6px;
    font-size: 11px;
    font-family: 'Segoe UI', Arial;
    padding: 6px 16px;
    letter-spacing: 1px;
}
QPushButton#btnBack:hover {
    color: #8888cc;
    border-color: #4444aa;
    background: #0e0e2a;
}
QLabel#statusLabel {
    font-size: 11px;
    font-family: 'Segoe UI', Arial;
    padding: 2px 0;
    min-height: 16px;
    background: transparent;
}
QLabel#fieldIcon {
    color: #3a3a77;
    font-size: 14px;
    background: transparent;
}
"""


class StripePanel(QWidget):
    """Left panel — animated vertical stripes + diamond."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("leftPanel")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._scan = 0.0

        self._scan_timer = QTimer(self)
        self._scan_timer.setInterval(20)
        self._scan_timer.timeout.connect(self._tick)
        self._scan_timer.start()

    def _tick(self):
        self._scan = (self._scan + 0.006) % 1.0
        self.update()

    def paintEvent(self, _event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Background gradient
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0, QColor("#0c0820"))
        grad.setColorAt(0.5, QColor("#080c1c"))
        grad.setColorAt(1, QColor("#050810"))
        p.fillRect(0, 0, w, h, grad)

        # Vertical stripes
        stripe_count = 9
        stripe_w = w // stripe_count
        for i in range(stripe_count):
            x = i * stripe_w
            sg = QLinearGradient(x, 0, x + stripe_w, 0)
            alpha = 22 if i % 2 == 0 else 10
            sg.setColorAt(0, QColor(60, 40, 200, alpha))
            sg.setColorAt(1, QColor(60, 40, 200, 0))
            p.fillRect(x, 0, stripe_w, h, sg)

        # Vertical line edges
        pen = QPen(QColor(80, 60, 220, 35))
        pen.setWidth(1)
        p.setPen(pen)
        for i in range(1, stripe_count):
            x = i * stripe_w
            p.drawLine(x, 0, x, h)

        # Horizontal accent lines
        pen2 = QPen(QColor(50, 50, 180, 45))
        pen2.setWidth(1)
        p.setPen(pen2)
        for frac in [0.15, 0.35, 0.55, 0.75, 0.9]:
            y = int(h * frac)
            p.drawLine(14, y, w - 14, y)

        # Animated horizontal scan line
        scan_y = int(self._scan * h)
        sg2 = QLinearGradient(0, scan_y - 30, 0, scan_y + 30)
        sg2.setColorAt(0, QColor(0, 212, 255, 0))
        sg2.setColorAt(0.5, QColor(0, 212, 255, 30))
        sg2.setColorAt(1, QColor(0, 212, 255, 0))
        p.fillRect(0, scan_y - 30, w, 60, sg2)

        # Corner marks
        p.setPen(QPen(QColor(0, 212, 255, 70), 1))
        seg = 12
        for cx2, cy2, dx, dy in [
            (6, 6, seg, 0), (6, 6, 0, seg),
            (w-6, 6, -seg, 0), (w-6, 6, 0, seg),
            (6, h-6, seg, 0), (6, h-6, 0, -seg),
            (w-6, h-6, -seg, 0), (w-6, h-6, 0, -seg),
        ]:
            p.drawLine(cx2, cy2, cx2 + dx, cy2 + dy)

        # Centre diamond
        cx, cy = w // 2, h // 2
        sz = 22
        diamond = QPolygon([QP(cx, cy-sz), QP(cx+sz, cy), QP(cx, cy+sz), QP(cx-sz, cy)])
        p.setPen(QPen(QColor(0, 212, 255, 90), 1))
        p.setBrush(QBrush(QColor(0, 20, 50, 180)))
        p.drawPolygon(diamond)
        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 212, 255, 140)))
        p.drawEllipse(cx - 4, cy - 4, 8, 8)

        p.end()


class FieldRow(QWidget):
    """Input field with a circle icon prefix."""

    def __init__(self, placeholder: str, echo_password: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("auth")
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.edit = QLineEdit()
        self.edit.setObjectName("field")
        self.edit.setPlaceholderText(placeholder)
        if echo_password:
            self.edit.setEchoMode(QLineEdit.Password)

        layout.addWidget(self.edit)

    def text(self) -> str:
        return self.edit.text()

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        field = self.edit
        fy = field.y() + field.height() // 2
        p.setPen(QPen(QColor("#2a2a77"), 1))
        p.setBrush(QBrush(QColor("#14143a")))
        p.drawEllipse(field.x() + 13, fy - 5, 10, 10)
        p.end()


class AuthWorker(QThread):
    done = pyqtSignal(bool, str)

    def __init__(self, fn, *args):
        super().__init__()
        self._fn = fn
        self._args = args

    def run(self):
        ok, msg = self._fn(*self._args)
        self.done.emit(ok, msg)


class AuthWindow(QWidget):
    def __init__(self, keyauth_api, on_success, on_back=None):
        super().__init__()
        self._api        = keyauth_api
        self._on_success = on_success
        self._on_back    = on_back
        self._drag_pos   = QPoint()
        self._mode       = "login"
        self._worker     = None
        self._pulse      = 0.4
        self._pulse_dir  = 1

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

    def _build_ui(self):
        self.setObjectName("auth")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setFixedSize(1014, 572)
        self.setStyleSheet(STYLE)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._title_bar())

        # Cyan separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #00d4ff44; border: none;")
        root.addWidget(sep)

        content = QHBoxLayout()
        content.setContentsMargins(0, 0, 0, 0)
        content.setSpacing(0)

        content.addWidget(StripePanel(), stretch=4)
        content.addWidget(self._right_panel(), stretch=5)

        root.addLayout(content)

    def _title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("auth")
        bar.setFixedHeight(52)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(22, 0, 16, 0)
        layout.setSpacing(0)

        # Logo bars
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
        sub = QLabel("AUTHENTICATION")
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

    def _right_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("rightPanel")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(44, 28, 44, 28)
        layout.setSpacing(0)

        # Tab row
        tab_row = QHBoxLayout()
        tab_row.setSpacing(0)
        tab_row.setAlignment(Qt.AlignCenter)

        self._tab_signin = QPushButton("Sign In")
        self._tab_signin.setObjectName("tabBtn")
        self._tab_signin.setProperty("active", "false")
        self._tab_signin.clicked.connect(lambda: self._switch_mode("register"))

        self._tab_login = QPushButton("Login")
        self._tab_login.setObjectName("tabBtn")
        self._tab_login.setProperty("active", "true")
        self._tab_login.clicked.connect(lambda: self._switch_mode("login"))

        tab_row.addWidget(self._tab_signin)
        tab_row.addWidget(self._tab_login)
        layout.addLayout(tab_row)
        layout.addSpacing(24)

        # Fields
        self._user_row    = FieldRow("Username")
        self._pass_row    = FieldRow("Password", echo_password=True)
        self._license_row = FieldRow("License Key")
        self._license_row.setVisible(False)

        layout.addWidget(self._user_row)
        layout.addSpacing(12)
        layout.addWidget(self._pass_row)
        layout.addSpacing(12)
        layout.addWidget(self._license_row)
        layout.addSpacing(24)

        # Submit button
        self._btn_submit = QPushButton("LOG IN")
        self._btn_submit.setObjectName("btnSubmit")
        self._btn_submit.setFixedHeight(48)
        self._btn_submit.clicked.connect(self._handle_submit)
        layout.addWidget(self._btn_submit)
        layout.addSpacing(10)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setObjectName("statusLabel")
        self._status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status_label)

        layout.addStretch()

        # Back button
        back_row = QHBoxLayout()
        back_row.setAlignment(Qt.AlignCenter)
        btn_back = QPushButton("← BACK")
        btn_back.setObjectName("btnBack")
        btn_back.clicked.connect(self._go_back)
        back_row.addWidget(btn_back)
        layout.addLayout(back_row)

        return panel

    def _go_back(self):
        self.hide()
        if self._on_back:
            self._on_back()

    def _switch_mode(self, mode: str):
        self._mode = mode
        is_register = mode == "register"
        self._license_row.setVisible(is_register)

        self._tab_login.setProperty("active", "false" if is_register else "true")
        self._tab_signin.setProperty("active", "true" if is_register else "false")
        for btn in (self._tab_login, self._tab_signin):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

        self._btn_submit.setText("SIGN IN" if is_register else "LOG IN")
        self._status_label.setText("")

    def _set_status(self, msg: str, ok: bool = False):
        color = "#00e676" if ok else "#ff2d78"
        self._status_label.setStyleSheet(
            f"color: {color}; font-size: 11px; font-family: 'Segoe UI', Arial;"
        )
        self._status_label.setText(msg)

    def _handle_submit(self):
        username    = self._user_row.text().strip()
        password    = self._pass_row.text().strip()
        license_key = self._license_row.text().strip()

        if not username or not password:
            self._set_status("Username and password are required.")
            return
        if self._mode == "register" and not license_key:
            self._set_status("License key is required to register.")
            return

        self._btn_submit.setEnabled(False)
        self._btn_submit.setText("...")
        self._set_status("Connecting to KeyAuth…")

        if self._mode == "login":
            fn, args = self._api.login, (username, password)
        else:
            fn, args = self._api.register, (username, password, license_key)

        self._worker = AuthWorker(fn, *args)
        self._worker.done.connect(self._on_auth_done)
        self._worker.start()

    def _on_auth_done(self, ok: bool, msg: str):
        label = "SIGN IN" if self._mode == "register" else "LOG IN"
        self._btn_submit.setEnabled(True)
        self._btn_submit.setText(label)
        self._set_status(msg, ok)
        if ok:
            self.hide()
            self._on_success(self._api.user_data)

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Outer glow layers
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

        # Purple accent
        p.setPen(QPen(QColor(123, 47, 255, int(20 * self._pulse)), 1))
        p.drawRect(2, 2, w - 4, h - 4)

        # Solid inner border
        p.setPen(QPen(QColor(0, 212, 255, 160), 1))
        p.drawRect(1, 1, w - 2, h - 2)

        # Corner accent marks
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
