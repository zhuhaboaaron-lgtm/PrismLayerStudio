"""Create reviewable source and offline portable archives without build caches.

Run after build.bat, build-installer.bat and the test/report preparation.
Does not modify app source or any user results.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"
OMITTED_DIRS = {"release", "build", "dist", ".git", ".tools", "__pycache__", "node_modules", ".pytest_cache", "test-results", "legacy"}
SOURCE_ROOT = "PrismLayerStudio-2.6.0-source"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_source_files():
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT)
        if any(part in OMITTED_DIRS or part.startswith(".venv") for part in relative.parts):
            continue
        if relative.name.startswith('CODEX_'):
            continue
        if relative.parts[0] == "vendor" and path.suffix.lower() != ".json":
            continue
        if path.suffix.lower() in {".pyc", ".pfx", ".p12", ".pem", ".key"} or path.name.startswith(".env"):
            continue
        yield path, relative


def main() -> None:
    required = [RELEASE / "PrismLayerStudio.exe", RELEASE / "PrismLayerStudio-Setup.exe",
                RELEASE / "runtime/MicrosoftEdgeWebView2RuntimeInstallerX64.exe",
                ROOT / "LICENSE", ROOT / "BUILD_GUIDE.md", ROOT / "USER_GUIDE.zh-CN.md", ROOT / "THIRD_PARTY_NOTICES.md"]
    for path in required:
        if not path.is_file():
            raise FileNotFoundError(f"Release component missing: {path}")
    subprocess.run([sys.executable, str(ROOT / 'scripts/prepare-installer-licenses.py')], check=True)
    note = ("# 源码归档说明\n\n此归档保存 v2.6 完整应用、桌面容器、构建脚本、测试及文档。\n\n"
            "不含 Python 虚拟环境、构建缓存、工具安装目录与二进制第三方依赖；首次构建需要联网下载固定依赖，"
            "WebView2 通过 vendor/webview2-runtime.lock.json 中的固定 Microsoft URL、SHA256 及签名验证获取。\n\n"
            "项目自有源码与资产采用根目录 MIT LICENSE；第三方声明位于 licenses/。\n")
    source_zip = RELEASE / "PrismLayerStudio-2.6.0-Source.zip"
    with zipfile.ZipFile(source_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        for path, relative in safe_source_files():
            archive.write(path, f"{SOURCE_ROOT}/{relative.as_posix()}")
        archive.writestr(f"{SOURCE_ROOT}/SOURCE_ARCHIVE_NOTE.md", note)
    print(f"Created {source_zip.name}", flush=True)
    for filename in ("LICENSE", "README.md", "BUILD_GUIDE.md", "USER_GUIDE.zh-CN.md", "THIRD_PARTY_NOTICES.md", "TEST_REPORT.md", "TEST_RESULTS.md"):
        path = ROOT / filename
        if path.is_file():
            shutil.copy2(path, RELEASE / filename)
    if (ROOT / "licenses").is_dir():
        shutil.copytree(ROOT / "licenses", RELEASE / "licenses", dirs_exist_ok=True)
    script_dir = RELEASE / "build-scripts"
    script_dir.mkdir(exist_ok=True)
    for path in ROOT.glob("*.bat"):
        shutil.copy2(path, script_dir / path.name)
    for filename in ("requirements-build.txt", "PrismLayerStudio.spec"):
        shutil.copy2(ROOT / filename, script_dir / filename)
    for dirname in ("scripts", "installer"):
        shutil.copytree(ROOT / dirname, script_dir / dirname, dirs_exist_ok=True,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (script_dir / "README.txt").write_text(
        "完整可重构项目位于 PrismLayerStudio-2.6.0-Source.zip。请先解压，再从源码根目录执行 build.bat。\n"
        "本目录是构建脚本的独立审阅副本，不包含 app/。\n", encoding="utf-8")
    portable_zip = RELEASE / "PrismLayerStudio-2.6.0-Portable-Offline-x64.zip"
    with zipfile.ZipFile(portable_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=3) as archive:
        for filename in ("LICENSE", "PrismLayerStudio.exe", "USER_GUIDE.zh-CN.md", "THIRD_PARTY_NOTICES.md"):
            archive.write(RELEASE / filename, filename)
        for dirname in ("runtime",):
            for path in sorted((RELEASE / dirname).rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(RELEASE).as_posix())
        for path in sorted((ROOT / 'build/installer-licenses').glob('*')):
            if path.is_file():
                archive.write(path, 'licenses/' + path.name)
    print(f"Created {portable_zip.name}", flush=True)
    files = []
    for path in sorted(RELEASE.rglob("*")):
        if path.is_file() and path.name not in {"SHA256SUMS.txt", "release-manifest.json"}:
            files.append({"path": path.relative_to(RELEASE).as_posix(), "bytes": path.stat().st_size, "sha256": sha256(path)})
    (RELEASE / "SHA256SUMS.txt").write_text("".join(f"{item['sha256']}  {item['path']}\n" for item in files), encoding="utf-8")
    manifest = {"product": "Prism Layer Studio", "version": "2.6.0", "platform": "Windows x64",
                "sourceArchive": source_zip.name, "offlinePortableArchive": portable_zip.name, "files": files}
    (RELEASE / "release-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Release source, offline portable package, scripts, licenses and SHA256 manifest completed.", flush=True)


if __name__ == "__main__":
    main()
