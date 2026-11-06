"""Verify the shipped PE and its actual embedded v2.6 resources."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pefile
from PyInstaller.archive.readers import CArchiveReader

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"


def main():
    executable = RELEASE / "PrismLayerStudio.exe"
    pe = pefile.PE(str(executable))
    assert pe.FILE_HEADER.Machine == 0x8664, "EXE must contain x64 machine code"
    assert pe.OPTIONAL_HEADER.Subsystem == 2, "EXE must use GUI subsystem (no console)"
    fixed = pe.VS_FIXEDFILEINFO[0]
    assert (fixed.FileVersionMS, fixed.FileVersionLS) == (0x20006, 0), "Wrong executable version"
    archive = CArchiveReader(str(executable))
    baseline = json.loads((ROOT / "tests/v2.6-baseline.json").read_text(encoding="utf-8"))["files"]
    embedded = {}
    for name, expected in baseline.items():
        payload = archive.extract(name.replace("/", "\\"))
        actual = hashlib.sha256(payload).hexdigest()
        assert actual == expected, f"Packaged v2.6 resource changed: {name}"
        embedded[name] = actual
    assert archive.extract("desktop_bridge.js") == (ROOT / "desktop_bridge.js").read_bytes()
    assert archive.extract("tests\\desktop_smoke.js") == (ROOT / "tests/desktop_smoke.js").read_bytes()
    manifests = []
    for resource in pe.DIRECTORY_ENTRY_RESOURCE.entries:
        if resource.id == 24:
            for identity in resource.directory.entries:
                for language in identity.directory.entries:
                    entry = language.data.struct
                    manifests.append(pe.get_data(entry.OffsetToData, entry.Size).decode("utf-8"))
    assert any("PerMonitorV2" in item and "asInvoker" in item for item in manifests)
    summary = json.loads((RELEASE / "test-results/packaged/packaged-smoke-summary.json").read_text(encoding="utf-8"))
    assert summary["passed"] and len(summary["runs"]) == 4
    for run in summary["runs"]:
        result = json.loads(Path(run["report"]).read_text(encoding="utf-8"))
        assert result["passed"] and result["frozen"] and len(result["tests"]) == 19
    installer = json.loads((RELEASE / "test-results/installer/installer-test-summary.json").read_text(encoding="utf-8"))
    assert installer["passed"]
    setup = RELEASE / "PrismLayerStudio-Setup.exe"
    setup_hash = hashlib.sha256(setup.read_bytes()).hexdigest()
    assert setup_hash == installer["setupSha256"], "Setup changed after install/uninstall testing"
    output = {"passed": True, "machine": "AMD64", "subsystem": "Windows GUI",
              "version": "2.6.0", "manifest": "asInvoker / PerMonitorV2",
              "embeddedOriginalV26Files": embedded,
              "embeddedDesktopBridgeMatchesSource": True,
              "embeddedSmokeSuiteMatchesSource": True,
              "exeSha256": hashlib.sha256(executable.read_bytes()).hexdigest(),
              "setupSha256": setup_hash,
              "packagedTests": "4 scales x 19 tests passed", "installerCycle": "passed"}
    target = RELEASE / "test-results/release-verification.json"
    target.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
