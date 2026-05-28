# 主人偏好

## 工作纪律

- 我是主人的付费工具，不要浪费时间和金钱
- 回答直接干脆，不废话
- 未经主人允许，严禁推送 GitHub 或打包 release 版本
- 改代码前先列改动清单，测试后再提交

## 代码风格

- 注释格式：`# yymmdd Red xxx`（当天日期 + Red + 修改内容）
- 项目文档风格参考 README.md 和 CHANGELOG.md

## 对话纪律

- 称呼：**主人**
- 每次对话开始时，先阅读本文件，再开始工作
- 主人给出指令后，先理解清楚再动手，不跳步骤
- 提交改动前，自我检查注释格式是否符合规范
- **改完代码必须自动运行 `python main.py` 测试，确认无报错后再通知主人**，不让主人手动去 cmd 输入
- **主人说「更新推送」时，必须更新所有相关项**：README、CHANGELOG、版本号、日期等，不遗漏任何需要更新的东西

## 教训记录 (2026.5.28)

### TypeRed 大文件渲染修复踩坑总结

**问题**: 2.3MB MD 文件打开白屏，因为 `render_markdown()` 在主线程阻塞 1.5s

**正确方案**: 在 `render_markdown()` 前 show 一个原生 QLabel + `repaint()` 强制即时绘制，阻塞结束后 hide。纯 Qt 原生组件，不依赖 WebEngine。

**踩坑记录 (按尝试顺序)**:

1. **QThread + Signal** → 闪退
   - 原因: `QObject` 的 `Signal` 在 PyInstaller 打包后可能无法正确注册，导致 exe 启动崩溃
   - 教训: 在 PyInstaller 环境下，避免使用自定义 `QObject` + `Signal` 做跨线程通信

2. **threading.Thread + QTimer.singleShot(0, callback)** → 回调永不触发
   - 原因: `QTimer` 内部会创建一个 QTimer 对象，它必须在一个有 Qt 事件循环的线程中才能工作。Python `threading.Thread` 没有 Qt 事件循环
   - 教训: 从非 Qt 线程调用任何 Qt API 前，先确认该 API 是否跨线程安全。`QTimer.singleShot` 不跨线程安全

3. **threading.Thread + QCoreApplication.postEvent** → 闪退
   - 原因: `QEvent` 子类构造时传入了 `int` 而非 `QEvent.Type`，PySide6 报错。之后修复了类型但大文件仍卡住
   - 教训: `QEvent.registerEventType()` 返回 `int`，需用 `QEvent.Type(int_value)` 包装。且大 QEvent 对象跨线程传递可能有问题

4. **threading.Thread + queue.Queue 轮询** → 小文件可用，大文件卡住
   - 原因: 不确定。可能是 `QWebEngineView.setHtml()` 对大 HTML 响应慢，或进程间通信超时
   - 教训: 复杂方案 = 更多失效点

5. **QTimer.singleShot(100, lambda) 延迟渲染** → 所有文件都打不开
   - 原因: lambda 闭包捕获变量在某些 PyInstaller 环境下可能有问题
   - 教训: 避免 lambda 做延时回调，用实例方法 + 实例属性存数据更可靠

6. **原代码 + 仅 QLabel show/processEvents** → "没用"
   - 原因: `processEvents()` 处理 Qt 事件但不一定触发 WebEngine 的渲染。父窗口的 `_EdgeOverlay` 可能遮挡了 QLabel
   - 教训: 用 `repaint()` 而非 `processEvents()` 强制立即绘制原生组件

7. **`repaint()` + 纯 ASCII 文本** → 成功！
   - 关键: `QLabel.repaint()` 强制即时绘制，`processEvents()` 是异步的。emoji/非ASCII字符在PyInstaller exe中有编码问题
   - 教训: exe 中优先用纯 ASCII 文本

### 通用教训

- 先从**最简单、改动最小**的方案开始尝试，不要一上来就上多线程
- PySide6 + PyInstaller 的组合会有一些奇怪的限制（Signal注册、跨线程通信等），优先用纯 Qt 原生组件 + 同步调用
- 不要假设 `QTimer`, `QThread`, `Signal` 在 PyInstaller 打包后的行为与 Python 直接运行时一致
- 每次改动后必须自己先验证再让主人测试，不能连续多次失败消耗主人耐心
