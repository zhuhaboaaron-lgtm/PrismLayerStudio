"""Desktop-only I/O; v2.6 calculation and visual source files stay untouched."""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import json
import logging
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import threading
import time

RUNTIME_GUID = "{F3017226-FE2A-4295-8BDF-00C3A9A7E4C5}"
MIN_WEBVIEW_MAJOR = 109


def resource_directory() -> Path:
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


def app_data_directory() -> Path:
    root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local")) / "PrismLayerStudio"
    root.mkdir(parents=True, exist_ok=True)
    return root


def configure_dpi() -> None:
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    except (AttributeError, OSError):
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("PrismLayerStudio.2.6")


def show_error(message: str) -> None:
    if sys.platform == "win32":
        ctypes.windll.user32.MessageBoxW(None, message, "Prism Layer Studio 2.6.0", 0x10)


def installed_webview_version() -> str | None:
    if sys.platform != "win32":
        return None
    import winreg
    versions = []
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                key_path = "SOFTWARE\\Microsoft\\EdgeUpdate\\Clients\\" + RUNTIME_GUID
                with winreg.OpenKey(hive, key_path, 0, winreg.KEY_READ | view) as key:
                    value = winreg.QueryValueEx(key, "pv")[0]
                    parts = tuple(int(x) for x in value.split("."))
                    if len(parts) == 4 and parts[0] >= MIN_WEBVIEW_MAJOR:
                        versions.append((parts, value))
            except (OSError, ValueError, TypeError):
                pass
    return max(versions)[1] if versions else None


def ensure_webview2() -> None:
    if sys.platform != "win32":
        raise RuntimeError("此发行入口仅支持 Windows 10/11 x64。")
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                            r"SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full") as key:
            net_release = int(winreg.QueryValueEx(key, "Release")[0])
    except OSError:
        net_release = 0
    if net_release < 394802:
        raise RuntimeError("需要系统 .NET Framework 4.6.2 或更新版本。\n"
                           "Windows 10 1809 及更新版本、Windows 11 已内置所需组件，请修复系统 .NET 后重试。")
    if installed_webview_version():
        return
    folder = Path(sys.executable).parent if getattr(sys, "frozen", False) else resource_directory()
    installer = folder / "runtime" / "MicrosoftEdgeWebView2RuntimeInstallerX64.exe"
    if not installer.is_file():
        raise RuntimeError("需要 Microsoft Edge WebView2 Runtime（109 或更新版本）。\n"
                           "请运行完整离线安装包，或便携包 runtime 目录中的微软离线运行时安装器。")
    signature_script = (
        "Import-Module ($env:SystemRoot + '\\System32\\WindowsPowerShell\\v1.0\\Modules\\Microsoft.PowerShell.Security\\Microsoft.PowerShell.Security.psd1') -ErrorAction Stop; "
        "$s=Get-AuthenticodeSignature -LiteralPath $args[0]; "
        "if($s.Status -eq 'Valid' -and $s.SignerCertificate.Subject -match 'O=Microsoft Corporation')"
        "{exit 0}else{exit 1}"
    )
    with tempfile.TemporaryDirectory(prefix="PrismRuntime-") as temp:
        script = Path(temp) / "verify.ps1"
        script.write_text(signature_script, encoding="utf-8-sig")
        result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
                                 str(script), str(installer)], creationflags=subprocess.CREATE_NO_WINDOW,
                                timeout=120, capture_output=True)
    if result.returncode:
        raise RuntimeError("WebView2 离线安装器的 Microsoft 数字签名验证失败。请重新获取正式离线发行包。")
    answer = ctypes.windll.user32.MessageBoxW(None,
        "首次运行需要安装 Microsoft Edge WebView2 Runtime。\n"
        "将使用随包附带的微软离线安装器，不需要联网。是否继续？",
        "Prism Layer Studio", 0x24)
    if answer != 6:
        raise RuntimeError("已取消安装 WebView2 Runtime。")
    result = subprocess.run([str(installer), "/silent", "/install"],
                            creationflags=subprocess.CREATE_NO_WINDOW, timeout=600)
    if not installed_webview_version():
        raise RuntimeError(f"WebView2 安装未完成（退出码 {result.returncode}）。请运行离线安装程序后重试。")


_clipboard_lock = threading.Lock()


def clipboard_text(text: str | None = None) -> str:
    """Unicode Windows clipboard, independent of browser permission and COM apartment."""
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    user32.OpenClipboard.argtypes = [wintypes.HWND]
    user32.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    user32.SetClipboardData.restype = wintypes.HANDLE
    user32.GetClipboardData.argtypes = [wintypes.UINT]
    user32.GetClipboardData.restype = wintypes.HANDLE
    kernel32.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
    kernel32.GlobalLock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalLock.restype = ctypes.c_void_p
    kernel32.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    kernel32.GlobalFree.argtypes = [wintypes.HGLOBAL]
    with _clipboard_lock:
        for _ in range(20):
            if user32.OpenClipboard(None):
                break
            time.sleep(0.025)
        else:
            raise OSError("剪贴板正被其他程序占用，请重试。")
        try:
            if text is not None:
                encoded = text.encode("utf-16-le") + b"\0\0"
                handle = kernel32.GlobalAlloc(0x0002, len(encoded))
                if not handle:
                    raise MemoryError("无法为剪贴板分配内存")
                try:
                    pointer = kernel32.GlobalLock(handle)
                    if not pointer:
                        raise OSError("无法锁定剪贴板内存")
                    ctypes.memmove(pointer, encoded, len(encoded))
                    kernel32.GlobalUnlock(handle)
                    if not user32.EmptyClipboard() or not user32.SetClipboardData(13, handle):
                        raise OSError("无法写入剪贴板")
                    handle = None
                finally:
                    if handle:
                        kernel32.GlobalFree(handle)
                return text
            handle = user32.GetClipboardData(13)
            if not handle:
                return ""
            pointer = kernel32.GlobalLock(handle)
            if not pointer:
                raise OSError("无法读取剪贴板")
            try:
                return ctypes.wstring_at(pointer)
            finally:
                kernel32.GlobalUnlock(handle)
        finally:
            user32.CloseClipboard()


def write_export(path: Path, contents: str) -> None:
    descriptor, temporary = tempfile.mkstemp(prefix=".prism-", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


class DesktopAPI:
    def __init__(self, webview, version="2.6.0"):
        self._webview = webview
        self._window = None
        self._version = version
        self._smoke_report = os.environ.get("PRISM_STUDIO_SMOKE_REPORT")
        self._smoke_export_dir = os.environ.get("PRISM_STUDIO_SMOKE_EXPORT_DIR") if self._smoke_report else None
        self._exports = []
        self._save_lock = threading.Lock()

    def save_file(self, filename: str, contents: str, mime: str = "") -> dict:
        if filename not in ("prism-layer-studio-layers.csv", "prism-layer-studio-result.json"):
            return {"ok": False, "error": "不支持的导出文件名"}
        if not isinstance(contents, str) or len(contents) > 16_000_000:
            return {"ok": False, "error": "导出内容无效或过大"}
        with self._save_lock:
            try:
                if self._smoke_export_dir:
                    folder = Path(self._smoke_export_dir)
                    folder.mkdir(parents=True, exist_ok=True)
                    path = folder / filename
                else:
                    import winreg
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders") as key:
                            documents = Path(os.path.expandvars(winreg.QueryValueEx(key, "Personal")[0]))
                    except OSError:
                        documents = Path.home() / "Documents"
                    folder = documents if documents.is_dir() else Path.home()
                    extension = "csv" if filename.endswith(".csv") else "json"
                    selection = self._window.create_file_dialog(
                        self._webview.FileDialog.SAVE, directory=str(folder), save_filename=filename,
                        file_types=(f"{extension.upper()} files (*.{extension})",))
                    if not selection:
                        return {"ok": False, "cancelled": True}
                    path = Path(selection[0] if isinstance(selection, (tuple, list)) else selection)
                    if not path.suffix:
                        path = path.with_suffix("." + extension)
                if filename.endswith(".json"):
                    payload = json.loads(contents)
                    payload["version"] = self._version
                    contents = json.dumps(payload, ensure_ascii=False, indent=2)
                write_export(path, contents)
                self._exports.append({"name": filename, "path": str(path)})
                return {"ok": True, "path": str(path)}
            except Exception as exc:
                logging.exception("Export failed")
                return {"ok": False, "error": str(exc)}

    def copy_text(self, text: str) -> dict:
        try:
            if not isinstance(text, str) or len(text) > 1_000_000:
                raise ValueError("复制内容无效")
            text = re.sub(r"^【Prism Layer Studio v[\d.]+】", f"【Prism Layer Studio v{self._version}】", text)
            clipboard_text(text)
            return {"ok": True}
        except Exception as exc:
            logging.exception("Clipboard failed")
            return {"ok": False, "error": str(exc)}

    def smoke_status(self) -> dict:
        if not self._smoke_report:
            return {"ok": False}
        return {"ok": True, "exports": list(self._exports), "clipboard": clipboard_text()}

    def smoke_set_window(self, action: str, width=1000, height=800) -> dict:
        if not self._smoke_report:
            return {"ok": False}
        if action == "resize":
            self._window.resize(int(width), int(height))
        elif action == "maximize":
            self._window.maximize()
        elif action == "minimize":
            self._window.minimize()
        elif action == "restore":
            self._window.restore()
        else:
            return {"ok": False}
        return {"ok": True}

    def smoke_complete(self, report: str) -> dict:
        if not self._smoke_report:
            return {"ok": False}
        payload = json.loads(report)
        payload.update({"applicationVersion": self._version, "webviewRuntime": installed_webview_version(),
                        "frozen": bool(getattr(sys, "frozen", False)), "executable": sys.executable})
        target = Path(self._smoke_report)
        target.parent.mkdir(parents=True, exist_ok=True)
        write_export(target, json.dumps(payload, ensure_ascii=False, indent=2))
        if self._window:
            timer = threading.Timer(0.6, self._window.destroy)
            timer.daemon = True
            timer.start()
        return {"ok": True}
