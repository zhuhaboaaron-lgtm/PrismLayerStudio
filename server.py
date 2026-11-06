"""Start Prism Layer Studio in a regular browser (Python standard library only)."""
import argparse
import webbrowser
from runtime import create_server


def main():
    parser = argparse.ArgumentParser(description='Prism Layer Studio 本地网页服务')
    parser.add_argument('--host', default='127.0.0.1', help='默认仅本机可访问；局域网需显式指定 0.0.0.0')
    parser.add_argument('--port', type=int, default=8000, help='起始端口，默认 8000；0 表示随机端口')
    parser.add_argument('--no-browser', action='store_true', help='不自动打开浏览器')
    args = parser.parse_args()
    ports = [0] if args.port == 0 else range(args.port, min(args.port + 10, 65536))
    httpd = None
    for port in ports:
        try:
            httpd = create_server(args.host, port)
            break
        except OSError:
            continue
    if httpd is None:
        raise SystemExit('无法找到可用端口。')
    host_for_url = '127.0.0.1' if args.host == '0.0.0.0' else args.host
    url = f'http://{host_for_url}:{httpd.server_address[1]}/'
    print('Prism Layer Studio · 网页版')
    print('访问：' + url)
    print('按 Ctrl+C 停止服务。')
    if not args.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print('\n已停止。')
    finally:
        httpd.server_close()


if __name__ == '__main__':
    main()
