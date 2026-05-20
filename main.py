# author Red
# TypeRed — Markdown Reader & Editor v0.4.3
#//#260518 Red 0.3.0 编辑模式/实时预览/Markdown格式快捷键/上下标高亮渲染
#//#260518 Red 0.3.1 欢迎页详细化/修复代码围栏嵌套渲染/README补全快捷键
#//#260518 Red 0.3.2 pygments_css缓存/字数统计/编辑模式Ctrl+F指向编辑区
#//#260519 Red 0.3.3 纯Qt边缘缩放覆盖层/修复Win11无边框窗口无法调整大小
#//#260519 Red 0.4.0 查找替换(Ctrl+H)/图片拖入自动插入语法/插入表格对话框(Ctrl+Shift+T)
#//#260519 Red 0.4.1 修复通过右键"打开方式"启动时显示欢迎页而非目标文件
#//#260519 Red 0.4.2 修复含BOM的UTF-8文件首行标题无法渲染
#//#260519 Red 0.4.3 任务栏图标支持最小化/还原切换/绿灯最大化还原
#//#260519 Red 0.4.4 修复绿灯还原不回正确尺寸/任务栏SWP_FRAMECHANGED生效
#//#260519 Red 0.4.5 修复关闭时保存最大化尺寸导致下次启动过大/默认窗口尺寸缩小
#//#260520 Red 0.4.6 链接拦截(内链渲染/外链浏览器)/导航历史Alt+左右/修夋HTML块内Markdown渲染

import sys
import os
import re
import ctypes
from functools import lru_cache

import markdown
from markdown.extensions.toc import TocExtension
from pygments.formatters import HtmlFormatter

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QPushButton, QSizeGrip, QMenu,
    QPlainTextEdit, QSplitter,
    QDialog, QSpinBox, QFormLayout, QDialogButtonBox,
)
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEnginePage
from PySide6.QtCore import (
    Qt, QUrl, QPointF, QRectF, QEvent, QObject,
    QFileSystemWatcher, QSettings, QSize, QPoint, QTimer,
)
from PySide6.QtGui import (
    QIcon, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut,
    QPainter, QColor, QPixmap, QFont, QPainterPath, QLinearGradient,
    QMouseEvent, QAction, QTextCursor, QRegion, QDesktopServices,
)
from PySide6.QtPrintSupport import QPrinter

VERSION  = "0.4.6"
APP_NAME = "TypeRed"
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
MAX_RECENT = 10

# ── 主题定义 ──────────────────────────────────────────────────────────────────

THEMES      = ['light', 'eye-care', 'cream', 'dark', 'night']
THEME_NAMES = ['默认',  '护眼',    '米黄',  '暗色', '夜间']

# (bg, fg, divider_border, btn_border, btn_fg)
THEME_TB: dict[str, tuple[str, str, str, str, str]] = {
    'light':    ('#ececec', '#2a2a2a', '#d0d0d0', '#b8b8b8', '#2a2a2a'),
    'eye-care': ('#d8edd8', '#1a2e1a', '#b8d8b8', '#88bb88', '#1a2e1a'),
    'cream':    ('#e8dcc0', '#2c1f0a', '#ccb888', '#aa8844', '#2c1f0a'),
    'dark':     ('#14151e', '#c0caf5', '#2a2b3d', '#5a5c7e', '#dde0ff'),
    'night':    ('#0d0d0d', '#d0d0d0', '#222222', '#505050', '#f0f0f0'),
}

THEME_DOT: dict[str, str] = {
    'light':    '#c8c8c8',
    'eye-care': '#6db86d',
    'cream':    '#c8a050',
    'dark':     '#5b6aae',
    'night':    '#3a3a3a',
}

THEME_PYG: dict[str, str] = {
    'light':    'friendly',
    'eye-care': 'friendly',
    'cream':    'autumn',
    'dark':     'monokai',
    'night':    'monokai',
}

# 编辑器 bg / fg / 行号区 bg
THEME_EDITOR: dict[str, tuple[str, str]] = {
    'light':    ('#ffffff', '#1a1a1a'),
    'eye-care': ('#f0f7f0', '#1a2e1a'),
    'cream':    ('#fdf6e3', '#2c1f0a'),
    'dark':     ('#1a1b26', '#c0caf5'),
    'night':    ('#0a0a0a', '#cccccc'),
}

# ── 程序化图标 ────────────────────────────────────────────────────────────────

def make_app_icon() -> QIcon:
    size = 256
    pix  = QPixmap(size, size)
    pix.fill(Qt.transparent)
    p = QPainter(pix)
    p.setRenderHint(QPainter.Antialiasing)
    grad = QLinearGradient(QPointF(0, 0), QPointF(size, size))
    grad.setColorAt(0.0, QColor('#5b7cf7'))
    grad.setColorAt(1.0, QColor('#8b5cf6'))
    path = QPainterPath()
    path.addRoundedRect(QRectF(10, 10, size - 20, size - 20), 54, 54)
    p.fillPath(path, grad)
    font = QFont('Segoe UI', 100, QFont.Bold)
    p.setFont(font)
    p.setPen(QColor(255, 255, 255, 230))
    p.drawText(pix.rect(), Qt.AlignCenter, 'TR')
    p.end()
    return QIcon(pix)


# ── Markdown 渲染 ─────────────────────────────────────────────────────────────

def _build_extensions() -> list:
    base = [
        'fenced_code', 'tables', 'attr_list', 'def_list',
        'footnotes', 'nl2br',
        TocExtension(permalink=True, toc_depth='2-4'),
        'codehilite', 'sane_lists',
    ]
    # 尝试加载 pymdownx 扩展（上标/下标/高亮）
    optional = ['pymdownx.mark', 'pymdownx.tilde', 'pymdownx.caret']
    for ext in optional:
        try:
            import importlib
            importlib.import_module(ext.replace('.', '/').replace('/', '.'))
            base.append(ext)
        except Exception:
            pass
    return base

MD_EXTENSIONS = _build_extensions()


def render_markdown(text: str) -> tuple[str, str]:
    # 剥除 <div> 标签（保留内容），避免 HTML 块阻断 Markdown 解析
    text = re.sub(r"</?div[^>]*>", "", text)
    md = markdown.Markdown(
        extensions=MD_EXTENSIONS,
        extension_configs={'codehilite': {'guess_lang': False, 'linenums': False}}
    )
    body = md.convert(text)
    toc  = getattr(md, 'toc', '')
    return body, toc


@lru_cache(maxsize=None)
def pygments_css(theme: str) -> str:
    try:
        return HtmlFormatter(style=THEME_PYG.get(theme, 'friendly')).get_style_defs('.codehilite')
    except Exception:
        return ''


def build_page(body: str, toc: str, theme: str, title: str = '') -> str:
    css_path  = os.path.join(BASE_DIR, 'frontend', 'style.css').replace('\\', '/')
    toc_block = f'<nav id="toc">{toc}</nav>' if toc.strip() else ''
    return f"""<!DOCTYPE html>
<html class="{theme}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<link rel="stylesheet" href="file:///{css_path}">
<style>{pygments_css(theme)}</style>
</head>
<body>
<div id="layout">
  {toc_block}
  <article id="content">{body}</article>
</div>
<script>
  document.querySelectorAll('#toc a').forEach(a => {{
    a.addEventListener('click', e => {{
      const id = a.getAttribute('href').replace(/.*#/, '');
      const el = document.getElementById(id);
      if (el) {{ e.preventDefault(); el.scrollIntoView({{behavior:'smooth'}}); }}
    }});
  }});
</script>
</body>
</html>"""


# ── 拖拽过滤器 ────────────────────────────────────────────────────────────────

class DragFilter(QObject):
    _EXTS = ('.md', '.markdown', '.mdown', '.txt')

    def __init__(self, win: 'TypeRedWindow'):
        super().__init__(win)
        self._win = win

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.Type.DragEnter:
            for u in event.mimeData().urls():
                if u.toLocalFile().lower().endswith(self._EXTS):
                    event.acceptProposedAction()
                    return True
        elif t == QEvent.Type.Drop:
            for u in event.mimeData().urls():
                path = u.toLocalFile()
                if path.lower().endswith(self._EXTS):
                    self._win.load_file(path)
                    return True
        return False



# ── 自定义页面（链接拦截）────────────────────────────────────────────────────

class MarkdownPage(QWebEnginePage):
    """拦截链接点击：.md 文件在当前窗口渲染，http(s) 链接用系统浏览器打开。"""
    _MD_EXTS = ('.md', '.markdown', '.mdown', '.txt')

    def __init__(self, win, parent=None):
        super().__init__(parent)
        self._win = win

    def acceptNavigationRequest(self, url, nav_type, _is_main):
        if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
            path = url.toLocalFile()
            if path:
                # 所有本地文件链接都通过 load_file 加载，确保历史栈记录
                QTimer.singleShot(0, lambda p=path: self._win.load_file(p))
                return False
            if url.scheme() in ('http', 'https'):
                QTimer.singleShot(0, lambda u=url: QDesktopServices.openUrl(u))
                return False
        return True


# ── Markdown 编辑器 ───────────────────────────────────────────────────────────

class Editor(QPlainTextEdit):
    """带 Markdown 格式快捷键的纯文本编辑器。"""
    _IMG_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff')

    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change
        self.setFont(QFont('Cascadia Code, JetBrains Mono, Consolas, Courier New', 13))
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabStopDistance(28)  # 约4个字符宽
        self.textChanged.connect(on_change)

    # ── 格式包裹 ──────────────────────────────────────────────────────────────

    def _wrap(self, marker: str, end: str = ''):
        if not end:
            end = marker
        cur = self.textCursor()
        if cur.hasSelection():
            text = cur.selectedText()
            cur.insertText(f'{marker}{text}{end}')
        else:
            pos = cur.position()
            cur.insertText(f'{marker}{end}')
            cur.setPosition(pos + len(marker))
            self.setTextCursor(cur)

    # ── 标题行 ────────────────────────────────────────────────────────────────

    def _set_heading(self, level: int):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.StartOfLine)
        cur.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cur.selectedText()
        line = re.sub(r'^#{1,6}\s*', '', line)
        prefix = '#' * level + ' ' if level > 0 else ''
        cur.insertText(prefix + line)

    # ── 列表 ──────────────────────────────────────────────────────────────────

    def _toggle_list(self, ordered: bool):
        cur = self.textCursor()
        cur.movePosition(QTextCursor.StartOfLine)
        cur.movePosition(QTextCursor.EndOfLine, QTextCursor.KeepAnchor)
        line = cur.selectedText()
        # 已有列表标记则去掉
        if re.match(r'^(\d+\.\s+|-\s+)', line):
            line = re.sub(r'^(\d+\.\s+|-\s+)', '', line)
        else:
            line = ('1. ' if ordered else '- ') + line
        cur.insertText(line)

    # ── Tab 缩进 ──────────────────────────────────────────────────────────────

    def keyPressEvent(self, e):
        # Tab → 4 空格
        if e.key() == Qt.Key_Tab and not e.modifiers():
            self.insertPlainText('    ')
            return
        # Shift+Tab → 去除前4空格
        if e.key() == Qt.Key_Backtab:
            cur = self.textCursor()
            cur.movePosition(QTextCursor.StartOfLine)
            cur.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor,
                             min(4, len(self.document().findBlockByNumber(
                                 cur.blockNumber()).text())))
            txt = cur.selectedText()
            stripped = re.sub(r'^ {1,4}', '', txt)
            cur.insertText(stripped)
            return
        # Ctrl+B 粗体
        if e.key() == Qt.Key_B and e.modifiers() == Qt.ControlModifier:
            self._wrap('**')
            return
        # Ctrl+I 斜体
        if e.key() == Qt.Key_I and e.modifiers() == Qt.ControlModifier:
            self._wrap('*')
            return
        # Ctrl+Shift+S 删除线
        if e.key() == Qt.Key_S and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._wrap('~~')
            return
        # Ctrl+Shift+H 高亮
        if e.key() == Qt.Key_H and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._wrap('==')
            return
        # Ctrl+Shift+P 上标 ^
        if e.key() == Qt.Key_P and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._wrap('^')
            return
        # Ctrl+Shift+B 下标 ~
        if e.key() == Qt.Key_B and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._wrap('~')
            return
        # Ctrl+1~6 标题
        if e.modifiers() == Qt.ControlModifier and Qt.Key_1 <= e.key() <= Qt.Key_6:
            self._set_heading(e.key() - Qt.Key_0)
            return
        # Ctrl+0 取消标题
        if e.key() == Qt.Key_0 and e.modifiers() == Qt.ControlModifier:
            self._set_heading(0)
            return
        # Ctrl+Shift+U 无序列表
        if e.key() == Qt.Key_U and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._toggle_list(False)
            return
        # Ctrl+Shift+O 有序列表
        if e.key() == Qt.Key_O and e.modifiers() == (Qt.ControlModifier | Qt.ShiftModifier):
            self._toggle_list(True)
            return
        super().keyPressEvent(e)

    # ── 图片拖入 ──────────────────────────────────────────────────────────────

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            for u in e.mimeData().urls():
                if u.toLocalFile().lower().endswith(self._IMG_EXTS):
                    e.acceptProposedAction()
                    return
        super().dragEnterEvent(e)

    def dropEvent(self, e):
        for u in e.mimeData().urls():
            path = u.toLocalFile()
            if path.lower().endswith(self._IMG_EXTS):
                self.insertPlainText(f'![]({path.replace(chr(92), "/")})')
                e.acceptProposedAction()
                return
        super().dropEvent(e)

    def apply_theme(self, theme: str):
        bg, fg = THEME_EDITOR[theme]
        _, _, border, _, _ = THEME_TB[theme]
        self.setStyleSheet(f"""
            QPlainTextEdit {{
                background: {bg};
                color: {fg};
                border: none;
                border-right: 1px solid {border};
                font-family: 'Cascadia Code', 'JetBrains Mono', Consolas, monospace;
                font-size: 13px;
                padding: 12px 16px;
                selection-background-color: rgba(91,124,247,0.35);
            }}
        """)


# ── macOS 交通灯 ──────────────────────────────────────────────────────────────

class TrafficLights(QWidget):
    _COLORS = ('#ff5f57', '#febc2e', '#28c840')

    def __init__(self, win: QMainWindow):
        super().__init__(win)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(7)
        btns = []
        for color in self._COLORS:
            btn = QPushButton()
            btn.setFixedSize(13, 13)
            btn.setStyleSheet(f"""
                QPushButton {{ background: {color}; border-radius: 6px; border: none; }}
                QPushButton:pressed {{ opacity: 0.7; }}
            """)
            btns.append(btn)
            layout.addWidget(btn)
        btns[0].clicked.connect(win.close)
        btns[1].clicked.connect(win.showMinimized)
        btns[2].clicked.connect(win._toggle_maximize)


# ── 主题圆点 ──────────────────────────────────────────────────────────────────

class ThemeDots(QWidget):
    def __init__(self, on_change):
        super().__init__()
        self._btns: list[QPushButton] = []
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        for theme, name, color in zip(THEMES, THEME_NAMES, THEME_DOT.values()):
            btn = QPushButton()
            btn.setFixedSize(16, 16)
            btn.setToolTip(name)
            btn._theme = theme   # type: ignore[attr-defined]
            btn._color = color   # type: ignore[attr-defined]
            btn.clicked.connect(lambda _, t=theme: on_change(t))
            self._btns.append(btn)
            layout.addWidget(btn)
        self.set_active('light')

    def set_active(self, active_theme: str):
        for btn in self._btns:
            sel    = btn._theme == active_theme  # type: ignore[attr-defined]
            ring   = '2px solid rgba(255,255,255,0.85)' if sel else '2px solid transparent'
            shadow = 'box-shadow: 0 0 0 1px rgba(0,0,0,0.3);' if sel else ''
            btn.setStyleSheet(f"""
                QPushButton {{
                    background: {btn._color};
                    border-radius: 8px;
                    border: {ring};
                    {shadow}
                }}
            """)


# ── 自定义标题栏 ──────────────────────────────────────────────────────────────

class TitleBar(QWidget):
    def __init__(self, win: 'TypeRedWindow'):
        super().__init__(win)
        self._win      = win
        self._drag_pos = None
        self.setFixedHeight(38)
        self.setObjectName('titlebar')

        root = QHBoxLayout(self)
        root.setContentsMargins(10, 0, 12, 0)
        root.setSpacing(8)

        root.addWidget(TrafficLights(win))
        root.addSpacing(6)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(18, 18)
        root.addWidget(self.icon_lbl)
        root.addSpacing(4)

        self.lbl_title = QLabel(APP_NAME)
        self.lbl_title.setObjectName('tb_title')
        root.addWidget(self.lbl_title)

        root.addStretch()

        self.theme_dots = ThemeDots(win.set_theme)
        root.addWidget(self.theme_dots)
        root.addSpacing(8)

        self.btn_edit = QPushButton('编辑')
        self.btn_edit.setObjectName('tb_btn')
        self.btn_edit.setFixedSize(46, 24)
        self.btn_edit.clicked.connect(win.toggle_edit)
        root.addWidget(self.btn_edit)
        root.addSpacing(4)

        self.btn_recent = QPushButton('最近')
        self.btn_recent.setObjectName('tb_btn')
        self.btn_recent.setFixedSize(46, 24)
        self.btn_recent.clicked.connect(self._show_recent_menu)
        root.addWidget(self.btn_recent)
        root.addSpacing(4)

        self.btn_open = QPushButton('打开')
        self.btn_open.setObjectName('tb_btn')
        self.btn_open.setFixedSize(46, 24)
        self.btn_open.clicked.connect(win.open_file_dialog)
        root.addWidget(self.btn_open)

    def set_icon(self, icon: QIcon):
        self.icon_lbl.setPixmap(icon.pixmap(18, 18))

    def apply_theme(self, theme: str):
        # 标题栏固定中性风格，不随内容主题变化
        self.setStyleSheet("""
            TitleBar { background: #f0f0f0; border-bottom: 1px solid #d0d0d0; }
            #tb_title { color: #2a2a2a; font-size: 13px; font-weight: 600; }
        """)
        self._btn_normal_style = """
            QPushButton {
                background: #f0f0f0;
                color: #2a2a2a;
                border: 1px solid #c0c0c0;
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover   { background: #e0e0e0; }
            QPushButton:pressed { background: #d0d0d0; }
        """
        for btn in (self.btn_edit, self.btn_recent, self.btn_open):
            btn.setStyleSheet(self._btn_normal_style)
        self.theme_dots.set_active(theme)

    def _show_recent_menu(self):
        recent = self._win.get_recent_files()
        if not recent:
            return
        menu = QMenu(self)
        bg, fg, border, _, _ = THEME_TB[self._win.theme]
        menu.setStyleSheet(f"""
            QMenu {{
                background: {bg}; color: {fg};
                border: 1px solid {border};
                padding: 4px 0; font-size: 12px;
            }}
            QMenu::item {{ padding: 5px 20px; }}
            QMenu::item:selected {{ background: rgba(128,128,128,0.2); }}
        """)
        for path in recent:
            act = QAction(os.path.basename(path), self)
            act.setToolTip(path)
            act.triggered.connect(lambda _, p=path: self._win.load_file(p))
            menu.addAction(act)
        menu.addSeparator()
        clear = QAction('清空记录', self)
        clear.triggered.connect(self._win.clear_recent_files)
        menu.addAction(clear)
        menu.exec(self.btn_recent.mapToGlobal(self.btn_recent.rect().bottomLeft()))

    def set_edit_active(self, active: bool):
        """编辑模式时「编辑」按钮高亮。"""
        if active:
            self.btn_edit.setStyleSheet("""
                QPushButton {
                    background: rgba(91,124,247,0.18);
                    color: #3a5ad4;
                    border: 1px solid rgba(91,124,247,0.55);
                    border-radius: 5px;
                    font-size: 12px;
                    font-weight: 600;
                }
                QPushButton:hover { background: rgba(91,124,247,0.28); }
            """)
        else:
            # 恢复到 apply_theme 时存储的普通样式
            if hasattr(self, '_btn_normal_style'):
                self.btn_edit.setStyleSheet(self._btn_normal_style)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._drag_pos = e.globalPosition().toPoint() - self._win.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self._drag_pos and e.buttons() & Qt.LeftButton:
            self._win.move(e.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, e: QMouseEvent):
        self._drag_pos = None

    def mouseDoubleClickEvent(self, e: QMouseEvent):
        if self._win.isMaximized():
            self._win.showNormal()
        else:
            self._win.showMaximized()


# ── 搜索/替换栏 ───────────────────────────────────────────────────────────────

class SearchBar(QWidget):
    def __init__(self, view: QWebEngineView, win: 'TypeRedWindow'):
        super().__init__(win)
        self._view   = view
        self._win    = win
        self._editor = None
        self.setVisible(False)

        from PySide6.QtWidgets import QLineEdit
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 4, 8, 4)
        vbox.setSpacing(3)

        # 搜索行
        row1 = QWidget()
        h1 = QHBoxLayout(row1)
        h1.setContentsMargins(0, 0, 0, 0)
        h1.setSpacing(6)
        self.input = QLineEdit()
        self.input.setPlaceholderText('搜索…')
        self.input.setFixedHeight(26)
        self.input.textChanged.connect(self._search)
        self.input.returnPressed.connect(self._next)
        h1.addWidget(self.input)
        for label, fn in [('↑', self._prev), ('↓', self._next), ('✕', self.hide_bar)]:
            btn = QPushButton(label)
            btn.setFixedSize(26, 26)
            btn.clicked.connect(fn)
            h1.addWidget(btn)
        vbox.addWidget(row1)

        # 替换行（仅编辑模式下展示）
        self._replace_row = QWidget()
        h2 = QHBoxLayout(self._replace_row)
        h2.setContentsMargins(0, 0, 0, 0)
        h2.setSpacing(6)
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText('替换为…')
        self.replace_input.setFixedHeight(26)
        h2.addWidget(self.replace_input)
        btn_rep = QPushButton('替换')
        btn_rep.setFixedHeight(26)
        btn_rep.clicked.connect(self._replace_one)
        h2.addWidget(btn_rep)
        btn_rep_all = QPushButton('全部替换')
        btn_rep_all.setFixedHeight(26)
        btn_rep_all.clicked.connect(self._replace_all)
        h2.addWidget(btn_rep_all)
        self._replace_row.setVisible(False)
        vbox.addWidget(self._replace_row)

    def set_target(self, editor=None):
        self._editor = editor

    def show_bar(self, replace_mode: bool = False):
        self._replace_row.setVisible(replace_mode and self._editor is not None)
        self.setVisible(True)
        self.input.setFocus()
        self.input.selectAll()

    def hide_bar(self):
        self.setVisible(False)
        if self._editor:
            cur = self._editor.textCursor()
            cur.clearSelection()
            self._editor.setTextCursor(cur)
            self._editor.setFocus()
        else:
            self._view.findText('')
            self._view.setFocus()

    def _search(self, text: str):
        if self._editor:
            self._editor.find(text)
        else:
            self._view.findText(text)

    def _next(self):
        text = self.input.text()
        if self._editor:
            self._editor.find(text)
        else:
            self._view.findText(text)

    def _prev(self):
        from PySide6.QtGui import QTextDocument
        text = self.input.text()
        if self._editor:
            self._editor.find(text, QTextDocument.FindFlag.FindBackward)
        else:
            self._view.findText(text, QWebEnginePage.FindFlag.FindBackward)

    def _replace_one(self):
        if not self._editor:
            return
        find_text    = self.input.text()
        replace_text = self.replace_input.text()
        cur = self._editor.textCursor()
        if cur.hasSelection() and cur.selectedText() == find_text:
            cur.insertText(replace_text)
        self._editor.find(find_text)

    def _replace_all(self):
        if not self._editor or not self.input.text():
            return
        find_text    = self.input.text()
        replace_text = self.replace_input.text()
        text  = self._editor.toPlainText()
        count = text.count(find_text)
        if count == 0:
            self._win.statusBar().showMessage('未找到匹配项')
            return
        cur_pos  = self._editor.textCursor().position()
        new_text = text.replace(find_text, replace_text)
        self._editor.setPlainText(new_text)
        cur = self._editor.textCursor()
        cur.setPosition(min(cur_pos, len(new_text)))
        self._editor.setTextCursor(cur)
        self._win.statusBar().showMessage(f'已替换 {count} 处')

    def apply_theme(self, theme: str):
        bg, fg, border, btn_border, _ = THEME_TB[theme]
        self.setStyleSheet(f"""
            SearchBar {{
                background: {bg};
                border-top: 1px solid {border};
            }}
            QLineEdit {{
                background: rgba(128,128,128,0.12);
                color: {fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                padding: 0 6px;
                font-size: 13px;
            }}
            QPushButton {{
                background: transparent;
                color: {fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                font-size: 12px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background: rgba(128,128,128,0.15); }}
        """)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide_bar()
        else:
            super().keyPressEvent(e)


# ── 边缘缩放覆盖层（纯 Qt，不依赖 Windows API） ──────────────────────────────

class _EdgeOverlay(QWidget):
    """透明覆盖层，`setMask` 只在窗口边缘 8px 接收鼠标事件，
       中间区域事件穿透到子部件。处理边缘拖拽缩放。"""
    _MARGIN    = 8
    _MIN_W     = 640
    _MIN_H     = 420
    _CURSORS   = {
        'tl': Qt.SizeFDiagCursor, 'tr': Qt.SizeBDiagCursor,
        'bl': Qt.SizeBDiagCursor, 'br': Qt.SizeFDiagCursor,
        'l': Qt.SizeHorCursor,    'r': Qt.SizeHorCursor,
        't': Qt.SizeVerCursor,    'b': Qt.SizeVerCursor,
    }

    def __init__(self, parent, window):
        super().__init__(parent)
        self._window    = window
        self._resizing  = False
        self._edge      = None
        self._start_pos = None
        self._start_geo = None
        self.setMouseTracking(True)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)

    def _update_mask(self):
        w, h = self.width(), self.height()
        m = self._MARGIN
        full  = QRegion(0, 0, w, h)
        inner = QRegion(m, m, w - 2*m, h - 2*m)
        self.setMask(full.subtracted(inner))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_mask()

    def _edge_at(self, pos):
        w, h = self.width(), self.height()
        m = self._MARGIN
        x, y = int(pos.x()), int(pos.y())
        on_l = x <= m; on_r = x >= w - m - 1
        on_t = y <= m; on_b = y >= h - m - 1
        if on_t and on_l: return 'tl'
        if on_t and on_r: return 'tr'
        if on_b and on_l: return 'bl'
        if on_b and on_r: return 'br'
        if on_l: return 'l'
        if on_r: return 'r'
        if on_t: return 't'
        if on_b: return 'b'
        return None

    def mouseMoveEvent(self, e):
        if self._resizing and self._edge:
            dx = e.globalPosition().x() - self._start_pos.x()
            dy = e.globalPosition().y() - self._start_pos.y()
            rx, ry, rw, rh = self._start_geo
            edge = self._edge
            if 'l' in edge: rx += dx; rw -= dx
            if 'r' in edge: rw += dx
            if 't' in edge: ry += dy; rh -= dy
            if 'b' in edge: rh += dy
            if rw < self._MIN_W:
                if 'l' in edge: rx -= (self._MIN_W - rw)
                rw = self._MIN_W
            if rh < self._MIN_H:
                if 't' in edge: ry -= (self._MIN_H - rh)
                rh = self._MIN_H
            self._window.setGeometry(int(rx), int(ry), int(rw), int(rh))
            return
        edge = self._edge_at(e.position())
        self.setCursor(self._CURSORS.get(edge, Qt.ArrowCursor))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            edge = self._edge_at(e.position())
            if edge:
                self._resizing  = True
                self._edge      = edge
                self._start_pos = e.globalPosition().toPoint()
                self._start_geo = (self._window.x(), self._window.y(),
                                   self._window.width(), self._window.height())
                return
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        if self._resizing:
            self._resizing  = False
            self._edge      = None
            self._start_pos = None
            self._start_geo = None
            return
        super().mouseReleaseEvent(e)


# ── 主窗口 ────────────────────────────────────────────────────────────────────

class TypeRedWindow(QMainWindow):
    def __init__(self, app_icon: QIcon, initial_file: str = ''):
        super().__init__()
        self._initial_file    = initial_file
        self._pre_max_geo     = None          # 最大化前保存的窗口尺寸
        self._nav_history: list[str] = []    # 导航历史栈
        self._nav_idx     = -1
        self.theme            = 'light'
        self.current_file     = ''
        self._current_text    = ''
        self._modified        = False
        self._edit_mode       = False
        self._app_icon        = app_icon
        self._settings        = QSettings('Red', APP_NAME)
        self._watcher         = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(400)
        self._preview_timer.timeout.connect(self._update_preview)

        self._build_ui()
        self._restore_state()
        self.setAcceptDrops(True)

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.resize(900, 640)
        self.setMinimumSize(640, 420)
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(self._app_icon)

        self.titlebar = TitleBar(self)
        self.titlebar.set_icon(self._app_icon)
        self.titlebar.apply_theme(self.theme)

        # 编辑器 + 预览 分栏
        self.editor = Editor(self._on_editor_changed)
        self.editor.apply_theme(self.theme)
        self.editor.setVisible(False)

        self.view = QWebEngineView()
        self.view.setPage(MarkdownPage(self, self.view))
        self.view.setAcceptDrops(False)
        self._drag_filter = DragFilter(self)
        self.view.installEventFilter(self._drag_filter)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self.view)

        self.search_bar = SearchBar(self.view, self)
        self.search_bar.apply_theme(self.theme)

        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addPermanentWidget(QSizeGrip(self))
        self.statusBar().showMessage(f'{APP_NAME} v{VERSION}  |  拖入 .md 文件或点击「打开」')

        central = QWidget()
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.titlebar)
        layout.addWidget(self.splitter, 1)
        layout.addWidget(self.search_bar)
        self.setCentralWidget(central)

        # 边缘缩放覆盖层（透明，只捕获边缘 8px）
        self._edge_overlay = _EdgeOverlay(central, self)
        self._edge_overlay.setGeometry(central.rect())
        self._edge_overlay.show()
        self._edge_overlay.raise_()

        self._register_shortcuts()
        if self._initial_file:
            QTimer.singleShot(0, lambda: self.load_file(self._initial_file))
        else:
            QTimer.singleShot(0, self._show_welcome)

    def _nav_back(self):
        if self._nav_idx > 0:
            self._nav_idx -= 1
            self.load_file(self._nav_history[self._nav_idx], _push_history=False)

    def _nav_forward(self):
        if self._nav_idx < len(self._nav_history) - 1:
            self._nav_idx += 1
            self.load_file(self._nav_history[self._nav_idx], _push_history=False)

    def _toggle_maximize(self):
        if self.isMaximized():
            self.showNormal()
            if self._pre_max_geo is not None:
                self.setGeometry(self._pre_max_geo)
        else:
            self._pre_max_geo = self.geometry()
            self.showMaximized()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, '_edge_overlay'):
            self._edge_overlay.setGeometry(self.centralWidget().rect())

    def showEvent(self, e):
        super().showEvent(e)
        # 为无边框窗口加 WS_MINIMIZEBOX，使任务栏图标支持点击最小化/还原切换
        try:
            GWL_STYLE        = -16
            WS_MINIMIZEBOX   = 0x00020000
            SWP_FRAMECHANGED = 0x0020
            SWP_NOMOVE       = 0x0002
            SWP_NOSIZE       = 0x0001
            SWP_NOZORDER     = 0x0004
            hwnd  = int(self.winId())
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style | WS_MINIMIZEBOX)
            ctypes.windll.user32.SetWindowPos(
                hwnd, None, 0, 0, 0, 0,
                SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_FRAMECHANGED
            )
        except Exception:
            pass
        from PySide6.QtWidgets import QWidget as _QW
        for child in self.view.findChildren(_QW):
            child.setAcceptDrops(False)
            child.installEventFilter(self._drag_filter)

    # ── 状态持久化 ────────────────────────────────────────────────────────────

    def _restore_state(self):
        theme = self._settings.value('theme', 'light')
        if theme in THEMES:
            self.theme = theme
            self.titlebar.apply_theme(theme)
            self.search_bar.apply_theme(theme)
            self.editor.apply_theme(theme)

        pos  = self._settings.value('pos')
        size = self._settings.value('size')
        if isinstance(pos, QPoint):
            self.move(pos)
        if isinstance(size, QSize):
            screen = QApplication.primaryScreen().availableSize()
            if size.width() < screen.width() * 0.9 and size.height() < screen.height() * 0.9:
                self.resize(size)

        last = self._settings.value('last_file', '')
        if not self._initial_file and last and os.path.isfile(last):
            QTimer.singleShot(50, lambda: self.load_file(last))

    def _save_state(self):
        self._settings.setValue('theme',     self.theme)
        # 最大化时保存最大化前的尺寸，避免下次启动以全屏大小打开
        if self.isMaximized() and self._pre_max_geo is not None:
            self._settings.setValue('pos',  self._pre_max_geo.topLeft())
            self._settings.setValue('size', self._pre_max_geo.size())
        else:
            self._settings.setValue('pos',  self.pos())
            self._settings.setValue('size', self.size())
        self._settings.setValue('last_file', self.current_file)

    def closeEvent(self, e):
        self._save_state()
        super().closeEvent(e)

    # ── 最近文件 ──────────────────────────────────────────────────────────────

    def get_recent_files(self) -> list[str]:
        return self._settings.value('recent_files', []) or []

    def _add_recent(self, path: str):
        recent = self.get_recent_files()
        if path in recent:
            recent.remove(path)
        recent.insert(0, path)
        self._settings.setValue('recent_files', recent[:MAX_RECENT])

    def clear_recent_files(self):
        self._settings.setValue('recent_files', [])

    # ── 快捷键 ────────────────────────────────────────────────────────────────

    def _register_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+O'),       self).activated.connect(self.open_file_dialog)
        QShortcut(QKeySequence('Ctrl+T'),       self).activated.connect(self._cycle_theme)
        QShortcut(QKeySequence('Ctrl+F'),       self).activated.connect(self._toggle_search)
        QShortcut(QKeySequence('Ctrl+H'),       self).activated.connect(self._toggle_replace)
        QShortcut(QKeySequence('Ctrl+P'),       self).activated.connect(self.export_pdf)
        QShortcut(QKeySequence('Ctrl+R'),       self).activated.connect(self._reload_from_disk)
        QShortcut(QKeySequence('Ctrl+E'),       self).activated.connect(self.toggle_edit)
        QShortcut(QKeySequence('Ctrl+S'),       self).activated.connect(self.save_file)
        QShortcut(QKeySequence('Ctrl+Shift+T'), self).activated.connect(self._insert_table_dialog)
        QShortcut(QKeySequence('Escape'),       self).activated.connect(self.search_bar.hide_bar)
        QShortcut(QKeySequence('Alt+Left'),     self).activated.connect(self._nav_back)
        QShortcut(QKeySequence('Alt+Right'),    self).activated.connect(self._nav_forward)

    def _toggle_search(self):
        if self._edit_mode:
            self.search_bar.set_target(self.editor)
        else:
            self.search_bar.set_target(None)
        self.search_bar.show_bar(replace_mode=False)

    def _toggle_replace(self):
        if not self._edit_mode:
            return
        self.search_bar.set_target(self.editor)
        self.search_bar.show_bar(replace_mode=True)

    def _insert_table_dialog(self):
        if not self._edit_mode:
            return
        dlg = QDialog(self)
        dlg.setWindowTitle('插入表格')
        dlg.setFixedWidth(260)
        form = QFormLayout(dlg)
        form.setContentsMargins(16, 16, 16, 12)
        form.setSpacing(10)
        rows_spin = QSpinBox(); rows_spin.setRange(1, 30); rows_spin.setValue(3)
        cols_spin = QSpinBox(); cols_spin.setRange(1, 15); cols_spin.setValue(3)
        form.addRow('行数（含标题行）', rows_spin)
        form.addRow('列数', cols_spin)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        form.addRow(btns)
        if dlg.exec() != QDialog.Accepted:
            return
        rows = rows_spin.value()
        cols = cols_spin.value()
        header    = '| ' + ' | '.join(f'列{i+1}' for i in range(cols)) + ' |'
        separator = '| ' + ' | '.join('---' for _ in range(cols)) + ' |'
        body_rows = ['| ' + ' | '.join('   ' for _ in range(cols)) + ' |'] * max(0, rows - 1)
        table = '\n'.join([header, separator] + body_rows)
        self.editor.insertPlainText('\n' + table + '\n')

    # ── 欢迎页 ────────────────────────────────────────────────────────────────

    def _show_welcome(self):
        welcome_md = f"""# 欢迎使用 {APP_NAME}

**{APP_NAME}** 是一个轻量级本地 Markdown 阅读/编辑器，基于 PySide6 + QWebEngineView，渲染效果接近 GitHub 风格。

支持拖拽 `.md` / `.markdown` / `.mdown` / `.txt` 文件直接打开，或通过 `Ctrl+O` 选择文件。

## 快捷键

### 文件操作

| 快捷键     | 功能                     |
|------------|--------------------------|
| `Ctrl+O`   | 打开文件                 |
| `Ctrl+S`   | 保存 / 另存为            |
| `Ctrl+R`   | 从磁盘重新加载           |
| `Ctrl+P`   | 导出 PDF                 |

### 视图与导航

| 快捷键      | 功能                                   |
|-------------|----------------------------------------|
| `Ctrl+E`    | 切换编辑 / 阅读模式                    |
| `Ctrl+T`    | 循环切换主题（5 种）                   |
| `Ctrl+F`    | 搜索（阅读模式=页内，编辑模式=编辑区） |
| `Ctrl+H`    | 查找替换（仅编辑模式）                 |
| `Ctrl+滚轮` | 缩放预览区                             |

### 编辑格式（编辑模式下）

| 快捷键            | 效果                  | 示例              |
|-------------------|-----------------------|-------------------|
| `Ctrl+B`          | **粗体**              | `**文字**`        |
| `Ctrl+I`          | *斜体*                | `*文字*`          |
| `Ctrl+Shift+S`    | ~~删除线~~            | `~~文字~~`        |
| `Ctrl+Shift+H`    | ==高亮==              | `==文字==`        |
| `Ctrl+Shift+P`    | ^上标^                | `^文字^`          |
| `Ctrl+Shift+B`    | ~下标~                | `~文字~`          |
| `Ctrl+1` ~ `Ctrl+6` | H1 ~ H6 标题       | `# 标题`          |
| `Ctrl+0`          | 取消标题              |                   |
| `Ctrl+Shift+U`    | 无序列表              | `- 项目`          |
| `Ctrl+Shift+O`    | 有序列表              | `1. 项目`         |
| `Ctrl+Shift+T`    | 插入表格（选行列）    |                   |
| `Tab`             | 缩进（4 空格）        |                   |
| `Shift+Tab`       | 取消缩进              |                   |

## Markdown 语法速查

### 标题

```
# 一级标题
## 二级标题
### 三级标题
```

### 强调

```
**粗体**    *斜体*    ~~删除线~~    ==高亮==
```

### 列表

> **注意**：`-` 后面必须有一个空格，列表前需要空一行。

```
- 无序项目
- 无序项目
  - 嵌套项目（两个空格缩进）

1. 有序项目
2. 有序项目
```

### 链接与图片

```
[链接文字](https://example.com)
![图片描述](image.png)
```

> **提示**：编辑模式下可直接将图片文件（`.png/.jpg/.gif` 等）拖入编辑区，自动插入 `![]()` 语法。

### 代码

    行内代码：`code`

    代码块：
    ```python
    print("Hello")
    ```

### 引用与分隔线

```
> 这是一段引用

---
```

### 表格

```
| 列1   | 列2   |
|-------|-------|
| 内容  | 内容  |
```

### 上下标

```
H~2~O（下标）    x^2^（上标）
```

## 主题

点击顶部工具栏的 5 个圆点按钮，或按 `Ctrl+T` 循环切换：

- **默认**（浅白）— 标准 GitHub 风格
- **护眼**（浅绿）— 减少视觉疲劳
- **米黄**（暖黄）— 纸张感阅读
- **暗色**（深蓝）— Tokyo Night 风格
- **夜间**（纯黑）— 极暗背景

---

*版本 {VERSION} · 作者 Red*
"""
        body, toc = render_markdown(welcome_md)
        self.view.setHtml(build_page(body, toc, self.theme, APP_NAME),
                          QUrl(f'file:///{BASE_DIR}/'))

    # ── 文件操作 ──────────────────────────────────────────────────────────────

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '打开 Markdown 文件', '',
            'Markdown 文件 (*.md *.markdown *.mdown *.txt)'
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str, _push_history: bool = True):
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            self.statusBar().showMessage(f'文件不存在：{path}')
            return
        try:
            with open(path, encoding='utf-8-sig') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(path, encoding='gbk', errors='replace') as f:
                text = f.read()

        if self.current_file and self.current_file != path:
            self._watcher.removePath(self.current_file)
        if path not in self._watcher.files():
            self._watcher.addPath(path)

        self.current_file  = path
        self._current_text = text
        if _push_history:
            # 截断前进历史，推入当前路径
            self._nav_history = self._nav_history[:self._nav_idx + 1]
            if not self._nav_history or self._nav_history[-1] != path:
                self._nav_history.append(path)
            self._nav_idx = len(self._nav_history) - 1
        self._modified     = False

        if self._edit_mode:
            self.editor.blockSignals(True)
            self.editor.setPlainText(text)
            self.editor.blockSignals(False)

        self._update_preview()
        self._update_title()
        self._add_recent(path)

        size_kb = max(1, os.path.getsize(path) // 1024)
        self.statusBar().showMessage(
            f'{path}  |  {text.count(chr(10)) + 1} 行  |  {size_kb} KB'
        )

    def save_file(self):
        if not self._edit_mode:
            return
        # 无当前文件则另存为
        if not self.current_file:
            path, _ = QFileDialog.getSaveFileName(
                self, '保存文件', 'untitled.md', 'Markdown 文件 (*.md)'
            )
            if not path:
                return
            self.current_file = path
            self._watcher.addPath(path)
        text = self.editor.toPlainText()
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as ex:
            self.statusBar().showMessage(f'保存失败：{ex}')
            return
        self._current_text = text
        self._modified     = False
        self._update_title()
        self.statusBar().showMessage(f'已保存：{self.current_file}')

    def _reload_from_disk(self):
        if self.current_file:
            self.load_file(self.current_file)

    def _on_file_changed(self, path: str):
        if path == self.current_file and os.path.isfile(path) and not self._modified:
            self.load_file(path)
            if path not in self._watcher.files():
                self._watcher.addPath(path)

    # ── 编辑模式 ──────────────────────────────────────────────────────────────

    def toggle_edit(self):
        self.search_bar.hide_bar()
        if not self._edit_mode:
            self._edit_mode = True
            self.editor.blockSignals(True)
            self.editor.setPlainText(self._current_text)  # 无文件时为空白
            self.editor.blockSignals(False)
            self.editor.setVisible(True)
            w = self.width()
            self.splitter.setSizes([w // 2, w // 2])
            self.editor.setFocus()
        else:
            self._edit_mode = False
            self.editor.setVisible(False)
            self.splitter.setSizes([0, self.width()])
        self.titlebar.set_edit_active(self._edit_mode)

    def _on_editor_changed(self):
        if not self._modified:
            self._modified = True
            self._update_title()
        self._preview_timer.start()
        text  = self.editor.toPlainText()
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        lines = self.editor.blockCount()
        self.statusBar().showMessage(f'{words} 词  ·  {chars} 字符  ·  {lines} 行')

    def _update_preview(self):
        text = self.editor.toPlainText() if self._edit_mode else self._current_text
        if not text and not self.current_file:
            return
        title = os.path.basename(self.current_file) if self.current_file else APP_NAME
        body, toc = render_markdown(text)
        if self.current_file:
            base_url = QUrl.fromLocalFile(os.path.dirname(self.current_file) + '/')
        else:
            base_url = QUrl(f'file:///{BASE_DIR}/')
        self.view.setHtml(build_page(body, toc, self.theme, title), base_url)

    def _update_title(self):
        if self.current_file:
            name   = os.path.basename(self.current_file)
            prefix = '* ' if self._modified else ''
            self.setWindowTitle(f'{prefix}{name} — {APP_NAME}')
            self.titlebar.lbl_title.setText(f'{prefix}{name}')

    # ── 导出 PDF ──────────────────────────────────────────────────────────────

    def export_pdf(self):
        if not self.current_file:
            self.statusBar().showMessage('请先打开一个文件')
            return
        default = os.path.splitext(self.current_file)[0] + '.pdf'
        save_path, _ = QFileDialog.getSaveFileName(self, '导出 PDF', default, 'PDF 文件 (*.pdf)')
        if save_path:
            self.view.page().printToPdf(save_path)
            self.statusBar().showMessage(f'已导出：{save_path}')

    # ── 主题 ──────────────────────────────────────────────────────────────────

    def _cycle_theme(self):
        idx = (THEMES.index(self.theme) + 1) % len(THEMES)
        self.set_theme(THEMES[idx])

    def set_theme(self, theme: str):
        if theme == self.theme:
            return
        self.theme = theme
        self.titlebar.apply_theme(theme)
        self.titlebar.set_edit_active(self._edit_mode)
        self.search_bar.apply_theme(theme)
        self.editor.apply_theme(theme)
        if self.current_file or self._edit_mode:
            self._update_preview()
        else:
            self._show_welcome()

    # ── 拖拽 ──────────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                if u.toLocalFile().lower().endswith(('.md', '.markdown', '.mdown', '.txt')):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for u in event.mimeData().urls():
            path = u.toLocalFile()
            if path.lower().endswith(('.md', '.markdown', '.mdown', '.txt')):
                self.load_file(path)
                break


# ── 入口 ──────────────────────────────────────────────────────────────────────

def main():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('Red.TypeRed.Reader')
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)

    icon = make_app_icon()
    app.setWindowIcon(icon)

    initial_file = sys.argv[1] if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]) else ''
    win = TypeRedWindow(icon, initial_file)
    win.show()

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
