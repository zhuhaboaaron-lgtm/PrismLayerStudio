# GitHub Actions 验证范围

`workflows/tests.yml` 在 push、pull request 或手动运行时，在 GitHub 托管 Windows runner 中使用 Python 3.13 x64、Node.js 24 和固定 Python 依赖执行 `test.bat`。

运行范围包括原有 13 项 JavaScript 数值测试，以及 Python 的源文件完整性、离线资源、HTTP 边界和原生 I/O 合同测试。托管 CI 设置 `PRISM_STUDIO_CI=1`，跳过依赖交互桌面的真实 Windows 剪贴板测试；本机直接执行 `test.bat` 时仍启用它。

此工作流不启动 EXE、不修改 Windows 显示缩放、不安装或卸载应用，也不发布 Release。完整 WebView2、剪贴板、DPI 和安装验收应按照 [BUILD_GUIDE.md](../BUILD_GUIDE.md) 在实际 Windows 桌面完成。历史本机报告不能替代当前 GitHub Actions 的运行结果；本仓库整理时尚未在 GitHub 执行该工作流。

工作流仅授予 `contents: read`，检出时不保留凭据，不使用仓库密钥。官方 action 均固定到完整 commit SHA；以下映射已在 2026-11-05 通过官方仓库 GitHub API 核对：

- [actions/checkout v5](https://github.com/actions/checkout/commit/fbc6f3992d24b796d5a048ff273f7fcc4a7b6c09)
- [actions/setup-python v6](https://github.com/actions/setup-python/commit/ece7cb06caefa5fff74198d8649806c4678c61a1)
- [actions/setup-node v6](https://github.com/actions/setup-node/commit/249970729cb0ef3589644e2896645e5dc5ba9c38)

升级 action 时，先核对官方版本、完整 SHA、runner 和 Node.js 最低要求，再更新工作流。不要用来自 issue 或未经核实评论的 action 引用替换这些固定值。
