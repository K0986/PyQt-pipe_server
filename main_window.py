"""
JACK Main Window — full Supremo Panel features integrated.
Sidebar: External / Supreme / Esp / Utility / Brutal / Hockey + Dashboard / Settings
Content: nested sub-tabs (Home, Aimbot, ESP, Brutal, Settings)
Bottom:  coloured log strip
"""

import sys, os, queue, time, threading, subprocess, urllib.request

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QScrollArea, QTextEdit, QFrame, QSizePolicy, QStackedWidget,
    QButtonGroup, QAbstractItemView, QColorDialog
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer, QPoint, pyqtSlot, QObject
from PyQt5.QtGui import QColor, QFont, QCursor, QTextCharFormat, QTextCursor, QPainter, QPen, QLinearGradient, QBrush

# ─── Colour palette ───────────────────────────────────────────────────────────
C_BG        = "#0d0d1a"
C_BG2       = "#111122"
C_SIDEBAR   = "#0f0f22"
C_SEL_TAB   = "#1a1a35"
C_CYAN      = "#00d4ff"
C_CYAN_DK   = "#007a99"
C_CYAN_BTN  = "#008fb5"
C_GREEN     = "#00e676"
C_PINK      = "#ff2d78"
C_GOLD      = "#ffaa00"
C_PURPLE    = "#7b2fff"
C_TEXT      = "#e0e0ff"
C_TEXT2     = "#7a7aaa"
C_BORDER    = "#1e1e40"
C_BTN_OFF   = "#0e1a24"
C_STEP_RUN  = "#0d1f28"
C_STEP_OK   = "#0d2018"
C_STEP_FAIL = "#200d15"
MONO        = "Consolas"

DLL_URL = "https://files.catbox.moe/552c5m.dll"

# ─── Win32 pipe + injection helpers ──────────────────────────────────────────
if sys.platform == "win32":
    import ctypes, ctypes.wintypes, struct as _struct

    GENERIC_READ  = 0x80000000
    GENERIC_WRITE = 0x40000000
    OPEN_EXISTING = 3
    PIPE_NAME     = r"\\.\pipe\esp_pipe"
    _k32 = ctypes.windll.kernel32

    # Random subdir so DLL path changes each panel session
    _DLL_SUBDIR = os.urandom(4).hex()

    _HANDLE  = ctypes.c_void_p
    _BOOL    = ctypes.c_bool
    _DWORD   = ctypes.c_uint32
    _SIZE_T  = ctypes.c_size_t
    _LPCVOID = ctypes.c_void_p
    _LPVOID  = ctypes.c_void_p

    INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

    _k32.CreateFileW.restype  = _HANDLE
    _k32.CreateFileW.argtypes = [ctypes.c_wchar_p, _DWORD, _DWORD, _LPVOID, _DWORD, _DWORD, _HANDLE]
    _k32.SetNamedPipeHandleState.restype  = _BOOL
    _k32.SetNamedPipeHandleState.argtypes = [_HANDLE, ctypes.POINTER(_DWORD), ctypes.POINTER(_DWORD), ctypes.POINTER(_DWORD)]
    _k32.WriteFile.restype  = _BOOL
    _k32.WriteFile.argtypes = [_HANDLE, _LPCVOID, _DWORD, ctypes.POINTER(_DWORD), _LPVOID]
    _k32.ReadFile.restype   = _BOOL
    _k32.ReadFile.argtypes  = [_HANDLE, _LPVOID, _DWORD, ctypes.POINTER(_DWORD), _LPVOID]
    _k32.PeekNamedPipe.restype  = _BOOL
    _k32.PeekNamedPipe.argtypes = [_HANDLE, _LPVOID, _DWORD, ctypes.POINTER(_DWORD), ctypes.POINTER(_DWORD), ctypes.POINTER(_DWORD)]
    _k32.CreateToolhelp32Snapshot.restype  = _HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = [_DWORD, _DWORD]
    _k32.CloseHandle.restype  = _BOOL
    _k32.CloseHandle.argtypes = [_HANDLE]
    _k32.OpenProcess.restype  = _HANDLE
    _k32.OpenProcess.argtypes = [_DWORD, _BOOL, _DWORD]
    _k32.VirtualAllocEx.restype  = _LPVOID
    _k32.VirtualAllocEx.argtypes = [_HANDLE, _LPVOID, _SIZE_T, _DWORD, _DWORD]
    _k32.WriteProcessMemory.restype  = _BOOL
    _k32.WriteProcessMemory.argtypes = [_HANDLE, _LPVOID, _LPCVOID, _SIZE_T, ctypes.POINTER(_SIZE_T)]
    _k32.VirtualFreeEx.restype  = _BOOL
    _k32.VirtualFreeEx.argtypes = [_HANDLE, _LPVOID, _SIZE_T, _DWORD]
    _k32.GetModuleHandleW.restype  = _HANDLE
    _k32.GetModuleHandleW.argtypes = [ctypes.c_wchar_p]
    _k32.GetProcAddress.restype  = _LPVOID
    _k32.GetProcAddress.argtypes = [_HANDLE, ctypes.c_char_p]
    _k32.CreateRemoteThread.restype  = _HANDLE
    _k32.CreateRemoteThread.argtypes = [_HANDLE, _LPVOID, _SIZE_T, _LPVOID, _LPVOID, _DWORD, _LPVOID]
    _k32.WaitForSingleObject.restype  = _DWORD
    _k32.WaitForSingleObject.argtypes = [_HANDLE, _DWORD]
    _k32.GetLastError.restype   = _DWORD
    _k32.GetLastError.argtypes  = []
    _k32.GetExitCodeThread.restype  = _BOOL
    _k32.GetExitCodeThread.argtypes = [_HANDLE, ctypes.POINTER(_DWORD)]

    class _PROCENTRY32(ctypes.Structure):
        _fields_ = [
            ("dwSize",              ctypes.c_uint32),
            ("cntUsage",            ctypes.c_uint32),
            ("th32ProcessID",       ctypes.c_uint32),
            ("th32DefaultHeapID",   ctypes.c_size_t),
            ("th32ModuleID",        ctypes.c_uint32),
            ("cntThreads",          ctypes.c_uint32),
            ("th32ParentProcessID", ctypes.c_uint32),
            ("pcPriClassBase",      ctypes.c_int32),
            ("dwFlags",             ctypes.c_uint32),
            ("szExeFile",           ctypes.c_char * 260),
        ]

    _k32.Process32First.restype  = _BOOL
    _k32.Process32First.argtypes = [_HANDLE, ctypes.POINTER(_PROCENTRY32)]
    _k32.Process32Next.restype   = _BOOL
    _k32.Process32Next.argtypes  = [_HANDLE, ctypes.POINTER(_PROCENTRY32)]

    def _is_invalid(h):
        return h is None or h == INVALID_HANDLE_VALUE or h == -1

    def _open_pipe():
        h = _k32.CreateFileW(PIPE_NAME, GENERIC_READ | GENERIC_WRITE, 0, None, OPEN_EXISTING, 0, None)
        if _is_invalid(h):
            return None
        mode = _DWORD(2)
        _k32.SetNamedPipeHandleState(h, ctypes.byref(mode), None, None)
        return h

    def _write_pipe(h, text):
        data = (text + "\n").encode("utf-8")
        written = _DWORD(0)
        return bool(_k32.WriteFile(h, data, len(data), ctypes.byref(written), None))

    def _read_chunk(h, size=4096):
        buf = ctypes.create_string_buffer(size)
        read = _DWORD(0)
        ok = _k32.ReadFile(h, buf, size - 1, ctypes.byref(read), None)
        return buf.raw[:read.value] if ok and read.value else None

    def _peek_pipe(h):
        avail = _DWORD(0)
        ok = _k32.PeekNamedPipe(h, None, 0, None, ctypes.byref(avail), None)
        return bool(ok), avail.value

    def _close_pipe(h):
        if h and not _is_invalid(h):
            _k32.CloseHandle(h)

    def _is_emulator_running():
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq HD-Player.exe"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8", errors="replace")
            return "HD-Player.exe" in out
        except Exception:
            return False

    def _find_pid(name):
        snap = _k32.CreateToolhelp32Snapshot(0x2, 0)
        if _is_invalid(snap):
            return None
        e = _PROCENTRY32()
        e.dwSize = ctypes.sizeof(_PROCENTRY32)
        pid = None
        try:
            if _k32.Process32First(snap, ctypes.byref(e)):
                while True:
                    try:
                        n = e.szExeFile.decode("utf-8", errors="replace")
                    except Exception:
                        n = ""
                    if n.lower() == name.lower():
                        pid = e.th32ProcessID
                        break
                    if not _k32.Process32Next(snap, ctypes.byref(e)):
                        break
        finally:
            _k32.CloseHandle(snap)
        return pid

    def _check_pe64(data):
        if len(data) < 2 or data[:2] != b"MZ":
            return False, "Not a valid DLL (got HTML/error page?)"
        if len(data) < 0x40:
            return False, "File too small to be a valid PE"
        pe_off = _struct.unpack_from("<I", data, 0x3C)[0]
        if len(data) < pe_off + 6:
            return False, "File too small to contain PE header"
        if data[pe_off:pe_off + 4] != b"PE\x00\x00":
            return False, "Not a valid PE signature"
        machine = _struct.unpack_from("<H", data, pe_off + 4)[0]
        if machine == 0x014C:
            return False, "DLL is 32-bit — need 64-bit build"
        if machine != 0x8664:
            return False, f"Unknown machine type 0x{machine:04X}"
        return True, ""

    def _download_dll(url):
        try:
            tmp = os.environ.get("TEMP") or os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
            subdir = os.path.join(tmp, _DLL_SUBDIR)
            os.makedirs(subdir, exist_ok=True)
            path = os.path.join(subdir, "sp_mod.dll")
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            ok, err = _check_pe64(data)
            if not ok:
                return None, err
            with open(path, "wb") as f:
                f.write(data)
            return path, None
        except Exception as e:
            return None, str(e)

    def _get_or_download_dll(url):
        """Return cached DLL if valid; otherwise download fresh."""
        tmp  = os.environ.get("TEMP") or os.path.join(os.path.expanduser("~"), "AppData", "Local", "Temp")
        path = os.path.join(tmp, _DLL_SUBDIR, "sp_mod.dll")
        if os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    data = f.read()
                ok, _ = _check_pe64(data)
                if ok:
                    return path, None, True   # (path, err, from_cache)
            except Exception:
                pass
        p, e = _download_dll(url)
        return p, e, False
    def _inject_dll(dll_path):
        pid = _find_pid("HD-Player.exe")
        if not pid:
            return False, "HD-Player.exe not found — is BlueStacks running?"
        PROCESS_ALL_ACCESS = 0x1F0FFF
        MEM_COMMIT_RESERVE = 0x3000
        PAGE_READWRITE     = 0x04
        MEM_RELEASE        = 0x8000
        h = _k32.OpenProcess(PROCESS_ALL_ACCESS, False, pid)
        if not h:
            return False, f"OpenProcess failed (err {_k32.GetLastError()}) — run as Administrator"
        try:
            path_w = (dll_path + "\x00").encode("utf-16-le")
            sz = len(path_w)
            remote = _k32.VirtualAllocEx(h, None, sz, MEM_COMMIT_RESERVE, PAGE_READWRITE)
            if not remote:
                return False, f"VirtualAllocEx failed (err {_k32.GetLastError()})"
            written = _SIZE_T(0)
            ok = _k32.WriteProcessMemory(h, remote, ctypes.cast(ctypes.c_char_p(path_w), _LPCVOID), sz, ctypes.byref(written))
            if not ok:
                _k32.VirtualFreeEx(h, remote, 0, MEM_RELEASE)
                return False, f"WriteProcessMemory failed (err {_k32.GetLastError()})"
            hk       = _k32.GetModuleHandleW("kernel32.dll")
            load_lib = _k32.GetProcAddress(hk, b"LoadLibraryW")
            if not load_lib:
                _k32.VirtualFreeEx(h, remote, 0, MEM_RELEASE)
                return False, "GetProcAddress(LoadLibraryW) failed"
            ht = _k32.CreateRemoteThread(h, None, 0, load_lib, remote, 0, None)
            if not ht:
                _k32.VirtualFreeEx(h, remote, 0, MEM_RELEASE)
                return False, f"CreateRemoteThread failed (err {_k32.GetLastError()})"
            _k32.WaitForSingleObject(ht, 8000)
            exit_code = _DWORD(0)
            _k32.GetExitCodeThread(ht, ctypes.byref(exit_code))
            _k32.CloseHandle(ht)
            _k32.VirtualFreeEx(h, remote, 0, MEM_RELEASE)
            if exit_code.value == 0:
                return False, "LoadLibraryW returned NULL — antivirus, arch mismatch, or missing dependency"
            return True, ""
        finally:
            _k32.CloseHandle(h)

else:
    def _open_pipe():                    return None
    def _write_pipe(h, t):               return False
    def _read_chunk(h, s=4096):          return None
    def _peek_pipe(h):                   return False, 0
    def _close_pipe(h):                  pass
    def _is_emulator_running():          return False
    def _find_pid(name):                 return None
    def _download_dll(url):              return None, "Windows only"
    def _get_or_download_dll(url):       return None, "Windows only", False
    def _inject_dll(path):               return False, "Windows only"


# ─── Friendly error translation ───────────────────────────────────────────────
_FRIENDLY = [
    ("il2cpp",           "Game engine not found — make sure Free Fire is running inside BlueStacks"),
    ("base_address",     "Game not detected — open Free Fire and wait until the lobby loads"),
    ("base addr",        "Game not detected — open Free Fire and wait until the lobby loads"),
    ("module not found", "A required game module is missing — restart Free Fire inside BlueStacks"),
    ("hook=0",           "Hooks not installed — run as Administrator and restart BlueStacks"),
    ("hook failed",      "Hook injection failed — restart BlueStacks as Administrator"),
    ("hooks not",        "Memory hooks not active — run as Administrator and restart BlueStacks"),
    ("adb not connect",  "ADB not connected — enable USB Debugging in BlueStacks settings"),
    ("adb=0",            "ADB is offline — enable ADB in BlueStacks ▸ Settings ▸ Advanced"),
    ("entities=0",       "No players found — get into a match before activating ESP"),
    ("access denied",    "Permission denied — right-click and choose 'Run as Administrator'"),
    ("timeout",          "Connection timed out — check BlueStacks is running"),
    ("pipe broken",      "Lost connection to the DLL — reconnecting…"),
]

def _translate(raw):
    low = raw.lower()
    for kw, msg in _FRIENDLY:
        if kw.lower() in low:
            return msg
    return raw


# ─── Setup states ─────────────────────────────────────────────────────────────
_S_IDLE     = "idle"
_S_STARTING = "starting"
_S_STEP1    = "step1"
_S_STEP2    = "step2"
_S_STEP3    = "step3"
_S_DONE     = "complete"
_S_FAILED   = "failed"
_STATE_STEP = {_S_STARTING: 1, _S_STEP1: 1, _S_STEP2: 2, _S_STEP3: 3}


# ─── Pipe worker thread ───────────────────────────────────────────────────────
class PipeWorker(QThread):
    status_changed = pyqtSignal(str)
    line_received  = pyqtSignal(str)
    RECONNECT_DELAY = 3.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self._q    = queue.Queue()
        self._stop = threading.Event()
        self.connected = False

    def enqueue(self, cmd):
        self._q.put(cmd)

    def request_stop(self):
        self._stop.set()

    def run(self):
        acc = ""
        while not self._stop.is_set():
            self.status_changed.emit("connecting")
            h = None
            while not self._stop.is_set() and h is None:
                h = _open_pipe()
                if h is None:
                    time.sleep(self.RECONNECT_DELAY)
            if h is None:
                break
            self.connected = True
            self.status_changed.emit("connected")
            acc = ""
            while not self._stop.is_set():
                try:
                    while True:
                        cmd = self._q.get_nowait()
                        if not _write_pipe(h, cmd):
                            raise BrokenPipeError
                except queue.Empty:
                    pass
                except (BrokenPipeError, OSError):
                    break
                ok, avail = _peek_pipe(h)
                if not ok:
                    break
                if avail:
                    chunk = _read_chunk(h, min(avail + 1, 4096))
                    if chunk is None:
                        break
                    try:
                        acc += chunk.decode("utf-8", errors="replace")
                    except Exception:
                        pass
                    while "\n" in acc:
                        line, acc = acc.split("\n", 1)
                        line = line.strip()
                        if line:
                            self.line_received.emit(line)
                else:
                    time.sleep(0.02)
            self.connected = False
            _close_pipe(h)
            self.status_changed.emit("disconnected")
            if not self._stop.is_set():
                time.sleep(self.RECONNECT_DELAY)


# ─── DLL injector thread ──────────────────────────────────────────────────────
class InjectorThread(QThread):
    finished = pyqtSignal(bool)
    status   = pyqtSignal(str, str)

    def __init__(self, url, parent=None):
        super().__init__(parent)
        self._url = url

    def run(self):
        # Step B — DLL: use cache or download fresh
        path, dl_err, from_cache = _get_or_download_dll(self._url)
        if not path:
            self.status.emit(f"✗ DLL unavailable: {dl_err}", "err")
            self.finished.emit(False)
            return

        # Step C — inject

        ok, reason = _inject_dll(path)
        if not ok:
            self.status.emit(f"✗ Injection failed: {reason}", "err")
        self.finished.emit(ok)


# ─── Panel controller ─────────────────────────────────────────────────────────
class PanelController(QObject):
    pipe_status   = pyqtSignal(str)
    adb_updated   = pyqtSignal(bool, bool)
    log_appended  = pyqtSignal(str, str)
    setup_state   = pyqtSignal(str)
    step_status   = pyqtSignal(int, str, str)
    setup_message = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker        = None
        self._state         = _S_IDLE
        self._injector      = None
        self._pending_ping  = False
        self._ping_timer    = None

        self._timeout = QTimer(self)
        self._timeout.setSingleShot(True)
        self._timeout.timeout.connect(self._on_timeout)

        self._poll = QTimer(self)
        self._poll.setInterval(3000)
        self._poll.timeout.connect(self._auto_poll)
        self._poll.start()

        self._start_worker()

    @pyqtSlot(str)
    def send(self, cmd, log_sent=False):
        if self._worker and self._worker.connected:
            self._worker.enqueue(cmd)
            if log_sent and cmd != "adb_status":
                self.log_appended.emit(f"▶ {cmd}", "cmd")
        else:
            self.log_appended.emit("Start emulator first", "warn")


    @pyqtSlot(str)
    def send_feature(self, cmd):
        if self._worker and self._worker.connected:
            self._worker.enqueue(cmd)
        else:
            self.log_appended.emit("Start emulator first", "warn")


    @pyqtSlot()
    def start_setup(self):
        # ── Guard: emulator must be running ───────────────────
        if not _is_emulator_running():
            self.log_appended.emit("Start BlueStacks first", "warn")
            return

        # ── Guard: reject duplicate starts ────────────────────
        if self._state in (_S_STARTING, _S_STEP1, _S_STEP2, _S_STEP3):
            self.log_appended.emit("⚠ Setup already in progress — please wait", "warn")
            return

        self._set_state(_S_STARTING)

        if self._worker and self._worker.connected:
            # Pipe is open — ping the DLL to check it is still healthy

            self._pending_ping = True
            self._worker.enqueue("ping")
            self._ping_timer = QTimer(self)
            self._ping_timer.setSingleShot(True)
            self._ping_timer.timeout.connect(self._on_ping_timeout)
            self._ping_timer.start(1500)
        else:
            # No pipe — full injection flow
            self._start_inject_flow()

    def _on_ping_timeout(self):
        """Called when no pong arrives within 1.5 s — DLL is stale, re-inject."""
        if not self._pending_ping:
            return
        self._pending_ping = False
        self.log_appended.emit("⚠ DLL health check timed out — proceeding with injection", "warn")
        self._start_inject_flow()

    def _start_inject_flow(self):
        """Kill ADB → get/download DLL → inject."""
        self._injector = InjectorThread(DLL_URL, self)
        self._injector.status.connect(self.log_appended)
        self._injector.finished.connect(self._on_inject_done)
        self._injector.start()

    def _on_inject_done(self, ok):
        if not ok:
            self._set_state(_S_FAILED)
            return
        QTimer.singleShot(2000, self._start_inject_poll)

    def _start_inject_poll(self):
        self._inject_poll_count = 0
        self._inject_poll = QTimer(self)
        self._inject_poll.setInterval(150)
        self._inject_poll.timeout.connect(self._inject_connect_poll)
        self._inject_poll.start()

    def _inject_connect_poll(self):
        self._inject_poll_count += 1
        if self._worker and self._worker.connected:
            self._inject_poll.stop()
            QTimer.singleShot(100, self._do_start)
            return
        if self._inject_poll_count > 200:
            self._inject_poll.stop()
            self.log_appended.emit("✗ Pipe timeout — DLL loaded but pipe never opened.", "err")
            self._set_state(_S_FAILED)

    def _do_start(self):
        if not (self._worker and self._worker.connected):
            self._set_state(_S_FAILED)
            return
        for s in (1, 2, 3):
            self.step_status.emit(s, "pending", "Waiting…")
        self._set_state(_S_STARTING)
        self.step_status.emit(1, "running", "Connecting ADB and verifying memory hooks…")
        self.setup_message.emit("Command sent — waiting for DLL response…")
        self._worker.enqueue("start")
        self._timeout.start(45_000)

    @pyqtSlot()
    def reset_esp(self):
        self.send_feature("reset_esp")

    def _start_worker(self):
        w = PipeWorker(self)
        w.status_changed.connect(self._on_status)
        w.line_received.connect(self._process_line)
        w.start()
        self._worker = w

    def _set_state(self, s):
        self._state = s
        self.setup_state.emit(s)

    def _auto_poll(self):
        if self._worker and self._worker.connected:
            self._worker.enqueue("adb_status")

    def _on_timeout(self):
        if self._state not in (_S_STARTING, _S_STEP1, _S_STEP2, _S_STEP3):
            return
        if not _is_emulator_running():
            self.log_appended.emit("Start emulator first", "warn")
        self._set_state(_S_FAILED)

    def _on_status(self, state):
        self.pipe_status.emit(state)
        if state == "disconnected":
            if self._state in (_S_STARTING, _S_STEP1, _S_STEP2, _S_STEP3):
                # Setup was running — mark as failed
                self._timeout.stop()
                self.log_appended.emit("✗ Pipe disconnected — setup interrupted", "err")
                self._set_state(_S_FAILED)
            elif self._state == _S_DONE:
                # HD-Player.exe closed after a successful run — reset cleanly
                self.log_appended.emit("⚠ Emulator disconnected", "warn")
                self._set_state(_S_IDLE)

    def _process_line(self, raw):
        if raw.lower().startswith("command received"):
            self._set_state(_S_STEP1)
            self.step_status.emit(1, "running", "Connecting ADB and verifying memory hooks…")
            self.setup_message.emit("DLL is running setup — please wait…")
            self.log_appended.emit(f"● {raw}", "pipe")
            return
        if raw.startswith("[STEP ") and "] passed" in raw:
            self._timeout.stop()
            try:
                step = int(raw[6])
            except (ValueError, IndexError):
                step = 0
            if step in (1, 2, 3):
                msgs = {
                    1: "ADB connected and memory hooks verified ✓",
                    2: "Game engine found and memory read working ✓",
                    3: "All features active and ready to use ✓",
                }
                self.step_status.emit(step, "passed", msgs[step])
                self.log_appended.emit(f"[STEP {step}] ✓ Passed", "ok")
                if step < 3:
                    nxt = step + 1
                    nxt_msgs = {2: "Checking game engine and memory…", 3: "Activating features…"}
                    self.step_status.emit(nxt, "running", nxt_msgs[nxt])
                    self._timeout.start(45_000)
                    self._set_state({1: _S_STEP2, 2: _S_STEP3}[step])
                else:
                    self.setup_message.emit("✓ Setup complete — all 3 steps passed!")
                    self.log_appended.emit("[SETUP] ✓ Complete — use the Aimbot, ESP and Brutal tabs", "ok")
                    self._set_state(_S_DONE)
            return
        if raw.startswith("[STEP ") and "] failed:" in raw:
            self._timeout.stop()
            try:
                step   = int(raw[6])
                reason = raw.split("] failed:", 1)[1].strip()
            except (ValueError, IndexError):
                step   = _STATE_STEP.get(self._state, 1)
                reason = raw
            reason = _translate(reason)
            self.step_status.emit(step, "failed", reason)
            self.setup_message.emit(f"Step {step} failed — {reason}")
            self.log_appended.emit(f"[STEP {step}] ✗ Failed: {reason}", "err")
            self._set_state(_S_FAILED)
            return
        if raw.startswith("adb_status ") or raw.startswith("status "):
            self.adb_updated.emit("hook=1" in raw, "adb=1" in raw)
            return
        if ": ON" in raw or ": OFF" in raw:
            tag = "ok" if ": ON" in raw else "ctrl"
            self.log_appended.emit(f"● {raw}", tag)
            return
        if raw.startswith("err "):
            self.log_appended.emit(f"✗ {_translate(raw[4:])}", "err")
            return
        if raw.strip() in ("pong", "ok"):
            if self._pending_ping:
                # DLL responded — healthy, skip injection entirely
                self._pending_ping = False
                if self._ping_timer:
                    self._ping_timer.stop()

                QTimer.singleShot(0, self._do_start)
            return
        if raw.strip() == "bye":

            return
        tag = "rx"
        lo  = raw.lower()
        if "✓" in raw or "passed" in lo or "ready" in lo or "complete" in lo:
            tag = "ok"
        elif "✗" in raw or "failed" in lo or "error" in lo:
            tag = "err"
        elif "[adb]"  in lo: tag = "adb"
        elif "[dll]"  in lo: tag = "dll"
        elif "[pipe]" in lo: tag = "pipe"
        elif "[warn]" in lo: tag = "warn"
        # Unknown/debug line — suppressed


# ═══════════════════════════════════════════════════════════════════════════════
#  Reusable UI widgets
# ═══════════════════════════════════════════════════════════════════════════════

def _font(size=9, bold=False, family=MONO):
    f = QFont(family, size)
    f.setBold(bold)
    return f

def _qss_combo():
    return f"""
    QComboBox {{
        background: {C_BG}; color: {C_CYAN}; border: 1px solid {C_CYAN_DK};
        padding: 2px 6px; font-family: {MONO}; font-size: 9pt; min-width: 80px;
    }}
    QComboBox::drop-down {{ border: none; width: 18px; }}
    QComboBox::down-arrow {{
        width: 8px; height: 8px;
        border-left: 4px solid transparent; border-right: 4px solid transparent;
        border-top: 6px solid {C_CYAN};
    }}
    QComboBox QAbstractItemView {{
        background: {C_BG2}; color: {C_CYAN}; border: 1px solid {C_CYAN_DK};
        selection-background-color: {C_CYAN_DK};
        font-family: {MONO}; font-size: 9pt;
    }}
    """

def _qss_scroll():
    return f"""
    QScrollArea {{ border: none; background: transparent; }}
    QScrollBar:vertical {{ background: {C_BG}; width: 6px; border: none; }}
    QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 3px; min-height: 20px; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    """

def _scrollable(inner_widget):
    sa = QScrollArea()
    sa.setWidgetResizable(True)
    sa.setWidget(inner_widget)
    sa.setStyleSheet(_qss_scroll())
    sa.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    return sa


class CyanButton(QPushButton):
    def __init__(self, text, active=False, parent=None):
        super().__init__(text, parent)
        self._active = active
        self.setFont(_font(9, True))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setFixedHeight(28)
        self.setMinimumWidth(46)
        self._refresh()

    def set_active(self, v):
        self._active = v
        self._refresh()

    def _refresh(self):
        if self._active:
            self.setStyleSheet(f"""
                QPushButton {{ background: {C_CYAN_BTN}; color: #fff;
                    border: 1px solid {C_CYAN}; padding: 0 10px;
                    font-family: {MONO}; font-size: 9pt; font-weight: bold; }}
                QPushButton:hover {{ background: {C_CYAN}; color: #000; }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{ background: {C_BTN_OFF}; color: {C_CYAN};
                    border: 1px solid {C_CYAN_DK}; padding: 0 10px;
                    font-family: {MONO}; font-size: 9pt; }}
                QPushButton:hover {{ background: #112030; border-color: {C_CYAN}; }}
            """)


class OnOffWidget(QWidget):
    def __init__(self, on_cmd, off_cmd, ctrl, parent=None):
        super().__init__(parent)
        self._on_cmd  = on_cmd
        self._off_cmd = off_cmd
        self._ctrl    = ctrl
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(4)
        self._btn_on  = CyanButton("On",  active=False)
        self._btn_off = CyanButton("Off", active=False)
        lay.addWidget(self._btn_on)
        lay.addWidget(self._btn_off)
        self._btn_on.clicked.connect(self._on_click)
        self._btn_off.clicked.connect(self._off_click)

    def _on_click(self):
        self._ctrl.send_feature(self._on_cmd)
        self._btn_on.set_active(True)
        self._btn_off.set_active(False)

    def _off_click(self):
        self._ctrl.send_feature(self._off_cmd)
        self._btn_on.set_active(False)
        self._btn_off.set_active(True)


class FeatureRow(QWidget):
    def __init__(self, label, on_cmd, off_cmd, ctrl, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self.setStyleSheet("background: transparent;")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)

        bar = QFrame()
        bar.setFixedSize(3, 28)
        bar.setStyleSheet(f"background: {C_BORDER};")
        lay.addWidget(bar)
        lay.addSpacing(10)

        lbl = QLabel(label)
        lbl.setFont(_font(9))
        lbl.setStyleSheet(f"color: {C_TEXT2};")
        lay.addWidget(lbl)
        lay.addStretch()

        lay.addWidget(OnOffWidget(on_cmd, off_cmd, ctrl))


class DropdownRow(QWidget):
    def __init__(self, label, cmd_prefix, values, default_val, ctrl, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._cmd_prefix = cmd_prefix
        self._ctrl = ctrl
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(10)

        lbl = QLabel(label)
        lbl.setFont(_font(9))
        lbl.setStyleSheet(f"color: {C_TEXT2};")
        lay.addWidget(lbl)
        lay.addStretch()

        self._combo = QComboBox()
        self._combo.setFont(_font(9))
        self._combo.setStyleSheet(_qss_combo())
        for v in values:
            self._combo.addItem(str(v))
        idx = self._combo.findText(str(default_val))
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        lay.addWidget(self._combo)
        self._combo.currentTextChanged.connect(lambda val: ctrl.send_feature(f"{cmd_prefix}:{val}"))


class BoneSelector(QWidget):
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self.setFixedHeight(36)
        self._ctrl = ctrl
        self._sel  = 0
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(6)

        lbl = QLabel("Aim Bone")
        lbl.setFont(_font(9))
        lbl.setStyleSheet(f"color: {C_TEXT2};")
        lay.addWidget(lbl)
        lay.addSpacing(10)

        self._btns = []
        for i, name in enumerate(["Head", "Neck", "Hip"]):
            b = QPushButton(name)
            b.setFont(_font(9))
            b.setFixedHeight(26)
            b.setCursor(QCursor(Qt.PointingHandCursor))
            b.setProperty("boneIdx", i)
            b.clicked.connect(self._clicked)
            self._btns.append(b)
            lay.addWidget(b)
        lay.addStretch()
        self._refresh()

    def _clicked(self):
        idx = self.sender().property("boneIdx")
        self._sel = idx
        self._ctrl.send_feature(f"aimtarget:{idx}")
        self._refresh()

    def _refresh(self):
        for i, b in enumerate(self._btns):
            if i == self._sel:
                b.setStyleSheet(f"""
                    QPushButton {{ background: {C_CYAN_BTN}; color: #fff;
                        border: 1px solid {C_CYAN}; padding: 0 12px;
                        font-family: {MONO}; font-size: 9pt; font-weight: bold; }}
                """)
            else:
                b.setStyleSheet(f"""
                    QPushButton {{ background: {C_BTN_OFF}; color: {C_CYAN};
                        border: 1px solid {C_CYAN_DK}; padding: 0 12px;
                        font-family: {MONO}; font-size: 9pt; }}
                    QPushButton:hover {{ background: #112030; border-color: {C_CYAN}; }}
                """)


class ColorPickerRow(QWidget):
    """A feature row with a colour-swatch button that opens QColorDialog.

    Sends:  color:<target>:<R>:<G>:<B>
    """
    def __init__(self, label, target, default_rgb, ctrl, parent=None):
        super().__init__(parent)
        self._target = target
        self._ctrl   = ctrl
        self._color  = QColor(*default_rgb)
        self.setFixedHeight(36)
        self.setStyleSheet("background: transparent;")

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)

        bar = QFrame()
        bar.setFixedSize(3, 28)
        bar.setStyleSheet(f"background: {C_BORDER};")
        lay.addWidget(bar)
        lay.addSpacing(10)

        lbl = QLabel(label)
        lbl.setFont(_font(9))
        lbl.setStyleSheet(f"color: {C_TEXT2};")
        lay.addWidget(lbl)
        lay.addStretch()

        self._swatch = QPushButton()
        self._swatch.setFixedSize(56, 22)
        self._swatch.setCursor(QCursor(Qt.PointingHandCursor))
        self._swatch.setToolTip("Click to pick colour")
        self._swatch.clicked.connect(self._pick)
        lay.addWidget(self._swatch)
        self._refresh_swatch()

    def _refresh_swatch(self):
        c = self._color.name()
        self._swatch.setStyleSheet(
            f"QPushButton {{ background: {c}; border: 1px solid {C_CYAN_DK}; border-radius: 3px; }}"
            f"QPushButton:hover {{ border: 1px solid {C_CYAN}; }}"
        )

    def _pick(self):
        chosen = QColorDialog.getColor(self._color, self, f"Pick colour — {self._target}",
                                        QColorDialog.ShowAlphaChannel)
        if not chosen.isValid():
            return
        self._color = chosen
        self._refresh_swatch()
        r, g, b = chosen.red(), chosen.green(), chosen.blue()
        self._ctrl.send_feature(f"color:{self._target}:{r}:{g}:{b}")



class SectionHeader(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setFixedHeight(26)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 0, 14, 0)
        lay.setSpacing(6)

        bar = QFrame()
        bar.setFixedSize(3, 10)
        bar.setStyleSheet(f"background: {C_CYAN};")
        lay.addWidget(bar)

        lbl = QLabel(title)
        lbl.setFont(_font(7, True))
        lbl.setStyleSheet(f"color: {C_TEXT2}; letter-spacing: 2px;")
        lay.addWidget(lbl)
        lay.addStretch()


class StepCard(QWidget):
    STATUS_COLORS = {
        "pending": (C_BORDER,   C_BORDER, C_TEXT2),
        "running": (C_STEP_RUN, C_CYAN,   C_CYAN),
        "passed":  (C_STEP_OK,  C_GREEN,  C_GREEN),
        "failed":  (C_STEP_FAIL, C_PINK,  C_PINK),
    }
    ICONS = {"pending": " ", "running": "◌", "passed": "✓", "failed": "✗"}

    def __init__(self, step_num, title, parent=None):
        super().__init__(parent)
        self._status = "pending"
        self.setFixedHeight(80)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(14)

        self._bar = QFrame()
        self._bar.setFixedWidth(4)
        lay.addWidget(self._bar)

        self._icon_lbl = QLabel()
        self._icon_lbl.setFont(_font(14, True))
        self._icon_lbl.setAlignment(Qt.AlignCenter)
        self._icon_lbl.setFixedSize(42, 42)
        lay.addWidget(self._icon_lbl)

        txt_col = QVBoxLayout()
        txt_col.setSpacing(4)
        self._title_lbl = QLabel(f"STEP {step_num} — {title}")
        self._title_lbl.setFont(_font(10, True))
        txt_col.addWidget(self._title_lbl)
        self._detail_lbl = QLabel("Waiting to start…")
        self._detail_lbl.setFont(_font(8))
        self._detail_lbl.setStyleSheet(f"color: {C_TEXT2};")
        self._detail_lbl.setWordWrap(True)
        txt_col.addWidget(self._detail_lbl)
        lay.addLayout(txt_col, stretch=1)
        self._apply_status()

    def set_status(self, status, message):
        self._status = status
        self._detail_lbl.setText(message)
        self._apply_status()

    def _apply_status(self):
        bg, border, text_c = self.STATUS_COLORS.get(self._status, self.STATUS_COLORS["pending"])
        icon = self.ICONS.get(self._status, " ")
        self.setStyleSheet(f"StepCard {{ background: {bg}; border: 1px solid {border}; }}")
        self._bar.setStyleSheet(f"background: {border};")
        self._icon_lbl.setText(icon)
        self._icon_lbl.setStyleSheet(
            f"border: 2px solid {border}; color: {text_c}; "
            f"font-family: {MONO}; font-size: 14pt; font-weight: bold;")
        self._title_lbl.setStyleSheet(f"color: {text_c};")


class NestedTabBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(_font(9, True))
        self.setCheckable(True)
        self.setFixedHeight(36)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_TEXT2};
                border: none; border-bottom: 2px solid transparent;
                padding: 0 12px; font-family: {MONO}; font-size: 9pt;
                font-weight: bold; letter-spacing: 1px;
            }}
            QPushButton:hover {{ background: rgba(0,212,255,0.10); color: {C_TEXT}; }}
            QPushButton:checked {{
                background: transparent; color: {C_CYAN};
                border-bottom: 2px solid {C_CYAN};
            }}
        """)


class SidebarBtn(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFont(_font(9, True))
        self.setCheckable(True)
        self.setFixedHeight(46)
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(f"""
            QPushButton {{
                background: transparent; color: {C_TEXT2};
                border: none; border-left: 3px solid transparent;
                text-align: center; padding: 0px;
                font-family: {MONO}; font-size: 9pt; font-weight: bold; letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,212,255,0.07); color: {C_TEXT}; }}
            QPushButton:checked {{
                background: rgba(0,212,255,0.10); color: {C_CYAN};
                border-left: 3px solid {C_CYAN};
            }}
        """)


class LogWidget(QTextEdit):
    TAG_COLORS = {
        "ok":      "#00e676",
        "err":     "#ff2d78",
        "warn":    "#ffaa00",
        "cmd":     "#00d4ff",
        "pipe":    "#7b2fff",
        "rx":      "#9a9aca",
        "ctrl":    "#ff9800",
        "adb":     "#00bcd4",
        "dll":     "#b39ddb",
        "default": "#9a9aca",
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(_font(8, family=MONO))
        self.setStyleSheet(f"""
            QTextEdit {{
                background: {C_BG}; color: {C_TEXT2};
                border: none; padding: 6px;
                font-family: {MONO}; font-size: 8pt;
            }}
            QScrollBar:vertical {{ background: {C_BG}; width: 5px; border: none; }}
            QScrollBar::handle:vertical {{ background: {C_BORDER}; border-radius: 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self.document().setMaximumBlockCount(400)

    @pyqtSlot(str, str)
    def append_line(self, text, tag):
        color = self.TAG_COLORS.get(tag, self.TAG_COLORS["default"])
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.End)
        if not self.document().isEmpty():
            cursor.insertText("\n", QTextCharFormat())
        cursor.insertText(text, fmt)
        self.ensureCursorVisible()


# ═══════════════════════════════════════════════════════════════════════════════
#  Tab content pages
# ═══════════════════════════════════════════════════════════════════════════════

class EmptyTab(QWidget):
    def __init__(self, label, parent=None):
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG2};")
        lay = QVBoxLayout(inner)
        lay.addStretch()
        lbl = QLabel(label)
        lbl.setFont(_font(14, True))
        lbl.setStyleSheet(f"color: {C_TEXT2};")
        lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(lbl)
        sub = QLabel("Coming soon")
        sub.setFont(_font(8))
        sub.setStyleSheet(f"color: {C_BORDER};")
        sub.setAlignment(Qt.AlignCenter)
        lay.addWidget(sub)
        lay.addStretch()
        outer.addWidget(_scrollable(inner))


class HomeTab(QWidget):
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self._ctrl = ctrl
        self._start_btn = None
        self._step_cards = {}
        self._msg_lbl    = None
        self._setup()

    def _setup(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG2};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(30, 16, 30, 20)
        lay.setSpacing(14)

        # Step cards
        for num, title in [
            (1, "ADB Connection & Memory Hooks"),
            (2, "Game Engine Detection"),
            (3, "Feature Activation"),
        ]:
            card = StepCard(num, title)
            self._step_cards[num] = card
            lay.addWidget(card)

        # Status message
        self._msg_lbl = QLabel("")
        self._msg_lbl.setFont(_font(8))
        self._msg_lbl.setStyleSheet(f"color: {C_TEXT2};")
        self._msg_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self._msg_lbl)

        lay.addStretch()

        # Buttons
        self._start_btn = QPushButton("▶  START SETUP")
        self._start_btn.setFont(_font(11, True))
        self._start_btn.setFixedHeight(52)
        self._start_btn.setCursor(QCursor(Qt.PointingHandCursor))
        self._start_btn.setStyleSheet(self._btn_style(C_CYAN))
        self._start_btn.clicked.connect(self._ctrl.start_setup)
        lay.addWidget(self._start_btn)

        reset_btn = QPushButton("RESET ESP")
        reset_btn.setFont(_font(9, True))
        reset_btn.setFixedHeight(38)
        reset_btn.setCursor(QCursor(Qt.PointingHandCursor))
        reset_btn.setStyleSheet(self._btn_style(C_CYAN, small=True))
        reset_btn.clicked.connect(self._ctrl.reset_esp)
        lay.addWidget(reset_btn)

        outer.addWidget(_scrollable(inner))

    def _btn_style(self, hue, small=False):
        sz = 9 if small else 11
        return f"""
            QPushButton {{
                background: transparent; color: {hue};
                border: 1px solid {hue}; font-family: {MONO};
                font-size: {sz}pt; font-weight: bold; letter-spacing: 2px;
            }}
            QPushButton:hover {{ background: rgba(0,212,255,0.10); }}
            QPushButton:pressed {{ background: rgba(0,212,255,0.20); }}
        """

    @pyqtSlot(int, str, str)
    def on_step_status(self, step, status, message):
        card = self._step_cards.get(step)
        if card:
            card.set_status(status, message)

    @pyqtSlot(str)
    def on_setup_message(self, msg):
        if self._msg_lbl:
            self._msg_lbl.setText(msg)

    @pyqtSlot(str)
    def on_setup_state(self, state):
        if self._start_btn is None:
            return
        if state == _S_DONE:
            self._start_btn.setText("✓  SETUP COMPLETE — RESTART?")
            self._start_btn.setStyleSheet(self._btn_style(C_GREEN))
        elif state in (_S_STARTING, _S_STEP1, _S_STEP2, _S_STEP3):
            self._start_btn.setText("● SETUP RUNNING…")
            self._start_btn.setStyleSheet(self._btn_style(C_GOLD))
        else:
            self._start_btn.setText("▶  START SETUP")
            self._start_btn.setStyleSheet(self._btn_style(C_CYAN))


class AimbotTab(QWidget):
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG2};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 4, 0, 16)
        lay.setSpacing(1)

        fov_vals = list(range(100, 1050, 50))
        lay.addWidget(SectionHeader("TARGETING"))
        lay.addWidget(FeatureRow("Aimbot Visible", "aimvisible:on", "aimvisible:off", ctrl))
        lay.addWidget(FeatureRow("Silent Aim",     "silentaim:on",  "silentaim:off",  ctrl))
        lay.addWidget(FeatureRow("Rage Mode",      "aimbot:on",     "aimbot:off",     ctrl))
        lay.addWidget(FeatureRow("Ignore Knocked", "ignorekd:on",   "ignorekd:off",   ctrl))

        lay.addWidget(SectionHeader("TARGET BONE"))
        lay.addWidget(BoneSelector(ctrl))

        lay.addWidget(SectionHeader("FOV & DISTANCE"))
        lay.addWidget(FeatureRow("Show FOV Circle", "fov:on", "fov:off", ctrl))
        lay.addWidget(DropdownRow("FOV Radius",
                                  "aimfov", fov_vals, 300, ctrl))
        lay.addWidget(DropdownRow("Aim Max Distance (m)",
                                  "aimdist",
                                  [20, 50, 100, 150, 200, 250, 300, 400, 500, 600],
                                  200, ctrl))

        lay.addWidget(SectionHeader("AIM SAFE  (chest → head pattern)"))
        lay.addWidget(FeatureRow("Aim Safe",
                                  "aimsafe:on", "aimsafe:off", ctrl))
        lay.addWidget(DropdownRow("Chest Shots Before Head",
                                  "safechest",
                                  [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
                                  3, ctrl))
        lay.addStretch()

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(_scrollable(inner))


class EspTab(QWidget):
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG2};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 4, 0, 16)
        lay.setSpacing(1)

        lay.addWidget(SectionHeader("PLAYER ESP"))
        lay.addWidget(FeatureRow("Box ESP",     "box:on",    "box:off",    ctrl))
        lay.addWidget(FeatureRow("Name ESP",    "name:on",   "name:off",   ctrl))
        lay.addWidget(FeatureRow("Health Bar",  "health:on", "health:off", ctrl))
        lay.addWidget(FeatureRow("Skeleton",    "skel:on",   "skel:off",   ctrl))
        lay.addWidget(FeatureRow("Weapon Name", "weapon:on", "weapon:off", ctrl))

        lay.addWidget(SectionHeader("TRACKING"))
        lay.addWidget(FeatureRow("ESP Lines",   "lines:on",  "lines:off",  ctrl))

        lay.addWidget(SectionHeader("ESP COLOURS"))
        lay.addWidget(ColorPickerRow("Box Colour",         "box",       (255, 165,   0), ctrl))
        lay.addWidget(ColorPickerRow("Skeleton Colour",    "skel",      (  0, 220, 255), ctrl))
        lay.addWidget(ColorPickerRow("Lines Colour",       "lines",     (  0, 255,   0), ctrl))
        lay.addWidget(ColorPickerRow("Knocked Colour",     "knocked",   (255, 255,   0), ctrl))
        lay.addWidget(ColorPickerRow("Name Label Colour",  "name",      (255, 255, 255), ctrl))
        lay.addWidget(ColorPickerRow("Distance Colour",    "distance",  (180, 150, 255), ctrl))
        lay.addWidget(ColorPickerRow("Health High",        "health_hi", (  0, 230,   0), ctrl))
        lay.addWidget(ColorPickerRow("Health Low",         "health_lo", (255,  50,  50), ctrl))
        lay.addWidget(ColorPickerRow("FOV Circle Colour",  "fov",       (  0, 212, 255), ctrl))

        lay.addWidget(SectionHeader("DISTANCE & SIZE"))
        lay.addWidget(DropdownRow("Max Entity Distance (m)",
                                  "maxdist",
                                  [100, 200, 300, 500, 800, 1000, 2000, 5000, 9999],
                                  9999, ctrl))
        lay.addWidget(DropdownRow("Skeleton Width",
                                  "skelthick",
                                  [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0],
                                  1.5, ctrl))
        lay.addStretch()

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(_scrollable(inner))


class BrutalTab(QWidget):
    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG2};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(0, 4, 0, 16)
        lay.setSpacing(1)

        lay.addWidget(SectionHeader("COMBAT"))
        lay.addWidget(FeatureRow("No Recoil",   "norecoil:on",  "norecoil:off",  ctrl))
        lay.addWidget(FeatureRow("No Spread",   "nospread:on",  "nospread:off",  ctrl))
        lay.addWidget(FeatureRow("Rapid Fire",  "rapidfire:on", "rapidfire:off", ctrl))
        lay.addWidget(FeatureRow("Auto Reload", "autoreload:on","autoreload:off", ctrl))

        lay.addWidget(SectionHeader("MOVEMENT"))
        lay.addWidget(FeatureRow("Speed Hack",  "speed:on",     "speed:off",     ctrl))
        lay.addWidget(FeatureRow("No Clip",     "noclip:on",    "noclip:off",    ctrl))
        lay.addStretch()

        vlay = QVBoxLayout(self)
        vlay.setContentsMargins(0, 0, 0, 0)
        vlay.addWidget(_scrollable(inner))


class ExternalTab(QWidget):
    """External tab: nested sub-tabs — Home / Aimbot / ESP / Brutal / Settings."""

    def __init__(self, ctrl, parent=None):
        super().__init__(parent)
        self._ctrl = ctrl

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Nested tab bar
        tabs_bar = QWidget()
        tabs_bar.setFixedHeight(36)
        tabs_bar.setStyleSheet(f"background: {C_BG2};")
        tabs_lay = QHBoxLayout(tabs_bar)
        tabs_lay.setContentsMargins(0, 0, 0, 0)
        tabs_lay.setSpacing(0)

        self._nested_group = QButtonGroup(self)
        self._nested_group.setExclusive(True)
        tabs_lay.addStretch()
        for i, name in enumerate(["Home", "Aimbot", "ESP", "Brutal", "Settings"]):
            btn = NestedTabBtn(name)
            btn.setProperty("tabIdx", i)
            self._nested_group.addButton(btn, i)
            tabs_lay.addWidget(btn)
        tabs_lay.addStretch()
        outer.addWidget(tabs_bar)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C_BORDER}; border: none;")
        outer.addWidget(sep)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {C_BG2};")

        self._home_tab    = HomeTab(ctrl)
        self._aim_tab     = AimbotTab(ctrl)
        self._esp_tab     = EspTab(ctrl)
        self._brutal_tab  = BrutalTab(ctrl)
        self._settings_tab = EmptyTab("Settings")

        for tab in [self._home_tab, self._aim_tab, self._esp_tab,
                    self._brutal_tab, self._settings_tab]:
            self._stack.addWidget(tab)

        outer.addWidget(self._stack, stretch=1)
        self._nested_group.idClicked.connect(self._stack.setCurrentIndex)
        self._nested_group.button(0).setChecked(True)

    @pyqtSlot(int, str, str)
    def on_step_status(self, step, status, message):
        self._home_tab.on_step_status(step, status, message)

    @pyqtSlot(str)
    def on_setup_message(self, msg):
        self._home_tab.on_setup_message(msg)

    @pyqtSlot(str)
    def on_setup_state(self, state):
        self._home_tab.on_setup_state(state)


# ═══════════════════════════════════════════════════════════════════════════════
#  Dashboard page
# ═══════════════════════════════════════════════════════════════════════════════

class DashboardPage(QWidget):
    def __init__(self, user_data, ctrl, pipe_dot_ref, parent=None):
        super().__init__(parent)
        self._ctrl = ctrl
        self._pipe_dot = pipe_dot_ref
        self.setStyleSheet(f"background: {C_BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 28)
        lay.setSpacing(16)

        username = (user_data.username or "Guest") if user_data else "Guest"
        welcome = QLabel(f"Welcome back, {username}.")
        welcome.setFont(_font(12, bold=True, family="Segoe UI"))
        welcome.setStyleSheet(f"color: {C_TEXT}; background: transparent;")
        lay.addWidget(welcome)

        cards_row = QHBoxLayout()
        cards_row.setSpacing(14)
        stats = [
            ("KeyAuth Status", "● Authenticated", C_GREEN),
            ("App Version",    "1.0",              C_CYAN),
            ("Session",        "Active",           C_PURPLE),
            ("Platform",       sys.platform,       C_GOLD),
        ]
        for label, val, color in stats:
            card = QLabel(f"<b style='font-size:10pt;color:{C_TEXT2}'>{label}</b><br>"
                          f"<span style='font-size:13pt;color:{color}'>{val}</span>")
            card.setTextFormat(Qt.RichText)
            card.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            card.setStyleSheet(f"""
                background-color: {C_BG2}; border: 1px solid {C_BORDER};
                border-radius: 10px; padding: 16px 20px; min-width: 130px;
            """)
            cards_row.addWidget(card)
        cards_row.addStretch()
        lay.addLayout(cards_row)

        info = QLabel(
            f"<b style='color:{C_CYAN}'>JACK Panel</b>"
            f"<br><span style='color:{C_TEXT2}'>Pipe connects automatically when BlueStacks + DLL are running.<br>"
            f"Go to <b>External → Home</b> and click <b>START SETUP</b>.</span>"
        )
        info.setTextFormat(Qt.RichText)
        info.setWordWrap(True)
        info.setStyleSheet(f"background: {C_BG2}; border: 1px solid {C_BORDER}; border-radius: 8px; padding: 14px 18px;")
        lay.addWidget(info)
        lay.addStretch()


class SettingsPage(QWidget):
    def __init__(self, user_data, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C_BG};")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(28, 20, 28, 28)
        lay.setSpacing(18)

        username = (user_data.username or "N/A") if user_data else "N/A"
        ip       = (user_data.ip       or "N/A") if user_data else "N/A"
        raw_hwid = (user_data.hwid     or "")    if user_data else ""
        hwid     = (raw_hwid[:32] + "…") if len(raw_hwid) > 32 else (raw_hwid or "N/A")

        for label, val in [("Username", username), ("IP Address", ip), ("HWID", hwid)]:
            row = QHBoxLayout()
            k = QLabel(label)
            k.setFont(_font(9, family="Segoe UI"))
            k.setStyleSheet(f"color: {C_TEXT2}; min-width: 120px; background: transparent;")
            v = QLabel(val)
            v.setFont(_font(9, family="Segoe UI"))
            v.setStyleSheet(f"color: {C_TEXT}; background: transparent;")
            row.addWidget(k)
            row.addWidget(v)
            row.addStretch()
            lay.addLayout(row)

        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background: {C_BORDER};")
        lay.addWidget(div)

        logout_btn = QPushButton("Logout / Exit")
        logout_btn.setFont(_font(9, True))
        logout_btn.setFixedSize(160, 36)
        logout_btn.setCursor(QCursor(Qt.PointingHandCursor))
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background: {C_BG2}; color: {C_PINK};
                border: 1px solid {C_PINK}; border-radius: 6px;
                font-family: {MONO}; font-size: 9pt;
            }}
            QPushButton:hover {{ background: #2a1020; }}
        """)
        logout_btn.clicked.connect(QApplication.instance().quit)
        lay.addWidget(logout_btn)
        lay.addStretch()


# ═══════════════════════════════════════════════════════════════════════════════
#  Main window
# ═══════════════════════════════════════════════════════════════════════════════

SIDEBAR_TABS = [
    ("External",  "⚡"),
    ("Supreme",   "★"),
    ("Esp",       "👁"),
    ("Utility",   "🔧"),
    ("Brutal",    "💀"),
    ("Hockey",    "🏒"),
    ("Dashboard", "🏠"),
    ("Settings",  "⚙"),
]


class MainWindow(QWidget):
    def __init__(self, user_data=None):
        super().__init__()
        self._user_data = user_data
        self._drag_pos  = QPoint()
        self._ctrl      = PanelController(self)
        self._pipe_dot  = None
        self._sidebar_btns: dict = {}
        self._pulse     = 0.4
        self._pulse_dir = 1

        self._pulse_timer = QTimer(self)
        self._pulse_timer.setInterval(30)
        self._pulse_timer.timeout.connect(self._tick_pulse)
        self._pulse_timer.start()

        self._build_ui()
        self._ctrl.pipe_status.connect(self._on_pipe_status)

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
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setMinimumSize(1000, 660)
        self.resize(1120, 700)
        self.setStyleSheet(f"QWidget {{ background: {C_BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_title_bar())

        # Cyan separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C_CYAN}; border: none;")
        root.addWidget(sep)

        # Body — card layout with outer padding
        body = QHBoxLayout()
        body.setContentsMargins(12, 10, 12, 10)
        body.setSpacing(10)

        # ── Sidebar card ──────────────────────────────────────
        s_card = QWidget()
        s_card.setAttribute(Qt.WA_StyledBackground, True)
        s_card.setObjectName("sidebarCard")
        s_card.setStyleSheet(f"""
            QWidget#sidebarCard {{
                background: {C_SIDEBAR};
                border-radius: 12px;
                border: 1px solid {C_CYAN}44;
            }}
        """)
        s_lay = QVBoxLayout(s_card)
        s_lay.setContentsMargins(0, 0, 0, 0)
        s_lay.setSpacing(0)
        s_lay.addWidget(self._build_sidebar())

        # ── Content card ──────────────────────────────────────
        c_card = QWidget()
        c_card.setAttribute(Qt.WA_StyledBackground, True)
        c_card.setObjectName("contentCard")
        c_card.setStyleSheet(f"""
            QWidget#contentCard {{
                background: {C_BG2};
                border-radius: 12px;
                border: 1px solid {C_CYAN}44;
            }}
        """)
        c_lay = QVBoxLayout(c_card)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(0)
        c_lay.addWidget(self._build_content(), stretch=1)
        c_lay.addWidget(self._build_log_area())

        body.addWidget(s_card, stretch=23)
        body.addWidget(c_card, stretch=77)

        root.addLayout(body, stretch=1)

    def _build_title_bar(self) -> QWidget:
        bar = QWidget()
        bar.setFixedHeight(42)
        bar.setStyleSheet(f"background: #08081a;")
        lay = QHBoxLayout(bar)
        lay.setContentsMargins(14, 0, 10, 0)
        lay.setSpacing(8)

        # Logo bars
        bar_col = QWidget()
        bar_col.setStyleSheet("background: transparent;")
        bl = QVBoxLayout(bar_col)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(2)
        for h in (8, 5, 3):
            b = QFrame()
            b.setFixedSize(3, h)
            b.setStyleSheet(f"background: {C_CYAN};")
            bl.addWidget(b)
        bl.addStretch()
        lay.addWidget(bar_col)

        # Title
        title = QLabel("JACK")
        title.setFont(_font(17, True, "Segoe UI"))
        title.setStyleSheet(f"color: {C_TEXT}; letter-spacing: 4px; background: transparent;")
        sub = QLabel("CONTROL PANEL")
        sub.setFont(_font(6, family="Segoe UI"))
        sub.setStyleSheet(f"color: {C_TEXT2}; letter-spacing: 3px; background: transparent;")
        txt_col = QVBoxLayout()
        txt_col.setSpacing(0)
        txt_col.addWidget(title)
        txt_col.addWidget(sub)
        lay.addLayout(txt_col)

        lay.addStretch()

        # Connection dot
        self._pipe_dot = QLabel("●")
        self._pipe_dot.setFont(_font(12))
        self._pipe_dot.setStyleSheet(f"color: {C_TEXT2}; background: transparent;")
        lay.addWidget(self._pipe_dot)

        # Username badge
        username = (self._user_data.username or "Guest") if self._user_data else "Guest"
        user_lbl = QLabel(f"  {username}")
        user_lbl.setFont(_font(8, family="Segoe UI"))
        user_lbl.setStyleSheet(f"color: {C_GREEN}; background: transparent;")
        lay.addWidget(user_lbl)

        lay.addSpacing(12)

        # Window controls
        btn_min = QPushButton("─")
        btn_min.setFont(_font(11))
        btn_min.setFixedSize(28, 28)
        btn_min.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C_TEXT2}; border: none; }}
            QPushButton:hover {{ background: rgba(255,255,255,0.06); }}
        """)
        btn_min.setCursor(QCursor(Qt.PointingHandCursor))
        btn_min.clicked.connect(self.showMinimized)

        btn_close = QPushButton("✕")
        btn_close.setFont(_font(12))
        btn_close.setFixedSize(28, 28)
        btn_close.setStyleSheet(f"""
            QPushButton {{ background: transparent; color: {C_PINK}; border: none; }}
            QPushButton:hover {{ background: rgba(255,45,120,0.2); }}
        """)
        btn_close.setCursor(QCursor(Qt.PointingHandCursor))
        btn_close.clicked.connect(QApplication.instance().quit)

        lay.addWidget(btn_min)
        lay.addWidget(btn_close)
        return bar

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sidebar.setStyleSheet("background: transparent;")
        lay = QVBoxLayout(sidebar)
        lay.setContentsMargins(0, 6, 0, 6)
        lay.setSpacing(0)

        self._tab_group = QButtonGroup(self)
        self._tab_group.setExclusive(True)

        for i, (name, icon) in enumerate(SIDEBAR_TABS):
            btn = SidebarBtn(f"{icon}  {name}")
            btn.setProperty("tabIdx", i)
            self._tab_group.addButton(btn, i)
            self._sidebar_btns[name] = btn
            lay.addWidget(btn)

        lay.addStretch()

        # Safety badge
        safe_lbl = QLabel("Safety Status")
        safe_lbl.setFont(_font(7, family="Segoe UI"))
        safe_lbl.setStyleSheet(f"color: {C_TEXT2}; background: transparent;")
        safe_lbl.setAlignment(Qt.AlignCenter)
        safe_val = QLabel("Safe")
        safe_val.setFont(_font(9, True, "Segoe UI"))
        safe_val.setStyleSheet(f"color: {C_GREEN}; background: transparent;")
        safe_val.setAlignment(Qt.AlignCenter)
        lay.addWidget(safe_lbl)
        lay.addWidget(safe_val)
        lay.addSpacing(6)

        self._tab_group.idClicked.connect(self._on_sidebar_clicked)
        self._tab_group.button(0).setChecked(True)
        return sidebar

    def _build_content(self) -> QWidget:
        self._stack = QStackedWidget()
        self._stack.setStyleSheet(f"background: {C_BG2};")

        self._external_tab  = ExternalTab(self._ctrl)
        self._stack.addWidget(self._external_tab)                # 0 External
        self._stack.addWidget(EmptyTab("Supreme"))               # 1
        self._stack.addWidget(EmptyTab("Esp"))                   # 2
        self._stack.addWidget(EmptyTab("Utility"))               # 3
        self._stack.addWidget(EmptyTab("Brutal"))                # 4
        self._stack.addWidget(EmptyTab("Hockey"))                # 5
        self._stack.addWidget(DashboardPage(
            self._user_data, self._ctrl, self._pipe_dot))        # 6 Dashboard
        self._stack.addWidget(SettingsPage(self._user_data))     # 7 Settings

        self._ctrl.step_status.connect(self._external_tab.on_step_status)
        self._ctrl.setup_message.connect(self._external_tab.on_setup_message)
        self._ctrl.setup_state.connect(self._external_tab.on_setup_state)

        return self._stack

    def _build_log_area(self) -> QWidget:
        container = QWidget()
        container.setFixedHeight(110)
        container.setStyleSheet(f"background: {C_BG};")

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background: {C_BORDER}; border: none;")

        self._log = LogWidget()
        self._ctrl.log_appended.connect(self._log.append_line)

        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)
        lay.addWidget(sep)
        lay.addWidget(self._log)

        return container

    def _on_sidebar_clicked(self, idx: int):
        self._stack.setCurrentIndex(idx)

    @pyqtSlot(str)
    def _on_pipe_status(self, state: str):
        if self._pipe_dot is None:
            return
        colors = {"connected": C_GREEN, "connecting": C_GOLD}
        self._pipe_dot.setStyleSheet(
            f"color: {colors.get(state, C_PINK)}; background: transparent;")

    def paintEvent(self, event):
        super().paintEvent(event)
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Outer glow layers — cyan
        for i, a in enumerate([int(8 * self._pulse), int(18 * self._pulse), int(45 * self._pulse)]):
            if a <= 0:
                continue
            pad = (3 - i) * 2
            p.setPen(QPen(QColor(0, 212, 255, a), 1))
            p.drawRect(pad, pad, w - pad * 2, h - pad * 2)

        # Purple accent layer
        p.setPen(QPen(QColor(123, 47, 255, int(20 * self._pulse)), 1))
        p.drawRect(2, 2, w - 4, h - 4)

        # Solid inner border — always visible
        p.setPen(QPen(QColor(0, 212, 255, 160), 1))
        p.drawRect(1, 1, w - 2, h - 2)

        # Corner accent marks
        seg = 18
        p.setPen(QPen(QColor(0, 212, 255, int(200 * self._pulse)), 2))
        for cx, cy, dx, dy in [
            (0, 0, seg, 0), (0, 0, 0, seg),
            (w, 0, -seg, 0), (w, 0, 0, seg),
            (0, h, seg, 0), (0, h, 0, -seg),
            (w, h, -seg, 0), (w, h, 0, -seg),
        ]:
            p.drawLine(cx, cy, cx + dx, cy + dy)

        p.end()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and not self._drag_pos.isNull():
            self.move(event.globalPos() - self._drag_pos)

    def closeEvent(self, event):
        if hasattr(self._ctrl, '_worker') and self._ctrl._worker:
            self._ctrl._worker.request_stop()
            self._ctrl._worker.wait(1000)
        event.accept()
