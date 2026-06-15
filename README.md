# TypeRed — Markdown Reader & Editor 😊📖

[![GitHub Release](https://img.shields.io/github/v/release/JiaHuiRed/TypeRed?label=版本&color=blue&logo=github)](CHANGELOG.md)
[![平台](https://img.shields.io/badge/平台-Windows%2010%2F11-0078d7?logo=windows&logoColor=white)](README.md)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776ab?logo=python&logoColor=white)](README.md)
[![许可证](https://img.shields.io/badge/许可证-MIT-lightgrey)](LICENSE)

> 贫穷的我用来替代 Typora 的轻量级 Markdown 阅读器 ✨

---

## 📖 简介

TypeRed 是一个轻量级本地 Markdown 阅读 / 编辑器，基于 **PySide6 + QWebEngineView**，用 **mistune** 代替 `python-markdown` 实现 5-10x 渲染加速。

支持原生毛玻璃窗口（桌面壁纸穿透）、XMind 思维导图、5 种主题、分屏编辑、实时预览、语法高亮。

## ✨ 特色

- **毛玻璃窗口** — `WA_TranslucentBackground` 实现桌面壁纸穿透，标题栏/搜索栏/状态栏半透明
- **mistune 渲染引擎** — 原生 C 扩展加速，大文件渲染 5-10x 提升
- **XMind 思维导图** — 打开 `.xmind` 文件自动解析为 Markdown 渲染，支持 Zen JSON + 旧版 XML
- **5 种主题** — 默认 / 护眼 / 米黄 / 深蓝 / 夜间
- **自动目录** — h2-h4 级标题自动生成侧边栏 TOC，可拖拽调整宽度
- **代码高亮** — Pygments 语法高亮，跟随主题色
- **分屏编辑** — `Ctrl+E` 切换编辑模式，400ms 实时预览 + 同步滚动
- **格式快捷键** — 粗体/斜体/删除线/高亮/上下标/标题/列表
- **猫猫动画** — 打字时猫猫弹跳，空闲时 GIF 循环
- **Emoji 短代码** — `:smile:` → 😄、`:rocket:` → 🚀，完整 emoji 词汇表支持
- **智能排版** — `...` → …、`--` → —、`->` → → 等，代码块内不受影响
- **图片点击放大** — 全屏遮罩查看原图，ESC/点击关闭，毛玻璃背景
- **缩写支持** — `*[HTML]: ...` 语法自动转为 `<abbr>` 标签
- **可点击任务列表** — `- [ ]` 复选框支持点击切换
- **macOS 交通灯** — 红黄绿关闭/最小化/最大化按钮 + 无边框窗口缩放
- **多标签页** — 同时打开多个文件，标签页拖拽排序、红色圆点关闭
- **Ctrl+N 新建文件** — 快速创建空白 untitled 文件，自动进入编辑模式
- **常驻状态栏** — 始终显示行数、文件大小、词数、字符数，不再一闪而过

## 🖥️ 环境要求

| 项目 | 要求 |
|------|------|
| 操作系统 | Windows 10 / 11（64 位） |
| Python | 3.10 或更高 |
| Visual C++ | [Microsoft Visual C++ Redistributable](https://aka.ms/vs/17/release/vc_redist.x64.exe) |

> 如果报 `DLL load failed`，通常是缺少 VC++ Redistributable。

## 🚀 快捷使用

```bash
pip install -r requirements.txt
python main.py                          # 打开应用
python main.py path/to/file.md          # 直接打开文件
python main.py path/to/file.xmind       # 打开思维导图
```

## 📦 打包 exe

```bash
build.bat
```

输出 `dist/TypeRed.exe`（单文件，无需 Python 环境）。首次需要 `pip install pyinstaller`。

## ⌨️ 快捷键

| 快捷键 | 功能 |
|--------|------|
| `Ctrl+N` | 新建文件 |
| `Ctrl+O` | 打开文件 |
| `Ctrl+S` | 保存 / 另存为 |
| `Ctrl+R` | 重新加载文件 |
| `Ctrl+P` | 导出 PDF |
| `Ctrl+E` | 切换编辑 / 阅读模式 |
| `Ctrl+T` | 循环切换主题 |
| `Ctrl+F` | 搜索 |
| `Ctrl+H` | 查找替换（编辑模式） |
| `Ctrl+Shift+T` | 插入表格 |
| `Alt+←` / `Alt+→` | 导航历史 |
| `Ctrl+1`~`Ctrl+6` | 标题 h1~h6 |
| `Ctrl+B` | 粗体 |
| `Ctrl+I` | 斜体 |
| `Ctrl+Shift+S` | 删除线 |
| `Ctrl+Shift+H` | 高亮 |
| `Ctrl+Shift+P` | 上标 |
| `Ctrl+Shift+B` | 下标 |
| `Ctrl+Shift+U` / `Ctrl+Shift+O` | 无序/有序列表 |
| `Tab` / `Shift+Tab` | 缩进 |

## 📜 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| 0.7.0 | 2026-06-09 | 多标签页 / Ctrl+N 新建文件 / 常驻状态栏 / 红色圆点关闭按钮 |
| 0.6.5 | 2026-06-08 | Emoji短代码 / 智能排版 / 图片放大 / 缩写 / 可点击任务列表 |
| 0.6.4 | 2026-06-01 | 修复mistune HTML转义，支持details折叠 |
| 0.6.3 | 2026-06-01 | 搜索栏移至标题栏下方 |
| 0.6.2 | 2026-06-01 | 真毛玻璃 / 6px 滚动条 / TOC blur |
| 0.6.1 | 2026-06-01 | XMind 思维导图支持 |
| 0.6.0 | 2026-06-01 | mistune 渲染引擎 / 自定义 TOC |
| 0.5.6 | 2026-05-28 | 提取前端资源 / 监听器去重 |
| 0.5.5 | 2026-05-27 | Toast / 未保存提醒 / 搜索增强 |
| 0.5.4 | 2026-05-26 | 启动速度优化 / PyInstaller 启动屏 |
| 0.5.3 | 2026-05-25 | 猫猫动画 / 同步滚动 / macOS 滚动条 |
| 0.5.2 | 2026-05-23 | 修复目录锚点跳转 |
| 0.5.1 | 2026-05-22 | 修复右侧缩放与滚动条重叠 |
| 0.5.0 | 2026-05-21 | 行号 / 自动保存 / TOC 调宽 |
| 0.4.6 | 2026-05-20 | 链接拦截 / Alt 导航 |
| 0.4.5 | 2026-05-19 | 修复窗口尺寸 |
| 0.4.4 | 2026-05-19 | 绿灯还原 / 任务栏最小化 |
| 0.4.3 | 2026-05-19 | 任务栏图标支持 |
| 0.4.2 | 2026-05-19 | 修复 BOM 文件标题渲染 |
| 0.4.1 | 2026-05-19 | 修复打开方式启动 |
| 0.4.0 | 2026-05-19 | 查找替换 / 图片拖入 / 表格对话框 |
| 0.3.3 | 2026-05-19 | 纯 Qt 边缘缩放 |
| 0.3.2 | 2026-05-18 | pygments 缓存 / 字数统计 |
| 0.3.1 | 2026-05-18 | 欢迎页 / 修复代码围栏 |
| 0.3.0 | 2026-05-18 | 编辑模式 / 实时预览 |
| 0.2.0 | 2026-05-18 | 最近文件 / 自动刷新 / PDF |
| 0.1.0 | 2026-05-18 | 5主题 / 交通灯 / 改名 TypeRed |
| 0.0.1 | 2026-05-18 | 初始版本 |

> 完整变更日志参见 [CHANGELOG.md](CHANGELOG.md)。

## 📏 版本规则

- 小改动：`0.0.x`（bug 修复、细节调整）
- 中改动：`0.x.0`（新功能、较大改动）
- 大改动：`x.0.0`（架构重构、重大更新）
