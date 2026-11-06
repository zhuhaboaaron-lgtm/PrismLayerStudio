"""Integration smoke tests for static application packaging/hosting."""
import threading
import unittest
from urllib.request import urlopen
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from runtime import create_server


class ServerTests(unittest.TestCase):
    def test_serve_local_html_js(self):
        httpd = create_server('127.0.0.1', 0)
        th = threading.Thread(target=httpd.serve_forever, daemon=True)
        th.start()
        try:
            root = f'http://127.0.0.1:{httpd.server_address[1]}'
            for route, expected in [('/', b'Prism Layer Studio'),('/core.js', b'geomSum'),('/app.js', b'modeUpdate'),('/style.css', b'.layout')]:
                with urlopen(root+route,timeout=3) as response:
                    self.assertEqual(response.status, 200)
                    self.assertIn(expected, response.read())
            with self.assertRaises(Exception):
                urlopen(root+'/../server.py',timeout=3)
        finally:
            httpd.shutdown();httpd.server_close();th.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
