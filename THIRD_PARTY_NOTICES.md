# Prism Layer Studio 2.6.0 第三方依赖及许可证

本项目自有源码、文档及原始资产采用根目录 `LICENSE` 中的 MIT 许可证。本文件说明 Windows 桌面发行所用第三方组件。精确版本以 `requirements-build.txt`、构建清单及原始许可证文本为准。第三方依赖的版权及许可独立存在，不因本项目采用 MIT 而改变。

## 运行和构建组件

| 组件 | 用途 | 许可证/权利说明 | 官方来源 |
|---|---|---|---|
| CPython 3.13.7 x64 | 打包在 EXE 中的 Python 运行时与标准库 | PSF License Version 2 及其中列明的第三方声明；未修改 Python 解释器源码 | [Python 许可](https://docs.python.org/3/license.html) |
| pywebview 6.2.1 | 原生窗口、Windows WebView2 容器与 JavaScript/Python 桥 | BSD 3-Clause；保留版权、条件和免责声明 | [pywebview LICENSE](https://github.com/r0x0r/pywebview/blob/master/LICENSE) |
| pythonnet | Windows .NET/WinForms 调用 | MIT | [Python.NET LICENSE](https://github.com/pythonnet/pythonnet/blob/master/LICENSE) |
| clr-loader | 加载 .NET 运行时 | MIT | [clr-loader](https://github.com/pythonnet/clr-loader) |
| cffi 2.1.1 / pycparser | CLR 加载相关传递依赖 | 分别为 MIT-0 / BSD 3-Clause，包含的 libffi 另保留原始声明 | [cffi](https://github.com/python-cffi/cffi)、[pycparser](https://github.com/eliben/pycparser) |
| bottle | pywebview 的本地服务相关依赖 | MIT | [Bottle](https://github.com/bottlepy/bottle) |
| proxy-tools / typing-extensions | pywebview 的工具及类型兼容依赖 | proxy-tools 元数据标注 MIT、源码及上游 LICENSE.txt 为 BSD 两条款，归档保留原文；typing-extensions 为 PSF 系列许可 | [proxy-tools](https://github.com/jtushman/proxy_tools)、[typing-extensions](https://github.com/python/typing_extensions) |
| Microsoft WebView2 SDK / Loader 1.0.3856.49 | 在原生窗口中创建 WebView2 | Microsoft 版权的 BSD 风格三条款许可，保留原始文件和声明 | [此 SDK 版本原始许可](https://www.nuget.org/packages/Microsoft.Web.WebView2/1.0.3856.49/License) |
| Microsoft Edge WebView2 Runtime | 本地 Chromium 渲染、MathML、SVG 与 CSS | Microsoft 专有软件许可；发行保留微软原始签名安装器及其条款 | [官方下载](https://developer.microsoft.com/en-us/microsoft-edge/webview2/) |
| Microsoft .NET Framework | Windows 自带的托管运行环境 | Microsoft 软件许可；不是由本项目重新授权的开源软件 | [Microsoft .NET](https://dotnet.microsoft.com/) |
| PyInstaller 6.22.3 | 将 Python、静态资源和依赖封装为 EXE | GPL 2.0 附商业应用打包特别例外；部分文件 Apache 2.0 | [PyInstaller 许可](https://pyinstaller.org/en/stable/license.html) |
| Inno Setup 6.6.1 | Windows 安装与卸载程序 | Inno Setup License，Jordan Russell / Martijn Laan | [Inno Setup 许可](https://jrsoftware.org/files/is/license.txt) |
| Node.js | 仅运行开发测试，不是最终应用的运行依赖 | Node.js 及其依赖的许可证；不随主 EXE 分发 | [Node.js LICENSE](https://github.com/nodejs/node/blob/main/LICENSE) |

pip、setuptools、packaging、altgraph、pefile、pywin32-ctypes、pyinstaller-hooks-contrib 等构建依赖按实际锁定文件和所附原始声明列入许可证归档。构建工具不等同于最终 EXE 中全部模块；构建清单记录环境，原始许可证目录记录分发声明。

## WebView2 分发

安装版内含微软官方 x64 Evergreen Standalone Installer。应用检测本机运行时后按需调用，不使用需要现场联网的 WebView2 Bootstrapper。便携版单 EXE 使用系统已有运行时，完整离线便携包另附同一微软安装器。微软官方文档说明了这种离线分发方式：[分发应用和 WebView2 Runtime](https://learn.microsoft.com/en-us/microsoft-edge/webview2/concepts/distribution)。

运行时仍受微软许可约束，随附文件不得被当作本项目原创或改变数字签名。卸载 Prism Layer Studio 不卸载系统共享 WebView2。

## 原有网页、图标和字体

正式发行继续使用 v2.6 HTML、CSS、JavaScript、SVG 图形以及现有 ICO/PNG 图标，没有引入第三方网页主题、在线字体、图像素材或数学排版 CDN。项目维护者已选择 MIT 作为本项目自有代码、文档与原始资产的开源许可证；原有 `app/core.js` MIT 标识继续保留，第三方版权声明保持原样。

字体沿用页面原有系统字体栈。Segoe UI、Microsoft YaHei、Cambria Math 等由用户操作系统提供，不复制分发微软字体文件。CSS 声明中列出的 Inter、STIX 等名称不表示本发行包含这些字体。

STAR-CCM+ 及相关产品名称归其各自权利人所有。本软件为独立辅助计算工具，未表示 Siemens 对本软件的认可、认证或保证。

## 原始声明归档

交付的 `licenses/` 目录包含实际构建环境可获得的原始 LICENSE/COPYING/NOTICE 文本、CPython 原始完整许可证和组件版本清单。缺少在 wheel 中声明文件的上游组件另在 `licenses/upstream/` 保留原文、官方来源 URL 与 SHA-256。本文件是阅读索引，不代替应随二进制保留的原文。有关二进制最终签名状态、文件校验值和本机实测范围，请查看发行测试报告。
