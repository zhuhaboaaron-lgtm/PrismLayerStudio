# Prism Layer Studio 2.6.0 验证记录

本文件区分此前 Windows 桌面发行的历史结果和本次 GitHub 源码整理的检查。GitHub Actions 尚未在远程仓库运行。

## 原始 v2.6 基准

正式页面是 `app/index.html`。该页面及 `style.css`、`hero.css`、`core.js`、`app.js`、`hero.js` 共六个文件保持原始 v2.6 字节；两份测试基线保存其 SHA-256。`.gitattributes` 为 app 目录关闭文本换行转换，避免 Git 克隆后哈希变化。

## 历史 Windows 本机验收

日期：2026-11-05，Asia/Shanghai。操作系统：Windows 11 x64 10.0.26200。构建环境：官方 CPython 3.13.7、pywebview 6.2.1、PyInstaller 6.22.3、Inno Setup 6.6.1。测试浏览器运行时：WebView2 156.0.4314.58；数值测试使用 Node.js 24.22.1。

| 检查 | 实际结果 |
|---|---|
| 数值核心 | 13/13 通过，未修改数学模型或算法 |
| Python 资源、导出与运行环境契约 | 21/21 通过 |
| 真实便携 EXE | 四档渲染缩放各 19/19 项通过，共 76 项 |
| 菜单与计算 | 物性选择、键盘关闭、自动刷新、全部正反计算、实测校准、翼型、圆管及非法输入恢复通过 |
| 图形与公式 | 真实模型同步、指针探针、键盘选层、动画暂停/恢复、折叠区域及 15 条 MathML 公式通过 |
| 原生输出 | 原页面按钮通过桌面桥保存真实 CSV/JSON；中文目录、CSV BOM、11 行与数值独立校验通过；真实 Unicode 剪贴板通过 |
| 窗口 | 真实调整尺寸、最大化、最小化及恢复通过 |
| 离线模拟 | 非本地 DNS 解析禁用，CSP 拒绝远程请求，计算与资源仍可用 |
| EXE 身份 | Windows GUI / AMD64 / 2.6.0 / PerMonitorV2，提取内嵌六个网页资源后哈希与基准一致 |
| Python 独立性 | 打包 EXE 子进程 PATH 排除 Python/Conda 后仍可运行；不等同于干净机器验收 |
| 安装与卸载 | 中文自定义目录安装、桌面与开始菜单快捷方式、卸载登记、已安装 EXE 19 项检查通过；卸载移除程序并保留外部结果和用户数据 |
| 离线运行时依赖 | 微软完整 Standalone x64 安装器的来源、文件大小、签名与 SHA-256 已验证 |

历史二进制测试是在开源整理前执行；本次只整理源码与许可，并增加公开仓库配置。重新构建后应重新运行打包和安装测试，再将对应结果随该次 Release 发布。原始机器日志、包含个人路径的 JSON 报告和大型二进制不提交到此源码仓库。

## GitHub 源码整理检查

- 本机运行公开目录中的 `test.bat`，13 项 Node 数值测试、21 项 Python 测试通过。
- 工作流使用 `PRISM_STUDIO_CI=1`，仅跳过不能由托管 runner 保证的真实交互剪贴板检查；本机默认仍执行该项。CI 配置不宣称验证完整桌面、打包 EXE 或安装程序。
- 本机另以官方 Python 3.13 设置 `PRISM_STUDIO_CI=1` 复验该分支，20 项 Python 检查通过、1 项剪贴板检查按设计跳过；这不是 GitHub 远程执行结果。
- 新增 MIT 许可证、公开 README、发布指南、贡献说明、Issue 模板和固定官方 Action SHA 的只读权限工作流。
- 新的构建配置将 MIT LICENSE 放入 EXE、安装目录与便携 ZIP，第三方许可证原文保留。
- `scripts/audit-github-source.py` 检查常见凭证签名、个人绝对路径、大型二进制以及原始六个文件；Git 索引存在时还会核对将要上传的原始页面字节。此检查不保证能发现所有形式的秘密数据。

## 仍需后续验收

- Windows 10 独立机器及完全未安装 Python 的干净系统。
- 完全缺失 WebView2 Runtime 时的首次离线安装；此前本机已有共享运行时。
- 实际 Windows 系统缩放切换和不同 DPI 显示器间移动；此前的四档比例是 WebView2 渲染缩放模拟。
- 物理断网场景；此前未改动网卡，仅进行 DNS/CSP 隔离模拟。
- 原生保存对话框的完整手工验收；自动化已验证实际写文件，契约测试覆盖选择、取消及异常路径。
- 发布者代码签名、杀毒信誉及 GitHub Actions 远程执行。附带的微软安装器保留微软签名，不代表应用 EXE 已有发布者签名。

复现命令见 [BUILD_GUIDE.md](BUILD_GUIDE.md)；发布步骤见 [GITHUB_PUBLISH_GUIDE.zh-CN.md](GITHUB_PUBLISH_GUIDE.zh-CN.md)。
