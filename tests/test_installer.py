"""Explicit Windows install/uninstall test; importing this file never installs anything.

Run: .venv-build\\Scripts\\python.exe tests\\test_installer.py
Uses a new isolated Chinese installation path and refuses to replace an existing
Prism Layer Studio installation or an existing application shortcut.
"""
from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid

APP_ID = "{E79C7545-C719-45BD-BC2F-B371EEACD0F6}_is1"
UNINSTALL_KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall" + "\\" + APP_ID


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def registered_installations() -> list[dict]:
    import winreg
    entries = []
    for hive_name, hive in (("HKCU", winreg.HKEY_CURRENT_USER), ("HKLM", winreg.HKEY_LOCAL_MACHINE)):
        for view in (winreg.KEY_WOW64_32KEY, winreg.KEY_WOW64_64KEY):
            try:
                with winreg.OpenKey(hive, UNINSTALL_KEY, 0, winreg.KEY_READ | view) as key:
                    values = {}
                    for name in ("DisplayName", "DisplayVersion", "InstallLocation", "UninstallString"):
                        try:
                            values[name] = winreg.QueryValueEx(key, name)[0]
                        except OSError:
                            pass
                    entries.append({"hive": hive_name, "view": view, **values})
            except FileNotFoundError:
                pass
    return entries


def shortcut_locations() -> tuple[Path, Path]:
    desktop = ctypes.create_unicode_buffer(32768)
    result = ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, desktop)
    if result:
        raise OSError(f"SHGetFolderPathW desktop failed: {result}")
    return (Path(desktop.value) / "Prism Layer Studio.lnk",
            Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Prism Layer Studio")


def execute_installer_test(setup: Path, output: Path, timeout: int) -> int:
    if os.name != "nt":
        raise SystemExit("Installer verification requires Windows.")
    if not setup.is_file():
        raise SystemExit(f"Setup missing: {setup}")
    existing = registered_installations()
    desktop_link, start_group = shortcut_locations()
    if existing or desktop_link.exists() or start_group.exists():
        raise SystemExit("Refusing to replace an existing installation or application shortcut. Use a fresh Windows account for this test.")
    output.mkdir(parents=True, exist_ok=True)
    run_dir = Path(tempfile.mkdtemp(prefix="install-cycle-", dir=output))
    install_dir = run_dir / "中文安装路径" / "Prism Layer Studio"
    external_result = run_dir / "外部计算结果保留.json"
    external_result.write_text('{"keep":"用户外部计算结果"}', encoding="utf-8")
    user_data = Path(os.environ["LOCALAPPDATA"]) / "PrismLayerStudio"
    user_data.mkdir(parents=True, exist_ok=True)
    data_sentinel = user_data / f"installer-test-{uuid.uuid4().hex}.keep"
    data_sentinel.write_text("preserve existing user data", encoding="utf-8")
    before_external, before_data = sha256(external_result), sha256(data_sentinel)
    report = {"setup": str(setup), "setupSha256": sha256(setup),
              "installDirectory": str(install_dir), "testedAt": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
              "runtimeAbsentBranch": "NOT TESTED: shared system runtime is not removed or modified for this test",
              "steps": [], "passed": False}
    installed = False
    started = time.monotonic()
    try:
        install = subprocess.run([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/SP-",
                                  "/LANG=chinesesimplified", "/TASKS=desktopicon", f"/DIR={install_dir}",
                                  f"/LOG={run_dir / 'install.log'}"], timeout=timeout)
        report["installExitCode"] = install.returncode
        executable = install_dir / "PrismLayerStudio.exe"
        installed = executable.is_file()
        assert install.returncode in (0, 3010), f"Setup exit code {install.returncode}"
        assert installed, "Setup did not install executable at selected Chinese path"
        source_exe = setup.parent / "PrismLayerStudio.exe"
        if source_exe.is_file():
            assert sha256(executable) == sha256(source_exe), "Installed EXE differs from portable EXE"
        report["steps"].append("custom Chinese install directory and installed EXE verified")
        entries = registered_installations()
        assert entries and all(x.get("DisplayVersion") == "2.6.0" for x in entries), "Windows uninstall registration/version missing"
        assert any(Path(x.get("InstallLocation", "")).resolve() == install_dir.resolve() for x in entries), "Uninstall registration path differs"
        report["registration"] = entries
        assert desktop_link.is_file(), "Desktop shortcut missing"
        assert (start_group / "Prism Layer Studio.lnk").is_file(), "Start menu shortcut missing"
        assert (start_group / "Uninstall Prism Layer Studio.lnk").is_file(), "Start menu uninstall shortcut missing"
        report["steps"].append("desktop/start menu shortcuts and Windows uninstall registration verified")
        driver = Path(__file__).with_name("run_packaged_smoke.py")
        smoke = subprocess.run([sys.executable, str(driver), "--exe", str(executable),
                                "--output", str(run_dir / "installed-exe-smoke"), "--scales", "1", "--timeout", "120"], timeout=180)
        assert smoke.returncode == 0, "Installed executable failed real WebView2 integration tests"
        report["steps"].append("installed EXE launched and passed real WebView2 integration tests")
        uninstaller = install_dir / "unins000.exe"
        assert uninstaller.is_file(), "Uninstaller missing"
        uninstall = subprocess.run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                                    f"/LOG={run_dir / 'uninstall.log'}"], timeout=timeout)
        report["uninstallExitCode"] = uninstall.returncode
        assert uninstall.returncode in (0, 3010), f"Uninstall exit code {uninstall.returncode}"
        for _ in range(60):
            if not install_dir.exists():
                break
            time.sleep(0.5)
        assert not executable.exists(), "EXE remains after uninstall"
        assert not install_dir.exists() or not any(install_dir.iterdir()), "Installed program files remain after uninstall"
        assert not registered_installations(), "Windows uninstall registration remains"
        assert not desktop_link.exists(), "Desktop shortcut remains"
        assert not start_group.exists() or not any(start_group.iterdir()), "Start menu shortcuts remain"
        assert external_result.is_file() and sha256(external_result) == before_external, "External calculation result changed or removed"
        assert data_sentinel.is_file() and sha256(data_sentinel) == before_data, "User data changed or removed"
        report["steps"].append("uninstall removed installed files/shortcuts/registration and preserved external results and user data")
        report["passed"] = True
    except Exception as error:
        report["error"] = f"{type(error).__name__}: {error}"
        report["installationMayRemain"] = installed and (install_dir / "PrismLayerStudio.exe").exists()
    finally:
        report["elapsedSeconds"] = round(time.monotonic() - started, 2)
        report_path = output / "installer-test-summary.json"
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # Only our uniquely named sentinel is removed after preservation has been checked.
        if data_sentinel.is_file() and sha256(data_sentinel) == before_data:
            data_sentinel.unlink()
        print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", type=Path, default=Path("release/PrismLayerStudio-Setup.exe"))
    parser.add_argument("--output", type=Path, default=Path("release/test-results/installer"))
    parser.add_argument("--timeout", type=int, default=600)
    arguments = parser.parse_args()
    sys.exit(execute_installer_test(arguments.setup.resolve(), arguments.output.resolve(), arguments.timeout))
