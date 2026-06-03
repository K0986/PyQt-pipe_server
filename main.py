"""
JACK Launcher — Entry point.

Flow:  LauncherWindow  →  AuthWindow  →  MainWindow

Run:
    pip install PyQt5 requests
    python main.py
"""

import sys
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import Qt

from keyauth import KeyAuthAPI, get_file_checksum, KeyAuthError
from launcher import LauncherWindow
from auth_window import AuthWindow
from main_window import MainWindow

APP_NAME    = "JACK X CHEAT"
OWNER_ID    = "wsdYQ2HlHZ"
VERSION     = "1.0"


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    try:
        checksum = get_file_checksum(__file__)
    except Exception:
        checksum = ""

    keyauth = KeyAuthAPI(
        name=APP_NAME,
        ownerid=OWNER_ID,
        version=VERSION,
        checksum=checksum,
    )

    print("[JACK] Initializing KeyAuth session...")
    ok, msg = keyauth.init()
    if not ok:
        QMessageBox.critical(None, "Initialization Error", f"KeyAuth init failed:\n{msg}")
        sys.exit(1)
    print(f"[JACK] {msg}")

    windows: dict = {}

    def show_main(user_data):
        main_win = MainWindow(user_data)
        windows["main"] = main_win
        main_win.show()

    def show_launcher():
        auth = windows.get("auth")
        if auth:
            auth.hide()
        launcher = windows.get("launcher")
        if launcher:
            launcher.show()

    def show_auth():
        launcher = windows.get("launcher")
        if launcher:
            launcher.hide()
        auth_win = AuthWindow(keyauth, on_success=show_main, on_back=show_launcher)
        windows["auth"] = auth_win
        auth_win.show()

    launcher = LauncherWindow(on_enter=show_auth)
    windows["launcher"] = launcher
    launcher.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
