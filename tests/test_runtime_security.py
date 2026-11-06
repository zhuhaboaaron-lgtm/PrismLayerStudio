"""Real HTTP requests exercise loopback hosting and packaged-resource boundaries."""
from __future__ import annotations

import http.client
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import create_server


class RuntimeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='Prism-资源-')
        self.folder=Path(self.temp.name)
        self.app=self.folder/'app'
        self.app.mkdir()
        (self.app/'index.html').write_text('<!doctype html><meta charset="utf-8">测试',encoding='utf-8')
        (self.app/'empty-directory').mkdir()
        (self.folder/'secret.txt').write_text('private outside app',encoding='utf-8')
        with patch('runtime.app_directory',return_value=self.app):
            self.server=create_server('127.0.0.1',0)
        self.thread=threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=3)
        self.temp.cleanup()

    def request(self,path='/',method='GET',host=None):
        conn=http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=3)
        try:
            headers={} if host is None else {'Host':host}
            conn.request(method,path,headers=headers)
            response=conn.getresponse()
            return response.status,dict(response.getheaders()),response.read()
        finally:
            conn.close()

    def test_binds_only_explicit_ipv4_loopback(self):
        for host in ('0.0.0.0','::','192.168.1.1','localhost'):
            with self.subTest(host=host),self.assertRaises(ValueError):
                create_server(host,0)

    def test_security_headers_and_utf8_content(self):
        status,headers,content=self.request()
        self.assertEqual(status,200)
        self.assertIn('测试',content.decode('utf-8'))
        self.assertEqual(headers['Cache-Control'],'no-store')
        self.assertEqual(headers['X-Content-Type-Options'],'nosniff')
        self.assertEqual(headers['Referrer-Policy'],'no-referrer')
        self.assertIn("connect-src 'self' blob:",headers['Content-Security-Policy'])
        self.assertIn("frame-src 'none'",headers['Content-Security-Policy'])

    def test_directory_listing_disabled_for_get_and_head(self):
        for method in ('GET','HEAD'):
            with self.subTest(method=method):
                self.assertEqual(self.request('/empty-directory/',method)[0],403)

    def test_parent_traversal_cannot_disclose_external_file(self):
        for path in ('/../secret.txt','/%2e%2e/secret.txt','/..%5csecret.txt'):
            with self.subTest(path=path):
                status,headers,content=self.request(path)
                self.assertIn(status,(200,301,400,403,404))
                self.assertNotIn(b'private outside app',content)
                if status==301:
                    self.assertTrue(headers['Location'].startswith('/'))
                    _,_,redirected=self.request(headers['Location'])
                    self.assertNotIn(b'private outside app',redirected)

    def test_foreign_or_wrong_port_host_rejected(self):
        for host in ('attacker.example','attacker.example:'+str(self.server.server_port),'127.0.0.1:1','localhost:1'):
            with self.subTest(host=host):
                self.assertEqual(self.request(host=host)[0],403)
        self.assertEqual(self.request(host='localhost:'+str(self.server.server_port))[0],200)

    def test_reparse_path_cannot_expose_file_outside_app_get_or_head(self):
        junction=None
        path='/external.txt'
        try:
            os.symlink(self.folder/'secret.txt',self.app/'external.txt')
        except OSError as error:
            if os.name!='nt':
                self.skipTest(f'Creating symlinks is not allowed on this host: {error}')
            # NTFS directory junctions exercise Path.resolve() reparse-point
            # traversal without requiring the Windows symlink privilege.
            outside=self.folder/'outside'
            outside.mkdir()
            (outside/'secret.txt').write_text('private outside app',encoding='utf-8')
            junction=self.app/'external-link'
            result=subprocess.run(['cmd.exe','/d','/c','mklink','/J',str(junction),str(outside)],capture_output=True)
            if result.returncode:
                self.skipTest('This Windows host permits neither symlink nor NTFS junction creation')
            path='/external-link/secret.txt'
        try:
            for method in ('GET','HEAD'):
                with self.subTest(method=method):
                    self.assertEqual(self.request(path,method)[0],403)
        finally:
            if junction is not None and junction.exists():
                os.rmdir(junction)


if __name__=='__main__':
    unittest.main()
