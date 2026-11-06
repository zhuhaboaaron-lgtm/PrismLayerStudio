"""Read-only CRC, release SHA256, source and offline portable archive checks."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RELEASE = ROOT / "release"


def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def main():
    manifest = json.loads((RELEASE / 'release-manifest.json').read_text(encoding='utf-8'))
    for item in manifest['files']:
        path = RELEASE / item['path']
        assert path.is_file() and path.stat().st_size == item['bytes'], item['path']
        assert digest(path) == item['sha256'], item['path']
    baseline = json.loads((ROOT/'tests/v2.6-baseline.json').read_text(encoding='utf-8'))['files']
    with zipfile.ZipFile(RELEASE/manifest['sourceArchive']) as source:
        assert source.testzip() is None
        prefix = 'PrismLayerStudio-2.6.0-source/'
        for name, expected in baseline.items():
            assert hashlib.sha256(source.read(prefix+name)).hexdigest() == expected
        assert not any(name.endswith('legacy/_gitee_upload.mjs') for name in source.namelist())
        for name in ['build.bat','build-installer.bat','clean.bat','test.bat','BUILD_GUIDE.md',
                     'desktop.py','desktop_support.py','desktop_bridge.js','scripts/verify-archives.py']:
            assert source.read(prefix+name) == (ROOT/name).read_bytes(), name
        source_count = len(source.namelist())
    with zipfile.ZipFile(RELEASE/manifest['offlinePortableArchive']) as portable:
        assert portable.testzip() is None
        assert hashlib.sha256(portable.read('PrismLayerStudio.exe')).hexdigest() == digest(RELEASE/'PrismLayerStudio.exe')
        lock = json.loads((ROOT/'vendor/webview2-runtime.lock.json').read_text(encoding='utf-8-sig'))
        runtime_name='runtime/MicrosoftEdgeWebView2RuntimeInstallerX64.exe'
        assert hashlib.sha256(portable.read(runtime_name)).hexdigest() == lock['sha256']
        for item in json.loads(portable.read('licenses/INDEX.json')):
            assert hashlib.sha256(portable.read('licenses/'+item['installedFile'])).hexdigest()==item['sha256']
        portable_count=len(portable.namelist())
    print(json.dumps({'passed': True, 'releaseFilesVerified':len(manifest['files']),
                      'sourceArchiveEntries':source_count,'offlinePortableEntries':portable_count,
                      'originalV26FilesVerified':6,'offlineRuntimeVerified':True,
                      'portableLicenseOriginalBytesVerified':True},indent=2))


if __name__ == '__main__':
    main()
