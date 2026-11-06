# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH)
webview_datas, webview_binaries, webview_hiddenimports = collect_all('webview')
datas = [(str(root / 'app'), 'app'),
         (str(root / 'LICENSE'), '.'),
         (str(root / 'assets'), 'assets'),
         (str(root / 'desktop_bridge.js'), '.'),
         (str(root / 'tests' / 'desktop_smoke.js'), 'tests')]
datas += webview_datas
licenses = root / 'licenses'
if licenses.is_dir():
    datas.append((str(licenses), 'licenses'))

a = Analysis([str(root / 'desktop.py')], pathex=[str(root)],
             binaries=webview_binaries, datas=datas,
             hiddenimports=webview_hiddenimports,
             hookspath=[], hooksconfig={}, runtime_hooks=[],
             excludes=['PyQt5', 'PyQt6', 'PySide2', 'PySide6', 'tkinter',
                       'cefpython3', 'webview.platforms.qt', 'webview.platforms.gtk',
                       'webview.platforms.cocoa', 'webview.platforms.android'],
             noarchive=False, optimize=0)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, a.binaries, a.datas, [],
          name='PrismLayerStudio', debug=False,
          bootloader_ignore_signals=False, strip=False, upx=False,
          console=False, disable_windowed_traceback=False,
          version=str(root / 'installer' / 'version_info.txt'),
          icon=str(root / 'assets' / 'prism-layer-studio.ico'),
          manifest=str(root / 'installer' / 'app.manifest'))
