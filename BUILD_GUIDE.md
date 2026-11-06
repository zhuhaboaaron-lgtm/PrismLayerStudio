# Prism Layer Studio 2.6.0 Windows 构建指南

本指南适用于 Windows 10 1809 及更新版本 / Windows 11 x64。正式界面源代码是 `app/index.html` 与同目录的两个 CSS、三个 JavaScript 文件。`publish/index.html` 是同一源码的单文件网页产物。公开仓库不包含历史私有上传脚本或预编译安装包。

## 环境

- Windows 10 1809 及更新版本 / Windows 11 64 位；使用 64 位 Python 3.11–3.14。本次使用官方 CPython 3.13.7 x64；重新构建推荐使用相同小版本并保留构建清单。
- Node.js 20 或更新版本，用于运行原有数值测试；最终用户不需要 Node.js 或 Python。
- 首次构建需要联网下载固定 Python 依赖、Inno Setup 编译器和微软官方 WebView2 x64 独立离线安装器。
- 若企业网络使用代理，先配置系统代理及 pip 代理；不要禁用 HTTPS 证书验证。

`requirements-build.txt` 固定构建包版本，包括 `pywebview==6.2.1` 和 `PyInstaller==6.22.3`。Inno Setup 固定为 6.6.1。构建虚拟环境为项目内 `.venv-build`，不会要求最终用户安装开发依赖。

## 一键构建

在资源管理器中双击批处理，或在项目根目录运行：

```bat
test.bat
build.bat
build-installer.bat
test.bat --packaged
```

`build.bat` 检查 Windows/Python 架构，创建虚拟环境，安装固定依赖，调用 `PrismLayerStudio.spec` 生成无控制台的单文件桌面程序。`build-installer.bat` 复用已经构建的主程序，准备离线 WebView2 和 Inno Setup，再生成安装程序。重新修改桌面代码后应先运行 `build.bat`，避免安装程序复用旧 EXE。

主要产物位于 `release/`：

- `PrismLayerStudio.exe`：单文件便携主程序；电脑上需要兼容的 WebView2 Runtime。
- `PrismLayerStudio-Setup.exe`：内置 WebView2 独立离线安装器的 Windows 安装程序。
- 含主程序和 WebView2 离线安装器的便携压缩包：用于运行环境未知或完全离线的电脑。
- 完整源码、构建脚本、中文说明、第三方许可证、测试结果及文件校验清单。

实际文件大小、SHA-256、构建环境和测试结论以交付目录中的清单与测试报告为准；本指南不是测试通过证明。

## WebView2 与离线安装

桌面容器强制使用 pywebview 的 EdgeChromium/WebView2 引擎，以保留现有 MathML、SVG、CSS 与键盘交互。没有重写页面，也不使用旧 IE 引擎。这个方案可以复用项目原有容器，因此没有引入体积更大的 PySide6/QtWebEngine。

应用计算和页面资源完全本地化。程序使用仅绑定 `127.0.0.1` 的进程内静态服务器和随机端口，无需用户启动服务器。该本机 HTTP 服务不需要互联网，也不向局域网提供页面。

安装程序使用微软的 **Evergreen Standalone Installer x64**；这不是需要现场联网下载的 Bootstrapper。安装前检测 HKCU/HKLM 中的 WebView2 Runtime 注册信息，要求版本 109 或更高，仅在缺失或过旧时安装。应用要求系统 .NET Framework 4.6.2 或更高，受支持系统自带兼容版本。默认按当前用户安装应用；WebView2 安装范围由微软安装器按进程权限和系统 Edge Updater 状态决定。

微软官方分发说明允许在应用安装程序中包含 Standalone Installer，并说明了 `/silent /install` 参数及注册表检测：[WebView2 分发文档](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)。发布时保留原始微软签名、下载 URL、文件版本、SHA-256 和缓存文件，避免把已打包运行时悄悄换成另一版。

公开仓库的 `vendor/` 仅保留下载锁定记录，构建脚本从记录的 Microsoft URL 获取离线安装器并验证 SHA-256 与 Microsoft 签名。若需要完全离线重建，请另行保存已验证的安装器和 Python wheel 缓存；不要提交到 Git。微软 Evergreen 下载入口会更新，锁文件只应在主动更新依赖时修改。

## 资源、路径与数据

- PyInstaller 将原始 `app/`、桌面兼容脚本和现有图标放入包内；运行时以 `sys._MEIPASS` 解析打包资源，不依赖开发机绝对路径。
- 单文件模式会在系统临时目录解压程序资源；用户导出结果由“另存为”选择到可写目录，不能写入该临时资源目录。
- WebView2 缓存及应用日志使用当前用户的本地应用数据目录。卸载程序不遍历或删除用户导出的 CSV/JSON。
- 源码与网页采用 UTF-8，CSV 含 UTF-8 BOM；测试应涵盖中文目录和中文导出文件名。
- 字体沿用页面原有系统字体栈，不从网络下载字体，也不额外分发微软字体。

## 测试与验收

`test.bat` 运行原有数值测试和 Python 测试。`test.bat --packaged` 另启动 `release/PrismLayerStudio.exe`，在真实 WebView2 中检查界面行为及原生导出文件，并将报告写入 `release/test-results/packaged/`。该测试的 100%/125%/150%/200% 为渲染器缩放模拟，不等同于改变系统显示缩放；离线模拟阻断远程域名解析，本机网卡保持原状态。打包后的桌面测试需在有桌面会话的 Windows 用户环境中运行，以实际 WebView2 结果为准，不能用 Node 的数值测试替代。

发行前至少核对：全部模式、菜单鼠标/键盘开关、物性刷新、SVG 模型跟随/选层/暂停、折叠公式与 MathML、剪贴板、CSV/JSON 文件内容、无网络运行、中文路径、窗口状态切换、125%/150%/200% 缩放、安装和卸载。DPI/视口自动化检查与真正改变 Windows 显示缩放的测试应在报告中分别说明。

源文件完整性基线为 `tests/v2.6-baseline.json`。六个 SHA-256 来源于用户交付的 v2.6 ZIP，且初始模块文件与 ZIP 逐字节一致；`publish/index.html` 也与当前模块拼接结果文本一致。原网页中 JSON `version: "2.2"` 和复制摘要 `v2.3` 是已有历史元数据；桌面兼容层在导出/复制时统一为 `2.6.0`，保留原始网页文件字节及全部计算内容。

## 清理与重建

```bat
clean.bat
build.bat
build-installer.bat
```

清理只针对项目构建缓存。不要用清理脚本删除外部计算结果或用户数据。若要从全新环境复现，请同时保留已锁定下载的 WebView2 安装器、Inno Setup 和 Python wheel 缓存；仅固定版本不能保证公网永久保留原始文件。

## 桌面测试与最终归档命令

在项目源码根目录运行：

```bat
test.bat --packaged
.venv-build\Scripts\python.exe tests\test_installer.py
.venv-build\Scripts\python.exe scripts\verify-release.py
powershell.exe -NoProfile -ExecutionPolicy Bypass -File scripts\package-release.ps1
```

安装测试实际安装到独立中文目录并卸载，拒绝覆盖已有同名应用或快捷方式。归档脚本生成完整源码 ZIP、完整离线便携 ZIP 与 SHA256SUMS.txt；源码 ZIP 不重复包含二进制依赖，首次构建按锁定 URL 下载，离线重建需额外保留 vendor 安装器和 Python wheel 缓存。

`desktop_bridge.js` 只处理原生文件保存、剪贴板、发行版本标签，以及特定 WebView2 缩放下长 MathML 表达式的可用宽度适配。公式内容、原始六个 app 文件及默认界面设计保持不变。安装程序和离线便携 ZIP 的许可证原文采用短文件名，INDEX.json 保留原路径与 SHA-256，避免中文深路径下的 MAX_PATH 问题。

## 签名与发布

微软 WebView2 安装器应具有有效的 Microsoft 数字签名。应用 EXE 和自制安装程序只有在发布者配置自己的代码签名证书后才会具有发布者签名；构建脚本不会伪造证书。Windows SmartScreen 的信誉判断与功能测试是不同事项。发布者可在构建完成后用 Windows SDK 的 `signtool` 签名，再重新生成最终文件 SHA-256。

PyInstaller 可用于生成商业应用，其特别例外允许应用采用自己的许可证，但仍须遵守全部依赖的许可证：[PyInstaller 许可证](https://pyinstaller.org/en/stable/license.html)。第三方完整声明随 `THIRD_PARTY_NOTICES.md` 与 `licenses/` 交付。
