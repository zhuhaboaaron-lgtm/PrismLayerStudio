# 历史网页版说明（原交付 README）

以下为桌面封装前随 v2.6 ZIP 提供的历史说明，仅作版本记录；当前桌面发行以 README.md、BUILD_GUIDE.md 和实际测试报告为准。历史文字提及的 legacy 目录、私有上传脚本和开发提示不属于此公开仓库；自有项目内容的现行许可为根目录 MIT LICENSE。

# Prism Layer Studio v2.6 · 物性下拉菜单视觉升级

- “物性预设”由浏览器默认展开列表升级为分组式自定义弹出面板，包含材料图标、温度、密度/黏度参考值、当前选项标记和鼠标悬停高亮。
- 保留真实 `<select id="preset">` 作为数据层；原有自动填充物性和计算监听器不变。用户直接编辑密度/粘度时自动切换到“自定义”，重置会同步恢复“空气 25°C”。
- 键盘支持方向键、Home/End、Enter/空格、Escape；焦点、ARIA 和窗口宽度适配；关闭动画遵循 `prefers-reduced-motion`。
- 不依赖网络/字体 CDN，不改物理模型公式；其他界面组件保留。页面运行和打包方式同 v2.5。

> v2.5 变化：数学模型与公式现在默认折叠，点击条目可展开；保留 MathML 排版与公式适用范围说明。

# v2.4 · 学术数学公式区排版升级

- 直接修改 `app/index.html` 与 `app/style.css`，将第 06 节 4 组共 15 条公式重新排版。
- **等号与近似号纵向对齐**：左侧变量、关系运算符、右侧表达式使用 3 列网格定位。
- **大尺寸显示公式**：以 MathML `mstyle displaystyle=true` 展示更清晰的根号、分数线、求和符号与上下标；系统数学字体优先 Cambria Math / STIX，离线可运行。
- 调整卡片标题、分隔线、公式留白、行高、深蓝背景和青绿色关系符号；保留术语及公式适用条件。
- 响应式适配 320、390、870、1280、1510px；针对狭窄手机上的 Petukhov 长公式单独压缩字号，避免横向截断。
- 物理计算内核、棱柱层交互效果和 CSV/JSON 导出不变。
- 在当前 Chromium 中检查了实际公式排版和控制台错误；原有 13 项 JS 计算测试和 1 项 Python 服务器测试通过。

# v2.3 · 论文式公式与简化主页

- 已直接修改 `app/index.html` 和 `app/style.css` / `app/hero.css`，删除主页左下角的“DESIGN · SIMULATE · VERIFY — 鼠标移动 / 点击模型可交互”和“02 / 06”装饰性页码。模型仍可以鼠标移动、点击、键盘切层。
- 第 06 节更改为浏览器原生 **MathML**，15 条核心公式使用真实分式、上下标、根号与大求和符号，不再使用字符模拟排版。
- 四组公式为首层厚度、层厚分布、平板外流、光滑圆管；必要工程条件和使用假设归入可展开的“公式假设与适用范围”，避免影响数学排版，同时保留科学严谨性。
- 完全离线，无需 MathJax / KaTeX CDN。现代 Chrome/Edge 可原生显示 MathML；在过旧的内嵌浏览器（如旧版 WebView2）需更新浏览器运行时。
- 启动方式不变。直接打开 `publish/index.html` 为单文件网站；源文件在 `app/`；Windows `.exe` 构建脚本保留。
- 未修改任何物理模型的计算逻辑，只改公式展示与主页装饰文案。

## v2.2 — 鼠标响应式交互工作台（新增）

本版本在 v2.1 全部工程计算功能基础上增加了**真正可交互**的 SVG 棱柱层主页：

- 鼠标移动会形成随位置变化的局部发光揭示区，整个模型有小幅平滑的视差倾斜。
- 点击模型任意位置，按最近的可视层选中，并显示具体层号与 **预测** 单层厚度；再次点击会重新选层，有波纹反馈。
- 箭头键可以切换层（需先聚焦模型容器），按钮可暂停或启用动效；支持 `prefers-reduced-motion` 和触摸点击。
- 修改层数、增长率或其他计算参数后，模型从真实计算结果重建；对 16 层以上的设计，显示的是**合并后的代表性视觉层**，探针数值仍来自对应真实层。
- 滚动进入工作台时，参数卡片和结果面板轻柔显现；网页离线无 CDN 依赖，可继续用于 Windows pywebview `.exe` 封装。
- 主页模型为**艺术化 2.5D 示意**，不表示真实 CFD 网格质量，不是 WebGL 完整 3D 模型，也并非 Lando Norris 网站头盔的复制品。

进入 `publish/index.html` 即可使用单文件交互版；开发源码在 `app/hero.css` 和 `app/hero.js`。若要向 Norris 官方站的液体揭示/真实 3D 深度进一步靠近，见 `CODEX_PROMPT_INTERACTIVE.md`。

# Prism Layer Studio v2.1 · STAR-CCM+ 棱柱层网格设计辅助工具

中文离线工具：由目标 `y+` 估计近壁首层厚度；输入 `N, r` 算总厚度；根据目标厚度**反求最少整数层数**或**增长率**；根据实际求解的局部 Wall Y+ **校准首层厚度**；提供**机翼弦向局部平板近似**、圆管 Fanning 摩擦系数、图表、CSV/JSON、STAR-CCM+ 分布模式提示。

## v2.1 视觉更新

- 工程工作台视觉：深海蓝 / 石墨灰基础配色，薄荷青与冷蓝强调，首层 / 总厚度突出，新增页面顶部棱柱层示意图及状态栏。
- 图表采用局部渐变柱形和累计曲线端点标记，统一卡片、表格与 STAR-CCM+ 参数块样式，并优化手机端响应布局。
- 新增 `assets/prism-layer-studio.ico` 与 `.png`，可用于 Windows 桌面图标。
- 面向 Codex 的完整可复制提示词：[`CODEX_PROMPT_READY.md`](CODEX_PROMPT_READY.md)。
- 原有科学计算模型未修改，仍需 Windows/WebView2 下的桌面和视觉实测验证；本环境未能成功运行浏览器截图测试。

## 选择一种运行方式

### A. 无安装网页版（最快）

直接双击 `app/index.html` 或 `publish/index.html`（**单文件版**），无需 Python 和网络。现代 Chrome/Edge 均可运行；所有运算在本机进行。也可在 Windows 上双击根目录的 `启动网页版.bat`（需要已安装 Python 3.11+）。

### B. Windows 独立桌面 EXE（推荐最终交付）

在 Windows 10/11、安装 Python 3.11 或以上版本的电脑上：

1. 将整个 ZIP 解压到普通文件夹。
2. 双击 `scripts/build-windows-desktop.bat`。首次打包会通过 pip 下载 **PyInstaller 和 pywebview**，需要联网。
3. 打包成功后得到 `dist/PrismLayerStudio.exe`，可以复制到其他 Windows 电脑使用，**无需另装 Python**。
4. 运行环境可能需要 Windows Edge WebView2 Runtime（Windows 11 通常已有），不是“零系统依赖”。打包和运行需要在 Windows 上验证。

> 当前提供的是**完整源代码 + 构建脚本**；没有在本环境内跨平台伪造 Windows `.exe`。PyInstaller 通常须在目标 Windows 环境构建 Windows EXE。

如果 pywebview 环境配置失败，可改双击 `scripts/build-windows-browser.bat`，获得 `dist/PrismLayerStudioBrowser.exe`。该版本直接打开系统浏览器，关闭控制台窗口即停止服务，软件运行时不需要 Python。

### C. 通过 MATLAB 运行同一个工具

在 MATLAB 命令行中运行：

```matlab
addpath('D:\YourPath\PrismLayerStudio\matlab')
PrismLayerStudio
```

此方式只是从 MATLAB 打开同一个离线 HTML 工具，并**不是**真正原生的 `.mltbx` 或 App Designer 工具箱。完整说明在 `matlab/README.md`。将来如需纯 MATLAB 原生计算内核与 `.mltbx`，需要单独移植并用本机 MATLAB 封装和验证。

## 升级内容（相对 legacy 的原始文件）

- 平板采用**局部** `Cf,x=0.664/sqrt(Re_x)`（层流）或 `Cf,x=0.0592/Re_x^0.2`（全湍流），不再用 `5e5` 当作全局硬切换来假定转捩。
- 转捩参考提供层流/全湍流估算端点，**不声称自动求解转捩**。
- 光滑圆管在 `Re<2300` 用 `Fanning Cf=16/Re`；`2300≤Re<4000` 要求手工输入 Fanning Cf；`4000≤Re≤100000` 用 Blasius；高雷诺数用 Petukhov 近似，并标注适用限制。
- 以 `w=2*y+*mu/(rho*u_tau)` 估算近壁首层完整厚度，并不声称已获得真实 STAR-CCM+ Wall Y+。
- 在 `r=1`、`r≈1` 的计算中避免 `(r^N-1)/(r-1)` 消差；层数取整，增长率以二分法求解。
- 增加 N/r/总厚度反求、实测 Wall Y+ 校准、局部位置 `x/L`、翼型表面标记、末层/核心尺寸比。
- 输出标准 Prism Layer Mesher 与 Advancing Layer Mesher 两种配置路径的**差异化说明**，不要求同时启用；按版本确认具体节点。
- 切换动态/运动粘度时自动保持物理数值不变；在界面错误时清空过期结果；提供适合粘贴的 `1.234e-5` 科学记数法。
- 浏览器前端不依赖 CDN；服务器默认仅绑定 `127.0.0.1`，不公开程序目录外文件。

## 计算假设与重要边界

- 固定物性、稳态经验摩擦关系；`u_tau = U sqrt(Cf/2)`，其中外流是**局部表面摩擦系数**，内流是 **Fanning** 而不是 Darcy。
- 近壁质心假定距墙 `w/2`，非结构/折叠/曲面网格会偏离这一近似。面积均值和局部 Wall Y+ 不可随意混用。
- 翼型模式将 `x/c` 作为局部计算长度，只能做平板估算，未建立真实翼型压力梯度、转捩、吸力面/压力面不同摩擦应力。需要 CFD 求解迭代。
- `δ99` 只是平板相关式参考；不是必须强制达到的 Prism Layer 总厚度。检查网格收缩、单元质量、最后一层和核心单元的尺寸衔接。
- 校准公式 `w_new=w_old*(y+_target/y+_observed)` 是一次线性近似，**不能**代替实际重新划分网格、重新计算流场和复测。
- 近壁与壁面函数的 `y+` 适用范围依赖 STAR-CCM+ 湍流模型及 Wall Treatment；不能把 5–30 固定称为所有壁面处理的禁区。

## 检验方法

运行 Node.js 核心公式测试：

```bash
node --test tests/core.test.cjs
```

运行 Python 静态服务器测试：

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

在目标 Windows 电脑上做额外冒烟测试：成功构建 EXE、能启动桌面窗口、切换全部计算模式、导出 CSV/JSON、退出后本地端口释放；对比真实 STAR-CCM+ 结果。

## 目录结构

```
app/                     网页完整代码，可离线直接打开
  index.html              用户界面
  style.css               主题样式
  core.js                 纯物理公式与反求算法（Node 测试）
  app.js                  前端交互、曲线与导出
server.py                 标准库本地 Web 服务器
runtime.py                仅提供 app/ 目录的静态服务
desktop.py                pywebview 原生桌面窗口入口
scripts/                  两种 Windows EXE 构建脚本
matlab/                   MATLAB 打开工具的启动入口（非真正 .mltbx）
tests/                    核心数值与服务器测试
legacy/                   用户原始文件，供 Codex 核对或回滚
publish/index.html        生成的单文件离线版，可部署到 Gitee Pages
CODEX_TASK.md             面向 Codex 的下一轮迭代任务说明
```

## 参考文档

- STAR-CCM+ Prism Layer Mesher: https://www.tech-doc.cn/wp-content/uploads/Free/StarCCM2406/GUID-4B9B4787-0BEF-4DC6-834D-59346F0C8316.html
- STAR-CCM+ Advancing Layer Mesher Reference: https://www.tech-doc.cn/wp-content/uploads/Free/StarCCM2406/GUID-1BF4D262-B64E-4A4E-AC10-B2DA8AD87EBF.html
- NASA Turbulence Modeling Resource: https://turbmodels.larc.nasa.gov/

本软件输出用于网格初始设计，不是 STAR-CCM+ 自动建模、宏命令或求解器验证，也不保证 CFD 收敛或目标精度。

## Gitee Pages 发布（单文件兼容原项目）

`publish/index.html` 已将 CSS 与 JS 内联为单文件，可作为网站根目录 `index.html` 上传到 Gitee Pages/GitHub Pages。若继续使用旧 Gitee 发布脚本，请确认令牌、仓库名及分支设置适合你的仓库；不要把令牌提交到公开仓库。本工具未自动向任何远程仓库推送。
