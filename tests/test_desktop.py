"""Packaging contracts, offline resources, and immutable v2.6 source baseline."""
from __future__ import annotations

import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from runtime import app_directory


class ResourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.resources=[]

    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        key='href' if tag=='link' else 'src'
        if tag in ('script','link','img','iframe','source') and attrs.get(key):
            self.resources.append(attrs[key])


class DesktopPackagingTests(unittest.TestCase):
    def test_official_v26_source_baseline_unchanged(self):
        baseline=json.loads((ROOT/'tests/v26_baseline.json').read_text(encoding='utf-8'))
        for name,digest in baseline['sha256'].items():
            with self.subTest(file=name):
                self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),digest)

    def test_official_entry_and_all_resources_are_local(self):
        parser=ResourceParser()
        html=(ROOT/'app/index.html').read_text(encoding='utf-8')
        parser.feed(html)
        self.assertIn('<b>v2.6</b>',html)
        self.assertIn('id="fluidPicker"',html)
        self.assertEqual(len(re.findall(r'class="equation"',html)),15)
        for reference in parser.resources:
            with self.subTest(resource=reference):
                self.assertNotRegex(reference,r'^(https?:)?//')
                self.assertTrue((ROOT/'app'/reference).is_file())
        for css in (ROOT/'app').glob('*.css'):
            self.assertNotRegex(css.read_text(encoding='utf-8'),r'url\([\s\"\']*(?:https?:)?//')

    def test_pyinstaller_extraction_path_can_be_unicode(self):
        with tempfile.TemporaryDirectory(prefix='Prism-中文-') as name:
            app=Path(name)/'app'
            app.mkdir()
            (app/'index.html').write_text('测试',encoding='utf-8')
            with patch.object(sys,'_MEIPASS',name,create=True):
                self.assertEqual(app_directory(),app)

    def test_missing_packaged_resources_fail_explicitly(self):
        with tempfile.TemporaryDirectory() as name:
            with patch.object(sys,'_MEIPASS',name,create=True):
                with self.assertRaises(FileNotFoundError):
                    app_directory()


if __name__=='__main__':
    unittest.main()
