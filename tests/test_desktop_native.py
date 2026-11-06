"""Native export failure/cancel/atomicity and Unicode Windows clipboard tests."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from desktop_support import DesktopAPI, clipboard_text, write_export


class NativeExportTests(unittest.TestCase):
    def api(self,report=None,folder=None):
        environment={key:value for key,value in os.environ.items() if not key.startswith('PRISM_STUDIO_SMOKE_')}
        if report: environment['PRISM_STUDIO_SMOKE_REPORT']=str(report)
        if folder: environment['PRISM_STUDIO_SMOKE_EXPORT_DIR']=str(folder)
        with patch.dict(os.environ,environment,clear=True):
            api=DesktopAPI(SimpleNamespace(FileDialog=SimpleNamespace(SAVE='save')))
        api._window=Mock()
        return api

    @unittest.skipUnless(sys.platform=='win32','Native Windows file dialog contract')
    def test_cancelled_save_does_not_create_file(self):
        api=self.api()
        api._window.create_file_dialog.return_value=None
        result=api.save_file('prism-layer-studio-layers.csv','\ufeff层号,单层厚度\n')
        self.assertEqual(result,{'ok':False,'cancelled':True})
        self.assertEqual(api._exports,[])

    def test_export_rejects_path_injection_and_oversized_input(self):
        api=self.api()
        self.assertFalse(api.save_file('../external.csv','x')['ok'])
        self.assertFalse(api.save_file('prism-layer-studio-layers.csv',None)['ok'])
        self.assertFalse(api.save_file('prism-layer-studio-layers.csv','x'*16_000_001)['ok'])
        api._window.create_file_dialog.assert_not_called()

    def test_atomic_unicode_export_preserves_exact_csv_bytes(self):
        with tempfile.TemporaryDirectory(prefix='Prism-中文-') as folder:
            path=Path(folder)/'结果.csv'
            expected='\ufeff层号,单层厚度(m),备注\n1,1e-5,棱柱层 μm\n'
            write_export(path,expected)
            self.assertEqual(path.read_bytes(),expected.encode('utf-8'))
            self.assertEqual(list(Path(folder).glob('.prism-*.tmp')),[])

    def test_failed_atomic_replace_preserves_old_result_and_removes_temp(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'existing-result.csv'
            path.write_bytes(b'keep previous external result')
            with patch('desktop_support.os.replace',side_effect=PermissionError('readonly target')):
                with self.assertRaises(PermissionError):
                    write_export(path,'new result')
            self.assertEqual(path.read_bytes(),b'keep previous external result')
            self.assertEqual(list(Path(folder).glob('.prism-*.tmp')),[])

    def test_missing_parent_fails_without_creating_arbitrary_directories(self):
        with tempfile.TemporaryDirectory() as folder:
            parent=Path(folder)/'does-not-exist'
            with self.assertRaises(FileNotFoundError):
                write_export(parent/'result.csv','data')
            self.assertFalse(parent.exists())

    def test_json_export_normalizes_only_release_metadata(self):
        with tempfile.TemporaryDirectory(prefix='Prism-中文-') as folder:
            api=self.api(Path(folder)/'report.json',Path(folder)/'外部计算结果')
            payload={'version':'2.2','generatedAt':'preserved','result':{'w':0.00006932296515521358,'N':10,'note':'真实中文结果'}}
            result=api.save_file('prism-layer-studio-result.json',json.dumps(payload,ensure_ascii=False))
            self.assertTrue(result['ok'])
            actual=json.loads(Path(result['path']).read_text(encoding='utf-8'))
            self.assertEqual(actual,{**payload,'version':'2.6.0'})
            self.assertEqual(len(api._exports),1)

    def test_invalid_json_reports_error_without_overwriting_existing_result(self):
        with tempfile.TemporaryDirectory() as folder:
            api=self.api(Path(folder)/'report.json',folder)
            path=Path(folder)/'prism-layer-studio-result.json'
            path.write_bytes(b'previous valid result')
            with self.assertLogs(level='ERROR'):
                result=api.save_file(path.name,'{bad json')
            self.assertFalse(result['ok'])
            self.assertEqual(path.read_bytes(),b'previous valid result')
            self.assertEqual(api._exports,[])

    def test_file_permission_error_is_a_reviewable_error_response(self):
        with tempfile.TemporaryDirectory() as folder:
            api=self.api(Path(folder)/'report.json',folder)
            with patch('desktop_support.write_export',side_effect=PermissionError('write denied')):
                with self.assertLogs(level='ERROR'):
                    result=api.save_file('prism-layer-studio-layers.csv','csv')
            self.assertFalse(result['ok'])
            self.assertIn('write denied',result['error'])
            self.assertEqual(api._exports,[])

    def test_smoke_window_controls_disabled_for_regular_users(self):
        api=self.api()
        self.assertFalse(api.smoke_set_window('resize',1000,700)['ok'])
        self.assertFalse(api.smoke_status()['ok'])
        self.assertFalse(api.smoke_complete('{}')['ok'])
        api._window.resize.assert_not_called()

    @unittest.skipUnless(sys.platform=='win32','Windows Unicode clipboard')
    @unittest.skipIf(os.environ.get('PRISM_STUDIO_CI')=='1',
                     'Interactive Windows clipboard is verified locally, not on hosted CI')
    def test_actual_windows_clipboard_unicode_and_release_identifier(self):
        previous=clipboard_text()
        try:
            text='【Prism Layer Studio v2.3】\n棱柱层 中文 μm ρ y⁺\nN=10\n'
            self.assertTrue(self.api().copy_text(text)['ok'])
            self.assertEqual(clipboard_text(),text.replace('v2.3','v2.6.0'))
        finally:
            clipboard_text(previous)


if __name__=='__main__':
    unittest.main()
