"""Prism Layer Studio 2.6.0: offline Windows / WebView2 desktop host."""
from __future__ import annotations

import json
import logging
import sys
import tempfile
import threading

from desktop_support import (
    DesktopAPI, app_data_directory, configure_dpi, ensure_webview2,
    resource_directory, show_error,
)
from runtime import create_server

VERSION = "2.6.0"


def main() -> int:
    configure_dpi()
    data = app_data_directory()
    logging.basicConfig(filename=str(data / "desktop.log"), encoding="utf-8",
                        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    server = None
    thread = None
    api = None
    smoke_profile = None
    try:
        ensure_webview2()
        import webview

        webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = False
        webview.settings["ALLOW_DOWNLOADS"] = False
        webview.settings["ALLOW_FILE_URLS"] = False
        server = create_server("127.0.0.1", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        api = DesktopAPI(webview, VERSION)
        window = webview.create_window(
            f"Prism Layer Studio {VERSION}", url, js_api=api,
            width=1350, height=920, min_size=(480, 420), resizable=True,
            background_color="#07131f", text_select=True, zoomable=True,
        )
        api._window = window

        def loaded():
            try:
                window.evaluate_js((resource_directory() / "desktop_bridge.js").read_text(encoding="utf-8"))
                if api._smoke_report:
                    window.evaluate_js((resource_directory() / "tests" / "desktop_smoke.js").read_text(encoding="utf-8"))
            except Exception:
                logging.exception("Failed to initialise desktop compatibility layer")
                if api._smoke_report:
                    api.smoke_complete(json.dumps({"ok": False, "error": "desktop initialisation failed"}))
                else:
                    show_error("桌面文件保存组件启动失败。请关闭后重试，详细信息见日志：\n" + str(data / "desktop.log"))

        window.events.loaded += loaded
        if api._smoke_report:
            smoke_profile = tempfile.TemporaryDirectory(prefix="PrismSmokeProfile-")
        webview.start(gui="edgechromium", debug=False, private_mode=bool(smoke_profile),
                      storage_path=smoke_profile.name if smoke_profile else str(data / "WebView2"),
                      icon=str(resource_directory() / "assets" / "prism-layer-studio.ico"))
        return 0
    except Exception as exc:
        logging.exception("Desktop startup failed")
        if api and api._smoke_report:
            api.smoke_complete(json.dumps({"ok": False, "error": str(exc)}))
        else:
            show_error(f"Prism Layer Studio 无法启动：\n{exc}\n\n日志：{data / 'desktop.log'}")
        return 1
    finally:
        if server:
            server.shutdown()
            server.server_close()
        if thread:
            thread.join(timeout=3)
        if smoke_profile:
            try:
                smoke_profile.cleanup()
            except OSError:
                logging.warning("WebView2 smoke profile still in use at exit")


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    sys.exit(main())
