"""Launch the shipped EXE, test its real WebView2, and verify native output files.

Usage: python tests/run_packaged_smoke.py --exe release/PrismLayerStudio.exe
The app itself contains Python; this DEVELOPMENT driver is not needed by users.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time


def validate_exports(folder: Path) -> dict:
    csv_file = folder / 'prism-layer-studio-layers.csv'
    json_file = folder / 'prism-layer-studio-result.json'
    raw = csv_file.read_bytes()
    assert raw.startswith(b'\xef\xbb\xbf'), 'CSV UTF-8 BOM was lost'
    rows = list(csv.reader(io.StringIO(raw.decode('utf-8-sig'))))
    assert rows[0][0] == '层号' and len(rows) == 11, 'CSV header/layers incorrect'
    data = json.loads(json_file.read_text(encoding='utf-8-sig'))
    assert data['version'] == '2.6.0', 'desktop JSON release identifier incorrect'
    result = data['result']
    assert result['mode'] == 'forward' and result['N'] == 10
    assert abs(result['w'] - 0.00006932296515521358) < 1e-15
    assert abs(float(rows[-1][2]) - result['T']) < 1e-12
    return {'csv': str(csv_file), 'json': str(json_file), 'csvRows': len(rows), 'jsonVersion': data['version']}


def run(executable: Path, output: Path, factors: list[str], timeout: int) -> int:
    if os.name != 'nt':
        raise SystemExit('Packaged Windows integration testing requires Windows.')
    output.mkdir(parents=True, exist_ok=True)
    reports = []
    for factor in factors:
        run_folder = output / f'scale-{factor}'
        exports = run_folder / '中文导出结果'
        exports.mkdir(parents=True, exist_ok=True)
        report_file = run_folder / 'webview2-report.json'
        if report_file.exists():
            report_file.unlink()
        environment = os.environ.copy()
        environment['PRISM_STUDIO_SMOKE_REPORT'] = str(report_file.resolve())
        environment['PRISM_STUDIO_SMOKE_EXPORT_DIR'] = str(exports.resolve())
        environment['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS'] = (
            f'--force-device-scale-factor={factor} --disable-background-networking '
            '--host-resolver-rules="MAP * ~NOTFOUND, EXCLUDE localhost, EXCLUDE 127.0.0.1"'
        )
        # Deliberately exclude installed Python/Conda from the application's PATH.
        environment['PATH'] = os.pathsep.join([str(executable.parent), str(Path(os.environ['SystemRoot'])/'System32'), os.environ['SystemRoot']])
        started = time.monotonic()
        process = subprocess.Popen([str(executable)], cwd=run_folder, env=environment)
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], capture_output=True)
            reports.append({'scale':factor,'passed':False,'error':'EXE did not exit after smoke report', 'elapsedSeconds':round(time.monotonic()-started,2)})
            continue
        try:
            report = json.loads(report_file.read_text(encoding='utf-8-sig'))
            assert returncode == 0, f'EXE exit code {returncode}'
            assert report['passed'], 'embedded WebView2 tests failed'
            assert abs(float(report['devicePixelRatio'])-float(factor)) < 0.02, 'requested renderer scale was not applied'
            export_results = validate_exports(exports)
            report['nativeExportVerification'] = export_results
            report['applicationPathExcludesPython'] = True
            report['offlineSimulationBrowserArguments'] = environment['WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS']
            report['physicalNetworkDisconnected'] = False
            report['cleanMachineWithoutPython'] = 'NOT TESTED: same host with Python removed from child PATH'
            report['exeExitCode'] = returncode
            report['elapsedSeconds'] = round(time.monotonic()-started,2)
            report_file.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            reports.append({'scale':factor,'passed':True,'tests':len(report['tests']),'report':str(report_file),'elapsedSeconds':report['elapsedSeconds']})
        except Exception as error:
            reports.append({'scale':factor,'passed':False,'error':str(error),'exitCode':returncode,'report':str(report_file),'elapsedSeconds':round(time.monotonic()-started,2)})
        print(json.dumps(reports[-1],ensure_ascii=False),flush=True)
    summary = {
        'executable':str(executable),'testedAt':time.strftime('%Y-%m-%dT%H:%M:%S%z'),
        'dpiMethod':'Chromium/WebView2 renderer scaling simulation; no claim of changing system DPI or testing multiple monitors',
        'offlineMethod':'Chromium DNS denies all non-loopback hosts plus application CSP blocks remote requests; physical network adapter is unchanged',
        'runs':reports,'passed':bool(reports) and all(report['passed'] for report in reports),
    }
    (output/'packaged-smoke-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    return 0 if summary['passed'] else 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--exe',type=Path,default=Path('release/PrismLayerStudio.exe'))
    parser.add_argument('--output',type=Path,default=Path('release/test-results/packaged'))
    parser.add_argument('--scales',nargs='+',default=['1','1.25','1.5','2'])
    parser.add_argument('--timeout',type=int,default=120)
    args=parser.parse_args()
    executable=args.exe.resolve()
    if not executable.is_file():
        parser.error(f'EXE not found: {executable}')
    sys.exit(run(executable,args.output.resolve(),args.scales,args.timeout))
