# Changelog

所有重要变更记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.8.0] - 2026-08-28

> 五套主题可读性对比度全线达标 + 代码块复制按钮 + 窄宽自适应 + 搜索栏懒加载期崩溃修复

#### 新增

- **代码块头部条**：左侧显示语言标签，右侧「复制」按钮，点击复制原始代码并短暂反馈「已复制」。事件委托挂在 `#content` 上，兼容大文档的渐进分块加载；`navigator.clipboard` 不可用时退回 `execCommand`。头部背景与分隔线用 `--text` 混合而非 `--th-bg` —— 代码区背景由 Pygments 主题决定，与 `--th-bg` 会撞色，涉及 `main.py:207`、`frontend/style.css:292`、`frontend/script.js:120`
- **窄宽自适应**：720px / 480px 两级断点收窄正文 padding（48px → 24px → 16px）与 TOC 宽度（220px → 168px → 140px）。编辑模式下预览区常只有 400-500px，原先双侧 96px 留白吃掉两成宽度，涉及 `frontend/style.css:493`
- **可访问性基础**：`:focus-visible` 覆盖正文/TOC 链接、任务列表复选框、复制按钮；QSS 补 `QPushButton:focus`（自定义 border 原会顶掉 Qt 默认焦点框）。新增 `prefers-reduced-motion` 兜底，CSS 过渡/动画降级、JS 锚点滚动退回 `auto`

#### 修复

- **搜索栏在 WebView 懒加载期崩溃**：`SearchBar(self, self)` 第二参签名是 `view` 却传了窗口自己，`_view` 指向窗口导致 `findText` 分支抛 `AttributeError`。无文件启动后 600ms 内按 Ctrl+E / Ctrl+F 必崩；改由 `_ensure_view()` 的 `set_view()` 注入，涉及 `main.py:1502`
- **状态栏统计陈旧**：`_update_status_bar` 只读 `self._current_text`，而它仅在 load/save/切标签时更新 —— 编辑时行数/词数/字符数卡在上次保存值，新建文档一直停在欢迎语。编辑模式改读 `editor.toPlainText()`
- **主题圆点看不出选中**：选中环原用白色，浅色三套主题下对比仅 1.08/1.19/1.31，等于不可见；改按主题取对比色（`THEME_RING`，最低 6.42）。原本用来补救的 `box-shadow` 那行 QSS 不支持，从未生效，一并删除
- **交通灯按下无反馈**：`pressed` 用 `opacity`，QSS 同样不支持；改为实色深浅并补 hover 态
- **「编辑」按钮激活态在深色主题下发暗**：文字色硬编码 `#3a5ad4`，叠在深色标题栏上只有 2.47/2.72；改按主题取（`THEME_EDIT_ACTIVE`，最低 5.57）。顺带修编辑模式下切主题会被 `apply_theme` 的普通样式顶掉激活态
- **暗色/夜间正文次要文字偏灰**：`--text-muted` 为 4.18/3.45（侧栏底上 4.37/3.29），而 TOC 全部链接、引用块、脚注、h5/h6 都吃这个变量；提到 6.16/5.73
- **标题栏按钮边框看不出是按钮**：五套主题 1.79-2.83，全部低于 WCAG 1.4.11 的 3:1；提到 3.19-3.86
- **行号灰得过头**：2.04-2.9，比主流编辑器灰不少；提到 3.10-3.74
- **宽表格撑破正文布局**：根因是 `#content` 作为 flex item 的 `min-width:auto` 被内容撑开，`table` 自身的 `overflow-x` 因此形同虚设。补 `min-width:0` 后表格改为内部滚动（470px 视口实测整页不再横向滚动）
- **TOC 长标题截断后无从得知全文**：`text-overflow:ellipsis` 之外补 `title` 属性（剥内联标签），涉及 `main.py:245`
- **图片放大遮罩关闭按钮**：由 `span` 改 `button`（键盘可达），加圆形半透明衬底，避免白色叉号落在浅色图片上不可见
- **资源读盘缓存失败后反复重试**：`_CSS_CACHE`/`_JS_CACHE` 原先判空字符串，读盘失败即每次 `build_page` 都重试磁盘；改 `None` 哨兵
- **后台渲染异常消息未转义**：worker 的异常文本直接拼进 HTML，改 `html.escape`

#### 重构

- 删死代码：`_smart_split_markdown`（23 行无调用）、两处恒假 `isinstance(toc, list)`、一处恒真 `hasattr(self, '_autosave_mtime')`

---

## [0.7.12] - 2026-08-28

> 编辑器行号区压字修复 + 渲染线程安全 + 外部修改提示可靠性 + 死代码清理

#### 修复

- **行号区压住正文行首**：`blockSignals(True)` 包裹 `setPlainText` 会连 `blockCountChanged` 一起屏蔽，`viewportMargins` 停在旧行数算出的宽度，而行号区 geometry 在 `resizeEvent` 里按实时行数计算 —— 宽出的部分盖住行首两三个字符（如 `**`），直到滚动触发 `updateRequest` 才恢复。新增 `Editor.set_text()` 统一封装（blockSignals + setPlainText + `refresh_line_numbers()`），margins 与 geometry 始终同源，4 处调用点（切 tab / 打开文件 / 新建 / 进编辑模式）全部改走它，涉及 `main.py:690`
- **后台分块渲染的 mistune 实例竞态**：`_ChunkedRenderWorker` 与主线程共用全局 `_MD_INSTANCE`，renderer 内部状态在并发下相互污染。worker 改用 `own_md=True` 走 `_create_md_instance()` 建独立实例
- **紧接自动保存的外部修改被静默跳过**：`_autosave` 后记录文件 mtime，`_on_file_changed` 基于 mtime 二次判断，不再把外部真实改动当成自己写盘的回声

#### 优化

- **Loading 覆盖层位置**：Y 坐标 50 → 44，减少对标题栏/搜索栏的遮挡
- **超大页面临时文件堆积**：`_set_page_html` 走临时文件前先 `_cleanup_typered_tmp()`，避免 `typered_preview.html` 残留累积

#### 重构

- **XMind 死代码清理**：删除 `_xmind_to_markdown` 末尾不可达的 `return ''`；删除 `_xmind_topic` 未使用的 `sheet_title` 参数并修正调用方
- **头部版本注释同步**：`main.py:2` 长期停在 v0.6.5，与 `VERSION` 对齐

---

## [0.7.11] - 2026-07-13

> 缓存键稳定性修复 + 渲染管道安全加固 + emoji 预处理性能优化

#### 修复

- **渲染缓存键不稳定**：用 `hash(text)` 做缓存 key 在不同 Python 进程间不一致，导致跨会话缓存失效。替换为 `_content_fingerprint()`（`hashlib.md5[:16]`），稳定跨进程，涉及 `main.py:360`、`main.py:2433`

#### 安全

- **chunked 页面 JSON 注入风险**：`_render_chunk_to_html` 将渲染结果直接 JSON 序列化后注入 `<script>`，含 `</script>` 的正文可截断 script 标签执行任意 JS。新增 `_json_safe_embed()` 转义 `</script>` 序列，涉及 `main.py:365`、`main.py:572`

#### 优化

- **emoji 短代码重复处理**：`emoji.emojize()` 原在 `_render_to_body_toc()` 每次渲染调用，改为在 `load_file()` 一次性预处理，消除每次重渲染的重复开销，涉及 `main.py:2130`

---

## [0.7.10] - 2026-06-22

> 性能/死代码/UI 三维优化：复用 mistune 实例、删除废弃异步渲染路径、Loading 和欢迎页跟随主题、TOC 当前位置高亮

#### 性能

- **复用 mistune Markdown 实例**：`render_markdown` 用 `hasattr` 做属性缓存的做法（v0.7.5 已消灭同类反模式）替换为模块级 `_MD_INSTANCE` 变量，渲染核心提取为 `_render_to_body_toc` 供 `_ChunkedRenderWorker` 复用，两个 worker 不再各自创建独立 mistune 实例
- **`import json` 提到模块级**：`render_chunked` 和 `_ChunkedRenderWorker.run` 中的局部导入改为模块级一次导入

#### 重构

- **删除废弃异步渲染路径**：`_start_async_render` / `_RenderWorker` / `_on_async_render_done` — v0.7.7 引入分块渲染后的全量异步遗留代码，从未被调用

#### 移除

- **清理 splash 残留**：`make_splash.py` / `splash.png` / `TypeRed.spec` 中废弃 Splash 块

#### 美化

- **欢迎页代码高亮**：`_build_welcome_page` 注入 `pygments_css`，欢迎页 Markdown 代码围栏获得语法高亮
- **Loading 覆盖层跟随主题**：暗色/夜间主题下 Loading 标签使用深色渐变背景，不再固定浅色
- **TOC 当前标题高亮**：新增 IntersectionObserver 监测，滚动时自动高亮当前阅读标题

#### 修复

- **`test_render.py`**：`test_long_text` 使用不存在的 `'oled'` 主题 → 改为 `'dark'`

---

## [0.7.9] - 2026-06-20

> 启动优化：去掉 PyInstaller splash 和 QLabel「加载中…」，替换为 QTextBrowser 欢迎页

#### 优化

- **启动渲染**：去掉两段式加载（splash + QTimer 延迟 + QLabel「加载中…」），窗口立现 QTextBrowser 欢迎页，WebView 后台 600ms 懒加载就绪后无损替换。无文件启动完全免等待，有文件启动也不再有 splash 闪烁，渲染完成前内容可见

#### 重构

- **WebView 懒加载**：`_init_view` 拆出 `_ensure_view()`，只有实际需要 WebView 的操作（onboarding、预览、导出）才触发初始化；代码中的显式 `_init_view` 调用替换为一次 QTimer.singleShot 后台初始化，不再阻塞 `showEvent`
- **主题切换适配**：QTextBrowser 实现 `set_theme` 方法，set_theme 不依赖 WebView 存在，欢迎页跟随主题色变更
- **构建流水线**：`build.bat` 删除 splash 生成步骤和 `--splash` 参数，`TypeRed.spec` 由 PyInstaller 自动生成无 Splash 块

---

## [0.7.8] - 2026-06-15

### 修复

- **标签切换渲染缓存穿透**：`_last_render_key` 是全局字段未按标签保存，每次切标签都会触发全量重渲染。`_TabData` 新增 `render_key` 字段，切标签时保存/恢复缓存 key，已渲染的标签切回时直接跳过渲染管道
- **消除残留 getattr 反模式**：`_start_async_render` 和 `_start_chunked_async_render` 改用 `__init__` 初始化的 `self._render_worker`/`self._chunked_worker`，删除 `getattr(self, ...)` 运行时开销
- **消除 TitleBar 残留 hasattr**：`_btn_normal_style` 在 `__init__` 初始化，`set_edit_active` 不再使用 `hasattr` 运行时检查

### 优化

- **异步 worker 字段初始化**：`_render_worker` 和 `_chunked_worker` 在 `__init__` 显式初始化为 `None`，避免首次调用时 getattr 兜底路径

---

## [0.7.7] - 2026-06-15

### 优化

- **大文档渐进加载**：超过 50KB 的文档只渲染首屏内容到 WebView，剩余内容随滚动逐步加载。大幅缩短大文档初始打开时间——首屏渲染从"等全部"变为"等可见部分"，QWebEngine DOM 构建时间从 O(全文) 降为 O(视口)
- **三级渲染策略**：≤50KB 同步全量渲染（零延迟）、50KB–256KB 同步分块渲染、>256KB 后台线程分块渲染（UI 不冻结），按文件大小自动选择最优路径
- **Tag 深度追踪 HTML 切块**：`_chunk_rendered_html()` 通过跟踪标签嵌套栈精确识别顶层元素边界，正确切分含嵌套的 `<ul>`/`<blockquote>`/`<pre>` 等结构
- **script.js 事件委托重构**：TOC 跳转/图片放大/任务列表改为事件委托，动态加载的内容块自动继承交互能力
- **TOC 锚点预加载**：点击 TOC 中尚未渲染的标题，JS 自动加载其所在区块

### 修复

- **大文件白屏**：`setHtml()` 有 Chromium ~2MB 硬性限制，超大 HTML 静默失败导致白屏；现改为写入临时文件用 `load(QUrl)` 加载，注入 `<base>` 标签保证相对路径正常

---

## [0.7.5] - 2026-06-12

### 优化

- **消除 getattr 反模式**：`_last_render_key`、`_pending_scroll_ratio`、`_skip_next_watch` 提到 `__init__` 初始化，消除 6 处 `getattr(self, ...)` 运行时开销
- **Pygments CSS 缓存**：每个主题的代码高亮 CSS 只生成一次，后续渲染复用缓存，减少字符串拼接和 `HtmlFormatter` 实例化

---

## [0.7.4] - 2026-06-11

### 修复

- **缺少 _goto_line 方法定义**：Ctrl+G 快捷键绑了但方法体缺失，修复启动崩溃
- **缺少 _start_render_worker / _apply_render_result 方法定义**：后台渲染方法缺失，修复启动崩溃

### 优化

- **标题栏和标签栏瘦身**：TitleBar 38px -> 32px，标签 padding 5px -> 3px，标题字号 13px -> 12px
- **浅色主题视觉优化**：背景更白（#f5f5f5），按钮边框更明显（#999999），主题圆点改为蓝色
- **标题栏按钮跟随主题**：按钮边框/颜色/悬停效果全部使用主题色，不再写死
- **Mona 猫猫去掉边框线**：左下角猫猫不再显示主题色边框，更干净
- **浅色主题圆点**：从蓝色改为柔和灰色，更符合浅色主题定位

---

## [0.7.3] - 2026-06-11

### 新增

- **Ctrl+G 跳转到行**：编辑模式下快速跳转到指定行号

### 优化

- **渲染缓存校验增强**：缓存 key 增加文本长度维度，降低哈希碰撞概率

---

## [0.7.2] - 2026-06-11

### 新增

- **Ctrl+Shift+S 另存为**：标准快捷键，删除线改绑为 Ctrl+Alt+S

### 修复

- **全部替换忽略大小写/全词开关**：Replace All 现在正确响应 Aa 和 W 切换
- **外部修改文件静默覆盖**：文件被外部修改时状态栏提示 Ctrl+R 刷新，不再自动覆盖
- **autosave 后无谓 reload**：自动保存后短暂跳过 watcher 通知，避免页面闪烁

---

## [0.7.1] - 2026-06-11

### 修复

- **关闭窗口遍历所有标签页**：关闭窗口时检查所有标签页的未保存状态，不再只检查当前标签，防止其他标签的编辑内容被静默丢弃
- **关闭标签页同步最新内容**：关闭标签页时先将编辑器当前内容同步到标签数据再写盘，防止编辑后直接点关闭保存的不是最新内容

---

## [0.7.0] - 2026-06-09

### 新增

- **📑 多标签页**：支持同时打开多个文件，标签页可切换、拖拽排序、关闭；「打开」或拖入文件自动创建新标签页，已打开的文件切回对应标签
- **✨ Ctrl+N 新建文件**：快速创建空白 untitled 标签页，自动切入编辑模式，标题栏和标签栏同步显示
- **🔴 红色圆点关闭按钮**：标签页关闭按钮改为 macOS 交通灯风格的红色圆点（#ff5f57），悬停/按下有亮度反馈
- **📊 常驻状态栏**：状态栏始终显示当前文件的格式、行数、文件大小、词数和字符数，不再一闪而过

---

## [0.6.6] - 2026-06-09

### 优化

- **🚀 启动速度大幅提升**：打包方式从 `--onefile` 切换为 `--onedir`，启动时无需解压 241MB 的临时文件，双击到显示窗口时间显著缩短
- **⚡ WebView 提前初始化**：`_init_view()` 在 `show()` 之前执行，Chromium 子进程启动+内容加载在 splash 阶段完成，窗口弹出时内容已就绪或接近就绪，消除「加载中…」等待时间

---

## [0.6.5] - 2026-06-08

### 新增

- **😊 Emoji 短代码支持**：`:smile:` → 😄、`:rocket:` → 🚀 等，基于 `emoji` 包，支持完整 emoji 短代码词汇表
- **🖼️ 图片点击放大**：点击正文图片弹出全屏遮罩层查看原图，支持 ESC / 点击关闭，带毛玻璃背景
- **📋 可点击任务列表**：`- [ ]` `- [x]` 复选框可点击切换状态，跟随主题色

### 优化

- **🔤 智能排版**：借鉴 markdown-it typographer 功能，自动替换 `...` → …、`--` → —、`->` → →、`<-` → ←、`=>` → ⇒、`(c)` → ©、`(r)` → ®、`(tm)` → ™（代码块内不受影响）
- **💡 缩写支持**：`*[HTML]: HyperText Markup Language` 语法自动转为 `<abbr>` 标签（基于 mistune `abbr` 插件）

---

## [0.6.4] - 2026-06-01

### 修复

- **HTML 标签被 mistune 转义**：`TypeRedRenderer` 传入 `escape=False`，修复 `<details>` / `<summary>` 等原生 HTML 标签被误转为 `&lt;` 导致折叠功能失效

---

## [0.6.3] - 2026-06-01

### 修复

- **搜索栏位置**：从底部移至标题栏下方，避免与猫猫动画重叠

---

## [0.6.2] - 2026-06-01

### 新增

- **真毛玻璃效果**：窗口 `WA_TranslucentBackground` 让桌面壁纸穿透，`paintEvent` 绘制半透明背景层，标题栏/搜索栏/状态栏完全透明
- **滚动条加粗**：4px → 6px，圆角 2px → 3px，过渡 0.2s → 0.3s
- **TOC 侧边栏毛玻璃**：暗色主题 blur(20px)，浅色主题 blur(12px)
- **平滑过渡**：所有按钮 hover 状态添加过渡动画

---

## [0.6.1] - 2026-06-01

### 新增

- **XMind 思维导图支持**：打开 `.xmind` 文件自动解析为 Markdown 渲染，支持 Zen JSON 和旧版 XML 两种格式，备注内容转为引用块显示
- **思维导图模式 CSS**：XMind 文件自动应用层级颜色（蓝色→绿色→灰色）和左侧边框缩进，层级一目了然

---

## [0.6.0] - 2026-06-01

### 重构

- **渲染引擎替换**：用 `mistune`（C 扩展加速）替换 `python-markdown`，大文件渲染速度提升 5-10x
- **移除 pymdownx / attr_list 依赖**：`==highlight==`、`~sub~`、`^sup^`、`~~strike~~` 由 mistune 原生插件支持，不再依赖 `pymdownx.mark`、`pymdownx.tilde`、`pymdownx.caret`

### 优化

- **TOC 生成重写**：自定 `TypeRedRenderer` 类，继承 `mistune.HTMLRenderer`，`heading()` 自动生成 ID 锚点 + ¶ permalink，`build_toc()` 根据 h2-h4 构建嵌套目录
- **代码高亮保留**：`block_code()` 重写，使用 pygments 行内高亮，输出 `<div class="codehilite">` 保持 CSS 完全兼容
- **去除模块级 `markdown` 导入**，进一步减少 Python 启动开销

---

## [0.5.6] - 2026-05-28

### 重构

- **提取内联资源**：`build_page()` 中的 JavaScript 移至 `frontend/script.js`，`_show_welcome()` 中的欢迎页 Markdown 内容移至 `frontend/welcome.md`，均启动时一次性读入内存缓存
- **文件监听器去重**：新增 `_suspend_watcher()` / `_resume_watcher()` 辅助方法，消除 `save_file`、`_autosave`、`load_file` 中的 `removePath` / `addPath` 重复模式

## [0.5.5] - 2026-05-27

### 新增

- **搜索大小写/全词匹配**：搜索栏新增 `Aa`（大小写）和 `W`（全词）切换按钮
- **保存成功 Toast 弹窗**：`Ctrl+S` 保存后在窗口底部居中弹出轻量提示，2 秒自动消失
- **未保存更改提醒**：关闭窗口或切换文件时，若存在未保存更改则弹出 保存/放弃/取消 对话框，防止数据丢失

### 优化

- **按键性能优化**：`_on_editor_changed` 中缓存 `toPlainText()`，`_update_preview` 和 `_sync_preview_from_cursor` 复用，避免每次按键双重调用；字数统计改为 200ms 防抖，大文档不再卡顿
- **渲染缓存 key 优化**：用 `hash(text)` 代替全文比较，O(n) → O(1)
- **CSS 启动时读入内存**：`build_page` 将 CSS 内联注入 `<style>`，消除每次渲染时的磁盘 I/O
- **渲染异常保护**：`render_markdown` 失败时捕获异常并在状态栏提示，而非直接闪退

### 修复

- **修复 build.bat 打包缺失猫猫 GIF**：`--add-data` 补充 `mona-loading.gif`，`>/dev/null` 修正为 `>nul`（Windows 无效路径）
- **style.css 中文注释乱码**：重新保存为正确 UTF-8 编码

### 重构

- **文件扩展名提取为常量**：`SUPPORTED_EXTS` 统一定义，消除 `DragFilter` / 拖拽事件中 3 处重复
- **pillow 移至构建依赖**：`requirements.txt` 中去掉 pillow（仅 `make_icon.py` / `make_splash.py` 需要，运行时不需要）

---

## [0.5.4] - 2026-05-26

### 优化

- **启动速度大幅优化**：QWebEngineView / QWebEnginePage 延迟创建并移至 `showEvent` 中初始化，窗口先弹出再加载 WebView，双击到见窗时间缩短 50%+
- **重型导入延迟加载**：`QWebEngineView`、`QWebEnginePage`、`MarkdownPage` 从模块级导入移至运行时按需加载，减少 Python 启动开销
- **PyInstaller 启动屏**：双击 exe 立即显示 TypeRed 品牌画面，后台加载完毕后自动消失，告别空白等待

### 修复

- 修复版本号 `0.5.2` 未随 v0.5.3 更新为 `0.5.3` 的问题（同步为 v0.5.4）

---

## [0.5.3] - 2026-05-25

### 新增

- **猫猫打字动画**：编辑区打字时 mona 猫猫在左侧（阅读模式）/ 预览区左侧（编辑模式）左右弹跳，1.5 秒无操作恢复 GIF 循环；猫猫边框跟随主题色
- **编辑/预览同步滚动**：光标移动时按比例自动同步预览滚动位置，内容变更渲染完成后 120ms 自动对齐
- **macOS 风格滚动条**：4px 宽、半透明、hover 显色、圆角 2px

### 优化

- **启动速度优化**：Markdown 实例懒加载（`render_markdown` 首次调用时初始化），省模块导入时间；QWebEngineView 延迟创建，窗口先弹出再加载内容

### 修复

- 修复 `Set-Content` 导致的中文编码损坏

---

## [0.5.2] - 2026-05-23

### 修复
- 修复正文目录（`#content` 内）锚点链接无法跳转：将 `e.preventDefault()` 提前至 `if (el)` 判断之前，避免找不到元素时浏览器触发导航
- 修复 `acceptNavigationRequest` 对同文件 fragment 链接误调用 `load_file` 导致整页重载：检测 `url.fragment()` 非空且路径与当前文件相同时，改为用 `runJavaScript` 滚动到目标元素

---

## [0.5.1] - 2026-05-22

### 修复
- 修复右侧边缘缩放与 WebView 滚动条重叠：`_EdgeOverlay` 右侧检测边距由 8px 缩小至 4px（`_MARGIN_R`），其余三边保持 8px 不变

---

## [0.5.0] - 2026-05-21

### 新增
- 行号显示（编辑模式）
- 自动保存（30 秒间隔）
- TOC 侧边栏可拖拽分隔线调整宽度

### 修复
- 修复左下角缩放问题
- 修复保存后触发重载

### 优化
- 性能优化

---

## [0.4.6] - 2026-05-20

### 新增
- 链接拦截渲染：文档内 `.md` 链接直接渲染
- 外链自动用浏览器打开
- `Alt+←` / `Alt+→` 导航历史前进后退

### 修复
- 修复 HTML 块渲染

---

## [0.4.5] - 2026-05-19

### 修复
- 修复启动时窗口尺寸过大
- 保存最大化前窗口尺寸
- 默认缩小启动窗口

---

## [0.4.4] - 2026-05-19

### 修复
- 修复绿灯按钮还原窗口尺寸
- 任务栏最小化功能生效

---

## [0.4.3] - 2026-05-19

### 新增
- 任务栏图标支持切换最小化 / 还原 / 绿灯最大化还原

---

## [0.4.2] - 2026-05-19

### 修复
- 修复含 BOM 的 UTF-8 文件首行标题无法渲染

---

## [0.4.1] - 2026-05-19

### 修复
- 修复右键打开方式启动时显示欢迎页而非目标文件

---

## [0.4.0] - 2026-05-19

### 新增
- 查找替换（Ctrl+H）
- 编辑模式下拖入图片自动插入 ![]() 语法
- 插入表格对话框（Ctrl+Shift+T）

### 优化
- 启动速度优化

---

## [0.3.3] - 2026-05-19

### 新增
- 纯 Qt 边缘缩放
- 修复 Win11 无边框窗口无法调整大小

---

## [0.3.2] - 2026-05-18

### 新增
- Pygments 缓存
- 字数统计
- 编辑模式下 Ctrl+F 搜索

---

## [0.3.1] - 2026-05-18

### 新增
- 欢迎页详细化

### 修复
- 修复代码围栏嵌套渲染

---

## [0.3.0] - 2026-05-18

### 新增
- 编辑模式
- 实时预览（400ms）
- 格式快捷键（粗体/斜体/删除线/高亮/上下标/标题）
- 上下标渲染

---

## [0.2.0] - 2026-05-18

### 新增
- 最近文件
- 自动刷新
- 页内搜索
- 导出 PDF
- 记住窗口位置和主题

---

## [0.1.0] - 2026-05-18

### 新增
- 5 种主题
- macOS 风格交通灯
- 程序化图标
- 改名 TypeRed

---

## [0.0.1] - 2026-05-18

### 新增
- 初始版本
