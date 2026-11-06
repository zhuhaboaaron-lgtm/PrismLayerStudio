# 上传 GitHub 与发布安装包

此目录是源码仓库。上传后，其他人可以查看、克隆、修改和构建 Prism Layer Studio；普通用户通过 GitHub Releases 下载已编译的 Windows 软件。

## 1. 创建空仓库

登录自己的 GitHub，在 **New repository** 中创建仓库。建议仓库名称为 `PrismLayerStudio`，可见性选择 **Public**。目录已经包含 README、MIT LICENSE 和 Git 配置文件，创建空仓库时无需再次生成这些文件。

把**当前文件夹内的文件和目录**作为仓库根内容上传，确保仓库首页能直接看到 `README.md`、`LICENSE`、`app/`、`desktop.py` 和构建脚本。不要只把一个源码 ZIP 上传到 Code 页面，否则其他人不便浏览代码、提交修改或运行自动检查。

网页上传适合首次少量文件导入；包含点号开头的 `.github/`、`.gitignore`、`.gitattributes` 也应保留。使用 GitHub Desktop 的 **Add local repository / Publish repository** 或 Git 命令上传完整目录，可减少漏传隐藏文件的情况。

Git 命令方式（把占位值替换成自己的真实仓库 URL）：

```powershell
git init
git add .
git commit -m "Open source Prism Layer Studio 2.6.0"
git branch -M main
git remote add origin https://github.com/<你的用户名>/<你的仓库名>.git
git push -u origin main
```

这里的占位 URL 不是已经创建的远程地址。本地整理工作不会自动创建 GitHub 仓库，也不会自动向任何账号上传文件。

## 2. 源码与下载文件分开存放

不要向 Code 页面上传 `release/`、`.venv-build/`、`.tools/`、构建缓存、测试导出、安装 EXE 或微软运行时安装器。本目录的 `.gitignore` 已用于排除这些内容。

本次离线安装包约 230 MB，超过 GitHub 普通 Git 仓库的单文件限制。GitHub 官方说明：网页上传单文件不得超过 25 MiB，普通 Git 仓库阻止超过 100 MiB 的文件；大型可下载二进制适合通过 Releases 分发。参见 [GitHub 大文件说明](https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github)。

源码仓库保留依赖版本、下载 URL、SHA-256 和签名验证脚本，构建时再准备第三方二进制。不要为了上传安装包而把大型 EXE 强行加入 Git 历史。

## 3. 创建 v2.6.0 Release

在 GitHub 仓库的 **Releases → Draft a new release** 中：

1. 选择或创建标签 `v2.6.0`，目标选择本次源码所在分支。
2. 标题填写 `Prism Layer Studio 2.6.0`。
3. 填写软件功能、支持平台、安装步骤和已验证范围。
4. 在附件区域上传构建后的 `release/` 中的 `PrismLayerStudio-Setup.exe`、`PrismLayerStudio-2.6.0-Portable-Offline-x64.zip`，并附上对应文件校验值、测试报告及本项目 `LICENSE`。新的开源构建已将 MIT 许可证加入 EXE、安装目录和便携包；如复用开源前生成的旧安装附件，请同时分发 `LICENSE`。
5. 确认附件完整后发布 Release，再把仓库首页的 Releases 入口或该版本链接分享给同事。

GitHub 自动生成的 Source code ZIP/TAR 只提供源码，不能替代安装程序。用户下载 Setup 后按向导安装；下载便携 ZIP 后完整解压再运行。

可使用以下发布说明：

```text
Prism Layer Studio 2.6.0

STAR-CCM+ 棱柱层网格初始设计辅助工具，支持正向设计、反求层数/增长率、实测 Wall Y+ 校准、翼型局部近似、CSV/JSON 导出。

平台：Windows 10 1809+ / Windows 11 x64。
安装版内含微软 WebView2 完整离线安装器；最终用户不需要 Python。
程序与计算完全在本地运行。

验证：已在 Windows 11 本机完成安装、运行、卸载和打包 EXE 检查。
Windows 10 干净系统、完全缺失 WebView2 的首次安装及系统级 DPI 切换仍需进一步验收。

项目自有代码采用 MIT License，第三方依赖按各自许可证分发。
```

## 4. 以后更新

修改代码后先运行适当测试，再重新构建主 EXE 和 Setup，更新版本号、变更说明、测试报告及校验值。为新版本创建新标签和 Release；保持标签对应源码与附件版本一致。

MIT 许可允许他人使用和修改项目，但第三方依赖、商标和软件组件仍遵循各自许可。项目的完整自有代码许可见根目录 `LICENSE`。
