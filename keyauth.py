"""
Lightweight KeyAuth API wrapper.
Handles init, login, register, and license-key auth.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time

try:
    import requests
except ImportError:
    os.system("pip install requests")
    import requests

KEYAUTH_URL = "https://keyauth.win/api/1.3/"


def get_hwid() -> str:
    if platform.system() == "Windows":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography"
            )
            val, _ = winreg.QueryValueEx(key, "MachineGuid")
            return val
        except Exception:
            pass
        try:
            out = subprocess.check_output(
                "wmic csproduct get uuid", shell=True
            ).decode().split("\n")[1].strip()
            return out
        except Exception:
            pass
    elif platform.system() == "Linux":
        try:
            with open("/etc/machine-id") as f:
                return f.read().strip()
        except Exception:
            pass
    elif platform.system() == "Darwin":
        try:
            out = subprocess.check_output(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"]
            ).decode()
            for line in out.split("\n"):
                if "IOPlatformUUID" in line:
                    return line.split('"')[-2]
        except Exception:
            pass
    return hashlib.md5(platform.node().encode()).hexdigest()


def get_file_checksum(path: str) -> str:
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        md5.update(f.read())
    return md5.hexdigest()


class UserData:
    def __init__(self, info: dict):
        self.username = info.get("username", "")
        self.email = info.get("email", "")
        self.ip = info.get("ip", "")
        self.hwid = info.get("hwid", "")
        self.expires = info.get("subscriptions", [{}])[0].get("expiry", "0") if info.get("subscriptions") else "0"
        self.createdate = info.get("createdate", "0")
        self.lastlogin = info.get("lastlogin", "0")
        self.subscriptions = info.get("subscriptions", [])


class AppData:
    def __init__(self, info: dict):
        self.num_keys = info.get("numKeys", "0")
        self.num_users = info.get("numUsers", "0")
        self.online_users = info.get("onlineUsers", "0")
        self.version = info.get("app_ver", "")
        self.customer_panel = info.get("customer_panel", "")


class KeyAuthError(Exception):
    pass


class KeyAuthAPI:
    def __init__(self, name: str, ownerid: str, version: str, checksum: str = ""):
        if len(ownerid) != 10:
            raise KeyAuthError("Invalid ownerid — copy Python code from keyauth.cc/app/")
        self.name = name
        self.ownerid = ownerid
        self.version = version
        self.checksum = checksum
        self.session_id = ""
        self.initialized = False
        self.user_data: UserData | None = None
        self.app_data: AppData | None = None

    def init(self) -> tuple[bool, str]:
        """Initialize session with KeyAuth. Returns (success, message)."""
        resp = self._request({
            "type": "init",
            "ver": self.version,
            "hash": self.checksum,
            "name": self.name,
            "ownerid": self.ownerid,
        })
        if resp is None:
            return False, "Could not reach KeyAuth servers"
        if resp == "KeyAuth_Invalid":
            return False, "Application does not exist on KeyAuth"
        data = json.loads(resp)
        if data.get("message") == "invalidver":
            link = data.get("download", "")
            return False, f"Outdated version. Update available: {link}" if link else "Outdated version — no download link set"
        if not data.get("success"):
            return False, data.get("message", "Init failed")
        self.session_id = data["sessionid"]
        self.initialized = True
        return True, "Initialized"

    def login(self, username: str, password: str, hwid: str = "") -> tuple[bool, str]:
        """Login with username + password. Returns (success, message)."""
        self._check_init()
        resp = self._request({
            "type": "login",
            "username": username,
            "pass": password,
            "hwid": hwid or get_hwid(),
            "sessionid": self.session_id,
            "name": self.name,
            "ownerid": self.ownerid,
        })
        data = json.loads(resp)
        if data.get("success"):
            self.user_data = UserData(data.get("info", {}))
            return True, data.get("message", "Login successful")
        return False, data.get("message", "Login failed")

    def register(self, username: str, password: str, license_key: str, hwid: str = "") -> tuple[bool, str]:
        """Register a new account. Returns (success, message)."""
        self._check_init()
        resp = self._request({
            "type": "register",
            "username": username,
            "pass": password,
            "key": license_key,
            "hwid": hwid or get_hwid(),
            "sessionid": self.session_id,
            "name": self.name,
            "ownerid": self.ownerid,
        })
        data = json.loads(resp)
        if data.get("success"):
            self.user_data = UserData(data.get("info", {}))
            return True, data.get("message", "Registration successful")
        return False, data.get("message", "Registration failed")

    def license_only(self, license_key: str, hwid: str = "") -> tuple[bool, str]:
        """Authenticate with license key only. Returns (success, message)."""
        self._check_init()
        resp = self._request({
            "type": "license",
            "key": license_key,
            "hwid": hwid or get_hwid(),
            "sessionid": self.session_id,
            "name": self.name,
            "ownerid": self.ownerid,
        })
        data = json.loads(resp)
        if data.get("success"):
            self.user_data = UserData(data.get("info", {}))
            return True, data.get("message", "License valid")
        return False, data.get("message", "Invalid license")

    def _check_init(self):
        if not self.initialized:
            raise KeyAuthError("Call init() before using other methods")

    def _request(self, payload: dict) -> str | None:
        try:
            r = requests.post(KEYAUTH_URL, data=payload, timeout=10)
            return r.text
        except Exception:
            return None
