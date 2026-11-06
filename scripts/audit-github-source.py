"""Read-only public-source audit; findings contain filenames, never secret values."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SKIP = {'.git', 'build', 'dist', 'release', 'test-results', '__pycache__', '.tools', 'node_modules'}
SIGNATURES = [
    re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b'),
    re.compile(r'\bgithub_pat_[A-Za-z0-9_]{40,}\b'),
    re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{20,}\b'),
    re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    re.compile(r'''(?i)(?:access[_-]?token|api[_-]?key|client[_-]?secret|password)\s*[:=]\s*['"][A-Za-z0-9_.-]{16,}['"]'''),
]
PERSONAL_PATH = re.compile(r'[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/]', re.IGNORECASE)


def main():
    issues = []
    paths = []
    for directory, folders, filenames in os.walk(ROOT):
        folders[:] = [name for name in folders if name not in SKIP and not name.startswith('.venv')]
        for filename in filenames:
            path = Path(directory) / filename
            relative = path.relative_to(ROOT)
            paths.append(path)
            if path.stat().st_size >= 25 * 1024 * 1024:
                issues.append({'file':relative.as_posix(),'type':'large file in source'})
            if path.suffix.lower() in {'.exe','.msi','.zip','.pfx','.p12','.pem','.key','.log'} or (filename.startswith('.env') and filename!='.env.example'):
                issues.append({'file':relative.as_posix(),'type':'private/generated file type'})
            if 'legacy' in relative.parts or filename.startswith('CODEX_'):
                issues.append({'file':relative.as_posix(),'type':'historic private helper'})
            try:
                contents = path.read_text(encoding='utf-8-sig')
            except UnicodeError:
                continue
            if any(pattern.search(contents) for pattern in SIGNATURES):
                issues.append({'file':relative.as_posix(),'type':'possible credential signature'})
            if PERSONAL_PATH.search(contents):
                issues.append({'file':relative.as_posix(),'type':'personal absolute path'})
    baseline = json.loads((ROOT/'tests/v2.6-baseline.json').read_text(encoding='utf-8'))['files']
    indexed = (ROOT/'.git').is_dir()
    if indexed:
        available = subprocess.check_output(['git','ls-files','-z'],cwd=ROOT).split(b'\0')
        indexed = b'app/core.js' in available
    for name, expected in baseline.items():
        if hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=expected:
            issues.append({'file':name,'type':'v2.6 baseline changed'})
        if indexed:
            blob = subprocess.check_output(['git','show',':'+name],cwd=ROOT)
            if hashlib.sha256(blob).hexdigest()!=expected:
                issues.append({'file':name,'type':'Git index changed original v2.6 bytes'})
    result = {'passed':not issues,'filesScanned':len(paths),'totalBytes':sum(path.stat().st_size for path in paths),
              'originalV26FilesVerified':len(baseline),'gitIndexChecked':indexed,'findings':issues,
              'scope':'Common credential signatures, personal paths, binary exclusions, size and original v2.6 bytes; not a guarantee against every possible secret'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 0 if result['passed'] else 1


if __name__=='__main__':
    raise SystemExit(main())
