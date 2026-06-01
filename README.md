# 📝 TypeRed — Markdown Reader & Editor

[![GitHub Release](https://img.shields.io/github/v/release/JiaHuiRed/TypeRed?label=版本&color=blue&logo=github)](CHANGELOG.md)
[![平台](https://img.shields.io/badge/平台-Windows%2010%2F11-0078d7?logo=windows&logoColor=white)](README.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](README.md)
[![许可证](https://img.shields.io/badge/许可证-MIT-lightgrey)](LICENSE)

作者：Red


> 贫穷的我用来替代 Typora 的轻量级 Markdown 阅读器 ✨

---

## 🌟 简介

TypeRed 是一个轻量级本地 Markdown 阅读 / 编辑器，基于 PySide6 + QWebEngineView，渲染效果接近 GitHub 风格。

![预览截图](docs/preview.png)

> 截图待补充

## ✨ 功能

- 📂 打开 / 拖拽 `.md` / `.markdown` / `.mdown` / `.txt` / `.xmind` 文件（思维导图自动转 Markdown 渲染）
- 🎨 5 种主题：默认 / 护眼 / 米黄 / 深蓝 / 夜间
- 🌲 自动生成目录（左侧可点击跳转）
- 💻 代码块语法高亮（Pygments）
- ✏️ 分屏编辑 + 400ms 实时预览 + 行号显示（`Ctrl+E`）
- 🔠 Markdown 格式快捷键：粗体 / 斜体 / 删除线 / 高亮 / 上下标 / 标题 / 列表
- 🔍 查找（`Ctrl+F`）/ 查找替换（`Ctrl+H`，仅编辑模式）+ 大小写/全词匹配
- 🔗 文档内 `.md` 链接直接渲染，外链自动用浏览器打开
- ⬅️ `Alt+←` / `Alt+→` 导航历史前进后退
- 📋 插入表格对话框（`Ctrl+Shift+T`）
- 🖼 编辑模式下拖入图片自动插入 `![]()` 语法
- 💾 `Ctrl+S` 保存弹出 Toast 提示，关闭/切换文件时自动检查未保存更改
- 🐱 猫猫打字动画（左侧/预览区弹跳 + GIF 循环）
- 🎯 编辑/预览同步滚动（光标位置自动对齐预览）
- 🪟 macOS 风格交通灯 + 无边框窗口（全边缘可拖拽缩放）
- 📌 最近文件、自动重载、自动保存（30s）、导出 PDF、记忆窗口位置和主题
- 📐 TOC 侧边栏可拖拽分隔线调整宽度

## 🖥 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| Python | 3.10 或更高 |
| Visual C++ | [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe)（PySide6 / QtWebEngine 依赖） |

> 如果运行时报 `DLL load failed`，通常是缺少 VC++ Redistributable，安装后重试即可。

## 🚀 使用方法

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py

# 直接打开指定文件
python main.py path/to/file.md
```

## 📦 打包为 exe

```bash
build.bat
```

会自动生成图标并调用 PyInstaller，输出 `dist/TypeRed.exe`（单文件，无需 Python 环境）。

> 首次打包需要安装 PyInstaller：`pip install pyinstaller`

## ⌨️ 快捷键

| 快捷键              | 功能                                         |
|---------------------|----------------------------------------------|
| `Ctrl+O`            | 打开文件                                     |
| `Ctrl+S`            | 保存 / 另存为                                |
| `Ctrl+R`            | 重新加载当前文件                             |
| `Ctrl+P`            | 导出 PDF                                     |
| `Ctrl+E`            | 切换编辑 / 阅读模式                          |
| `Ctrl+T`            | 循环切换主题（5 种）                         |
| `Ctrl+F`            | 搜索（阅读模式=页内，编辑模式=编辑区）       |
| `Ctrl+H`            | 查找替换（仅编辑模式）                       |
| `Alt+←` / `Alt+→`  | 导航历史后退 / 前进                          |
| `Ctrl+滚轮`         | 缩放预览区                                   |
| `Ctrl+B`            | 粗体（编辑模式）                             |
| `Ctrl+I`            | 斜体（编辑模式）                             |
| `Ctrl+Shift+S`      | 删除线（编辑模式）                           |
| `Ctrl+Shift+H`      | 高亮（编辑模式）                             |
| `Ctrl+Shift+P`      | 上标（编辑模式）                             |
| `Ctrl+Shift+B`      | 下标（编辑模式）                             |
| `Ctrl+1` ~ `Ctrl+6` | H1 ~ H6 标题（编辑模式）                   |
| `Ctrl+0`            | 取消标题（编辑模式）                         |
| `Ctrl+Shift+U`      | 无序列表（编辑模式）                         |
| `Ctrl+Shift+O`      | 有序列表（编辑模式）                         |
| `Ctrl+Shift+T`      | 插入表格（编辑模式）                         |
| `Tab` / `Shift+Tab` | 缩进 / 取消缩进（编辑模式）                  |

## 📋 版本历史

| 版本  | 日期       | 说明                                                              |
|-------|------------|-------------------------------------------------------------------|
| 0.6.1 | 2026-06-01 | XMind 思维导图支持（Zen+XML 格式）/ 思维导图模式 CSS 层级颜色   |
| 0.6.0 | 2026-06-01 | mistune 渲染引擎替换（5-10x 加速）/ 自定义 TOC + 代码高亮渲染器   |
| 0.5.6 | 2026-05-28 | 提取JS和欢迎页到frontend目录 / 文件监听器去重                     |
| 0.5.5 | 2026-05-27 | 保存Toast/未保存提醒/搜索大小写全词/性能优化/猫猫GIF打包修复      |
| 0.5.4 | 2026-05-26 | 启动速度优化(QWebEngineView延迟创建+重型导入按需加载)/PyInstaller启动屏 |
| 0.5.3 | 2026-05-25 | 猫猫打字动画/编辑预览同步滚动/macOS滚动条/启动速度优化             |
| 0.5.2 | 2026-05-23 | 修复正文目录锚点无法跳转（JS优先preventDefault + Python同文件fragment检测） |
| 0.5.1 | 2026-05-22 | 修复右侧边缘缩放与 WebView 滚动条重叠（右侧检测边距缩小至 4px）   |
| 0.5.0 | 2026-05-21 | 行号显示/自动保存30s/TOC拖拽调宽/性能优化/修复左下角缩放/修复保存触发重载 |
| 0.4.6 | 2026-05-20 | 链接拦截渲染/外链浏览器/Alt导航/修复HTML块渲染                    |
| 0.4.5 | 2026-05-19 | 修复启动尺寸过大/保存最大化前尺寸/默认缩小      |
| 0.4.4 | 2026-05-19 | 修复绿灯还原尺寸/任务栏最小化生效               |
| 0.4.3 | 2026-05-19 | 任务栏图标支持切换最小化/还原/绿灯最大化还原    |
| 0.4.2 | 2026-05-19 | 修复含BOM的UTF-8文件首行标题无法渲染            |
| 0.4.1 | 2026-05-19 | 修复右键"打开方式"启动时显示欢迎页而非目标文件  |
| 0.4.0 | 2026-05-19 | 查找替换/图片拖入插入/插入表格/启动速度优化     |
| 0.3.3 | 2026-05-19 | 纯Qt边缘缩放/修复Win11无边框窗口无法调整大小    |
| 0.3.2 | 2026-05-18 | pygments缓存/字数统计/编辑模式Ctrl+F            |
| 0.3.1 | 2026-05-18 | 欢迎页详细化/修复代码围栏嵌套渲染              |
| 0.3.0 | 2026-05-18 | 编辑模式/实时预览/格式快捷键/上下标高亮渲染    |
| 0.2.0 | 2026-05-18 | 最近文件/自动刷新/页内搜索/导出PDF/记住窗口    |
| 0.1.0 | 2026-05-18 | 5主题/macOS交通灯/程序化图标/改名TypeRed       |
| 0.0.1 | 2026-05-18 | 初始版本                                        |


> 完整变更日志参见 [CHANGELOG.md](CHANGELOG.md)。

## 📐 版本规则

- 小改动：`0.0.x`（bug 修复、细节调整）
- 中改动：`0.x.0`（新功能、较大改动）
- 大改动：`x.0.0`（架构重构、重大更新）
