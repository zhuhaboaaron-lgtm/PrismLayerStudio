"""Preserve all notice bytes while shortening installed paths for Windows."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "licenses"
DESTINATION = ROOT / "build/installer-licenses"


def main():
    DESTINATION.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in sorted(SOURCE.rglob("*")):
        if not path.is_file():
            continue
        relative = path.relative_to(SOURCE)
        component = relative.parts[1] if relative.parts[0] == "python-packages" else relative.parts[0]
        stem = re.sub(r"[^A-Za-z0-9_.-]", "_", component)[:24]
        filename = re.sub(r"[^A-Za-z0-9_.-]", "_", path.name)[:30]
        suffix = hashlib.sha256(relative.as_posix().encode("utf-8")).hexdigest()[:8]
        target = DESTINATION / f"{stem}-{suffix}-{filename}"
        shutil.copyfile(path, target)
        entries.append({"installedFile": target.name, "sourcePath": relative.as_posix(),
                        "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    (DESTINATION / "INDEX.json").write_text(json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")
    (DESTINATION / "README.txt").write_text(
        "Third-party license and notice files retain their original contents.\n"
        "Installed names are shortened for Windows path compatibility.\n"
        "INDEX.json maps each installed file to its source path and SHA256.\n", encoding="utf-8")
    print(f"Prepared {len(entries)} unchanged license/notice files with short installation paths.")


if __name__ == "__main__":
    main()
