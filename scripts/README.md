本文件夹下是构建汉化补丁所用的脚本。

构建脚本使用 [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html) 协议发布。

## 构建准备

- [Python 3.12+](https://www.python.org/downloads/)（`pip install -r requirements.txt`）
- [PowerShell 5.0+](https://learn.microsoft.com/powershell/)
- [devkitPro、devkitARM](https://devkitpro.org/wiki/Getting_Started)（`dkp-pacman -Sl nds-dev`）
- 字体文件（默认读取以下文件：`files/fonts/Zfull-GB.ttf`、`C:/Windows/Fonts/simsun.ttc`）

## 构建脚本

导航到项目根目录，然后在 PowerShell 中运行：

```shell
. scripts\build_patch.ps1
```

构建后的补丁路径为 `out/patch-ds.xzp`。
