# MATLAB 调用入口

此目录提供可在 MATLAB 命令行调用的独立网页工具入口（**不是**已经打包的 `.mltbx`）。保留整个 `PrismLayerStudio` 文件夹，再在 MATLAB 输入：

```matlab
addpath('D:\YourPath\PrismLayerStudio\matlab')
PrismLayerStudio
```

网页计算引擎仍为 `app/core.js`，MATLAB 启动器只负责打开它，因此网页版、Windows .exe 和 MATLAB 打开的是同一套前端算法。无需编写两套不同的物理公式。

如需真实 MATLAB 工具箱文件，需在已安装 MATLAB 的 Windows 机器上利用 **Package Toolbox** 将此目录和依赖的 `app/` 资源一起打包，并处理相对路径。推荐优先使用 Windows EXE，部署更简单。
