r"""Archive installed distribution notices using the selected build interpreter.

Run with .venv-build\Scripts\python.exe. No network is required: immutable
upstream notices are committed under licenses/upstream and copied with source.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import sys


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "licenses"
    target.mkdir(exist_ok=True)
    records = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda d: d.metadata.get("Name", "").lower()):
        name = distribution.metadata.get("Name", "unknown")
        version = distribution.version
        safe = re.sub(r"[^a-zA-Z0-9_.-]", "_", name + "-" + version)
        archived = []
        for item in distribution.files or []:
            file = Path(item)
            if not re.match(r"^(LICENSE|COPYING|NOTICE|COPYRIGHT)(\b|[._-])", file.name, re.IGNORECASE):
                continue
            source = Path(distribution.locate_file(item))
            if not source.is_file():
                continue
            # Keep relative package path so vendored licenses do not overwrite
            # each other, while preventing RECORD paths outside the archive.
            parts = [p for p in file.parts if p not in ("..", ".", "") and p != file.anchor]
            destination = target / "python-packages" / safe / Path(*parts)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            archived.append(str(destination.relative_to(target)).replace("\\", "/"))
        records.append({"name": name, "version": version,
                        "declared_license": distribution.metadata.get("License-Expression") or distribution.metadata.get("License") or "see original notices",
                        "files": archived})
    python_license = Path(sys.base_prefix) / "LICENSE.txt"
    if not python_license.is_file():
        python_license = Path(sys.base_prefix) / "LICENSE"
    if not python_license.is_file():
        raise SystemExit("Build Python's LICENSE.txt is missing; use an official Python installation.")
    destination = target / "python" / "LICENSE.txt"
    destination.parent.mkdir(exist_ok=True)
    shutil.copyfile(python_license, destination)
    manifest = {"python_version": sys.version, "components": records,
                "python_license_sha256": hashlib.sha256(destination.read_bytes()).hexdigest()}
    (target / "component-manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Archived notices for {len(records)} installed distributions and CPython into {target}")


if __name__ == "__main__":
    main()
