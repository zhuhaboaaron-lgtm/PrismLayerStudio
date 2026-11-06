# Third-party license archive

`python/LICENSE.txt` is the original license file from the official CPython
3.13.7 installation used for this build. The interpreter source was not modified.

`python-packages/` preserves original LICENSE, COPYING, NOTICE and COPYRIGHT files
available through the installed distributions' RECORD metadata, including
vendored build-tool notices. `component-manifest.json` records installed versions
and their declared licenses. This is a build environment inventory, so it can
include tools which are not inside the application executable.

`upstream/` supplies original notices missing from or supplementary to the
installed wheel files:

- proxy_tools 0.1.0: upstream BSD two-clause license. PyPI's MIT metadata differs
  from its source header and upstream LICENSE.txt; both facts are retained in the
  inventory and project notices.
- Microsoft.Web.WebView2 1.0.3856.49: LICENSE.txt and NOTICE.txt from Microsoft's
  exact NuGet package version matching the DLL shipped with pywebview 6.2.1.
- cffi 2.1.1: original MIT-0 license plus copyright and permission comments from
  the bundled Windows x86/x64 libffi source.
- Inno Setup 6.6.1: original license from the official tagged source.

`upstream/sources.json` records the source URLs and SHA-256 values of these texts.
The Microsoft Edge WebView2 Runtime is distributed as its unchanged, signed
official standalone installer and remains subject to Microsoft's Runtime terms;
its identity and original source are recorded in `runtime/webview2-runtime.lock.json`
in the release. The SDK license is distinct from the Runtime license.

To refresh installed-package notices using the selected build interpreter:

```bat
.venv-build\Scripts\python.exe scripts\collect-licenses.py
```

The collector does not download or alter the committed upstream notices.
