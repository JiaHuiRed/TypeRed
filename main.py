# author Red
# TypeRed — Markdown Reader & Editor v0.7.12
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
#//#260521 Red 0.5.0 行号显示/自动保存30s/TOC拖拽调宽/性能优化(MD复用+渲染缓存)/修复左下角缩放/修复保存触发重载
#//#260522 Red 0.5.1 修复右侧边缘缩放与WebView滚动条重叠（右侧检测边距缩小至4px）
#//#260523 Red 0.5.2 修复正文目录锚点无法跳转（JS优先preventDefault + Python同文件fragment检测）
#//#260601 Red 0.6.4 修复mistune HTML标签转义问题
#//#260528 Red 0.5.6 提取JS和欢迎页到frontend/、文件监听器去重
#//#260601 Red 0.6.0 mistune 替换 markdown 渲染引擎 / 自定义 TOC + 代码高亮渲染器
#//#260601 Red 0.6.1 支持打开 .xmind 思维导图文件（Zen JSON + 旧版 XML 格式）/ 思维导图模式CSS
#//#260601 Red 0.6.2 真毛玻璃：WA_TranslucentBackground + paintEvent半透明背景 + 标题栏/搜索栏/状态栏透明

import sys
import os
import re
import math
import html
import ctypes
import tempfile
import json
import hashlib
from dataclasses import dataclass, field


import emoji
import mistune
from pygments import highlight
from pygments.lexers import get_lexer_by_name
from pygments.formatters import HtmlFormatter

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QLabel, QPushButton, QSizeGrip, QMenu,
    QPlainTextEdit, QSplitter, QLineEdit, QTabBar,
    QDialog, QSpinBox, QFormLayout, QDialogButtonBox, QMessageBox,
    QTextBrowser,
)
from PySide6.QtCore import (
    Qt, QUrl, QPointF, QRectF, QRect, QEvent, QObject,
    QFileSystemWatcher, QSettings, QSize, QPoint, QTimer,
    QThread, Signal,
)
from PySide6.QtGui import (
    QIcon, QDragEnterEvent, QDropEvent, QKeySequence, QShortcut,
    QPainter, QColor, QPixmap, QFont, QPainterPath, QLinearGradient,
    QMouseEvent, QAction, QTextCursor, QTextDocument, QRegion, QDesktopServices, QMovie,
)

VERSION  = "0.7.12"
APP_NAME = "TypeRed"
BASE_DIR = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))


def _cleanup_typered_tmp(path: str) -> None:
    """清理上一次超大页面写入的临时文件，避免堆积。"""
    try:
        if os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass

_TMP_PREVIEW = os.path.join(tempfile.gettempdir(), 'typered_preview.html')
MAX_RECENT = 10
SUPPORTED_EXTS = ('.md', '.markdown', '.mdown', '.txt', '.xmind')
# 渐进渲染阈值：>50KB 启用分块，>256KB 异步渲染
CHUNK_THRESHOLD = 50 * 1024
CHUNK_INITIAL = 5  # 首屏渲染块数

# ── 主题定义 ──────────────────────────────────────────────────────────────────

THEMES      = ['light', 'eye-care', 'cream', 'dark', 'night']
THEME_NAMES = ['默认',  '护眼',    '米黄',  '暗色', '夜间']


# (bg, fg, divider_border, btn_border, btn_fg)
THEME_TB: dict[str, tuple[str, str, str, str, str]] = {
    'light':    ('#f5f5f5', '#1a1a1a', '#d5d5d5', '#999999', '#1a1a1a'),
    'eye-care': ('#d8edd8', '#1a2e1a', '#b8d8b8', '#88bb88', '#1a2e1a'),
    'cream':    ('#e8dcc0', '#2c1f0a', '#ccb888', '#aa8844', '#2c1f0a'),
    'dark':     ('#14151e', '#c0caf5', '#2a2b3d', '#5a5c7e', '#dde0ff'),
    'night':    ('#0d0d0d', '#d0d0d0', '#222222', '#505050', '#f0f0f0'),
}

THEME_DOT: dict[str, str] = {
    'light':    '#a0a0a0',
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

# 编辑器 bg / fg
THEME_EDITOR: dict[str, tuple[str, str]] = {
    'light':    ('#ffffff', '#1a1a1a'),
    'eye-care': ('#f0f7f0', '#1a2e1a'),
    'cream':    ('#fdf6e3', '#2c1f0a'),
    'dark':     ('#1a1b26', '#c0caf5'),
    'night':    ('#0a0a0a', '#cccccc'),
}

# 行号区 bg / fg
THEME_LINENO: dict[str, tuple[str, str]] = {
    'light':    ('#f0f0f2', '#aaaaaa'),
    'eye-care': ('#e4ede4', '#7a9a7a'),
    'cream':    ('#ede4c8', '#a08858'),
    'dark':     ('#13141d', '#5a5e7a'),
    'night':    ('#080808', '#484848'),
}

# ── Tab 数据 ──────────────────────────────────────────────────────────────────

@dataclass
class _TabData:
    """单个标签页的状态快照。"""
    path: str = ''
    text: str = ''
    modified: bool = False
    is_xmind: bool = False
    nav_history: list = field(default_factory=list)
    nav_idx: int = -1
    render_key = None          # _last_render_key 快照，切标签免重渲染


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

class TypeRedRenderer(mistune.HTMLRenderer):
    def __init__(self):
        super().__init__(escape=False)
        self.toc_entries: list[tuple[int, str, str]] = []

    def reset_toc(self):
        self.toc_entries.clear()

    def heading(self, text: str, level: int) -> str:
        slug = re.sub(r'<[^>]+>', '', text)
        slug = re.sub(r'[^\w\u4e00-\u9fff]+', '-', slug).strip('-').lower()
        if not slug:
            slug = 'heading'
        existing = {s for _, s, _ in self.toc_entries}
        base = slug
        i = 1
        while slug in existing:
            slug = f'{base}-{i}'
            i += 1
        self.toc_entries.append((level, slug, text))
        return f'<h{level} id="{slug}">{text}<a class="headerlink" href="#{slug}">\u00b6</a></h{level}>'

    def block_code(self, text: str, info: str | None = None) -> str:
        lang = info.strip().split()[0] if info else ''
        if lang:
            try:
                lexer = get_lexer_by_name(lang)
                highlighted = highlight(text, lexer, HtmlFormatter(nowrap=True))
                return f'<div class="codehilite"><pre><code class="language-{lang}">{highlighted}</code></pre></div>'
            except Exception:
                pass
        text = html.escape(text)
        return f'<div class="codehilite"><pre><code>{text}</code></pre></div>'


def build_toc(entries: list[tuple[int, str, str]]) -> str:
    filtered = [(l, s, t) for l, s, t in entries if 2 <= l <= 4]
    if not filtered:
        return ''
    lines = ['<ul>']
    prev = 2
    for level, slug, text in filtered:
        while level < prev:
            lines.append('</ul></li>')
            prev -= 1
        while level > prev:
            lines.append('<ul>')
            prev += 1
        lines.append(f'<li><a href="#{slug}">{text}</a>')
    while prev > 2:
        lines.append('</ul></li>')
        prev -= 1
    lines.append('</ul>')
    return '\n'.join(lines)


# ── 智能排版替换 ──────────────────────────────────────────────────────────
#//#260601 Red 0.6.5 markdown-it typographer 风格的智能排版 + emoji

_TYPOGRAPH = [
    (r'\.\.\.',              '\u2026'),  # ... → …
    (r'(?<!-)--(?!-)',       '\u2014'),  # -- → — (em dash, not ---)
    (r'-&gt;',               '\u2192'),  # -> → → (HTML-escaped >)
    (r'&lt;-',               '\u2190'),  # <- → ←
    (r'=&gt;',               '\u21d2'),  # => → ⇒
    (r'\(c\)',               '\u00a9'),  # (c) → ©
    (r'\(r\)',               '\u00ae'),  # (r) → ®
    (r'\(tm\)',              '\u2122'),  # (tm) → ™
]

_TAG_BLOCK = re.compile(
    r'(<(pre|code|style|script)[^>]*>.*?</\2>)',
    re.DOTALL | re.IGNORECASE,
)

def _typograph(text: str) -> str:
    """Apply typographic replacements outside code/pre/style blocks."""
    parts = _TAG_BLOCK.split(text)
    for i in range(0, len(parts), 2):
        for pattern, repl in _TYPOGRAPH:
            parts[i] = re.sub(pattern, repl, parts[i])
    return ''.join(parts)


# ── 块级拆分与渐进渲染 ─────────────────────────────────────────────────────────
#//#260615 Red 0.7.7 大文档分块渐进加载

def _chunk_rendered_html(body: str, chunk_size: int = 30) -> list[str]:
    """将渲染后的 HTML 按顶层块级元素切分成块，用于渐进加载。

    通过跟踪标签嵌套深度正确识别顶层元素边界（含 <ul>/<blockquote>/<pre> 等嵌套结构）。
    """
    TOP_TAGS = {'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'div', 'pre',
                'ul', 'ol', 'blockquote', 'table', 'hr', 'figure', 'dl'}
    any_tag = re.compile(r'<(/?)(\w+)[^>]*?(/?)>')

    stack: list[str] = []
    split_points = [0]

    for match in any_tag.finditer(body):
        tag = match.group(2).lower()
        if tag not in TOP_TAGS:
            continue
        is_closing = bool(match.group(1))
        is_self_closing = bool(match.group(3))
        if is_closing:
            if stack and stack[-1] == tag:
                stack.pop()
                if not stack:
                    split_points.append(match.end())
        elif not is_self_closing:
            if not stack:
                # 新顶层元素开始 —— split_points 已在前面记录
                pass
            stack.append(tag)

    blocks = []
    for i in range(len(split_points) - 1):
        blk = body[split_points[i]:split_points[i + 1]].strip()
        if blk:
            blocks.append(blk)
    if split_points and split_points[-1] < len(body):
        trailing = body[split_points[-1]:].strip()
        if trailing:
            blocks.append(trailing)

    return ['\n'.join(blocks[i:i + chunk_size]) for i in range(0, len(blocks), chunk_size)]


def render_chunked(text: str, initial_chunks: int = 5) -> tuple[str, str, str]:
    """分块渲染：全量渲染获取正确 HTML + TOC，然后切块供渐进加载。

    Returns:
        (initial_body_html, remaining_chunks_json, toc_html)
    """
    body, toc = render_markdown(text)
    chunks = _chunk_rendered_html(body)
    if len(chunks) <= initial_chunks + 1:
        return body, '[]', toc
    initial = '\n'.join(chunks[:initial_chunks])
    remaining = json.dumps(chunks[initial_chunks:])
    return initial, remaining, toc


_MD_INSTANCE: mistune.Markdown | None = None


def _get_md_instance() -> mistune.Markdown:
    """获取/创建全局复用的 mistune Markdown 实例。"""
    global _MD_INSTANCE
    if _MD_INSTANCE is None:
        _MD_INSTANCE = _create_md_instance()
    return _MD_INSTANCE


def _render_to_body_toc(text: str, own_md: bool = False) -> tuple[str, str]:
    """共享渲染核心：Markdown → body HTML + TOC。
    
    后台线程渲染时传入 own_md=True，使用独立 mistune 实例避免线程竞态。
    """
    if own_md:
        md = _create_md_instance()
    else:
        md = _get_md_instance()
    md.renderer.reset_toc()
    text = re.sub(r"</?div[^>]*>", "", text)
    body = md(text)
    body = _typograph(body)
    toc = build_toc(md.renderer.toc_entries)
    return body, toc


def render_markdown(text: str) -> tuple[str, str]:
    return _render_to_body_toc(text)


def _create_md_instance():
    """创建独立的 mistune Markdown 实例（线程安全）。"""
    inline = mistune.InlineParser(hard_wrap=True)
    plugins = [mistune.plugins.import_plugin(p) for p in [
        'speedup', 'table', 'footnotes', 'def_list', 'abbr',
        'mark', 'superscript', 'subscript', 'strikethrough',
        'task_lists', 'url',
    ]]
    return mistune.Markdown(
        renderer=TypeRedRenderer(), inline=inline, plugins=plugins,
    )


def _content_fingerprint(text: str) -> str:
    """返回文本的短指纹，替代 hash() 以保证跨进程稳定。"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:16]


def _json_safe_embed(s: str) -> str:
    """将 JSON 字符串安全嵌入 HTML <script> 标签内。"""
    return s.replace('</script>', '<\\/script>').replace('<!--', '<\\!--')


class _ChunkedRenderWorker(QThread):
    """后台线程执行分块 Markdown 渲染（全量 → 切块 → 渐进加载）。"""
    finished = Signal(str, str, str)  # initial_body, remaining_json, toc

    def __init__(self, text: str, title: str, parent=None):
        super().__init__(parent)
        self._text = text
        self._title = title

    def run(self):
        try:
            full_body, toc = _render_to_body_toc(self._text, own_md=True)
            chunks = _chunk_rendered_html(full_body)
            initial = '\n'.join(chunks[:CHUNK_INITIAL])
            remaining = json.dumps(chunks[CHUNK_INITIAL:])
        except Exception as ex:
            #260828 Red 异常文本可能含 < > 等字符，转义后再插进页面，避免破页
            initial, remaining, toc = (
                f'<p style="color:red">渲染失败：{html.escape(str(ex))}</p>', '[]', ''
            )
        self.finished.emit(initial, remaining, toc)


_PYG_CACHE: dict[str, str] = {}


def pygments_css(theme: str) -> str:
    if theme not in _PYG_CACHE:
        try:
            _PYG_CACHE[theme] = HtmlFormatter(style=THEME_PYG.get(theme, 'friendly')).get_style_defs('.codehilite')
        except Exception:
            _PYG_CACHE[theme] = ''
    return _PYG_CACHE[theme]


# ── XMind 思维导图解析 ─────────────────────────────────────────────────────────

def _xmind_to_markdown(path: str) -> str:
    import zipfile, json, xml.etree.ElementTree as ET
    try:
        with zipfile.ZipFile(path) as zf:
            if 'content.json' in zf.namelist():
                data = json.loads(zf.read('content.json'))
                return _xmind_zen_to_md(data)
            if 'content.xml' in zf.namelist():
                tree = ET.parse(zf.open('content.xml'))
                return _xmind_8_to_md(tree)
    except Exception:
        return ''


def _xmind_zen_to_md(data: list) -> str:
    lines = [f'# {APP_NAME} — XMind 思维导图\n']
    for sheet in data:
        root = sheet.get('rootTopic', {})
        _xmind_topic(lines, root, 2)
    return '\n'.join(lines)

def _xmind_topic(lines: list, topic: dict, level: int):
    title = topic.get('title', '').strip()
    note = topic.get('notes', {}).get('plain', {}).get('content', '').strip()
    if title:
        marker = '#' * min(level, 6)
        lines.append(f'{marker} {title}')
        if note:
            for p in note.split('\n'):
                lines.append(f'> {p}')
        lines.append('')
    children = topic.get('children', {}).get('attached', [])
    for child in children:
        _xmind_topic(lines, child, level + 1)

def _xmind_8_to_md(tree) -> str:
    ns = {'x': 'urn:xmind:xmap:xmlns:content:2.0'}
    lines = [f'# {APP_NAME} — XMind 思维导图\n']
    for sheet in tree.findall('.//x:sheet', ns):
        title_el = sheet.find('x:title', ns)
        title = title_el.text.strip() if title_el is not None and title_el.text else ''
        if title:
            lines.append(f'## {title}\n')
        topic = sheet.find('x:topic', ns)
        if topic is not None:
            _xmind_xml_topic(topic, lines, 3, ns)
    return '\n'.join(lines)

def _xmind_xml_topic(topic, lines: list, level: int, ns: dict):
    title_el = topic.find('x:title', ns)
    title = title_el.text.strip() if title_el is not None and title_el.text else ''
    if title:
        marker = '#' * min(level, 6)
        lines.append(f'{marker} {title}')
        lines.append('')
    for child in topic.findall('x:children/x:topics/x:topic', ns):
        _xmind_xml_topic(child, lines, level + 1, ns)


#260828 Red 缓存用 None 做「尚未加载」哨兵：早先判 `not _CSS_CACHE`，读盘失败
# 存 '' 后每次 build_page 都会再试一遍磁盘，文件真丢时变成每帧 IO。
_CSS_CACHE: str | None = None
_JS_CACHE: str | None = None

def _load_css() -> str:
    global _CSS_CACHE
    if _CSS_CACHE is None:
        try:
            with open(os.path.join(BASE_DIR, 'frontend', 'style.css'), encoding='utf-8') as f:
                _CSS_CACHE = f.read()
        except Exception:
            _CSS_CACHE = ''
    return _CSS_CACHE

def _load_js() -> str:
    global _JS_CACHE
    if _JS_CACHE is None:
        try:
            with open(os.path.join(BASE_DIR, 'frontend', 'script.js'), encoding='utf-8') as f:
                _JS_CACHE = f.read()
        except Exception:
            _JS_CACHE = ''
    return _JS_CACHE


def build_page(body: str, toc: str, theme: str, title: str = '', is_xmind: bool = False) -> str:
    css_content = _load_css()
    js_content = _load_js()
    toc_block = f'<nav id="toc">{toc}</nav><div id="toc-resize"></div>' if toc.strip() else ''
    extra_class = f' mindmap' if is_xmind else ''
    return f"""<!DOCTYPE html>
<html class="{theme}{extra_class}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css_content}</style>
<style>{pygments_css(theme)}</style>
</head>
<body>
<div id="layout">
  {toc_block}
  <article id="content">{body}</article>
</div>
<script>{js_content}</script>
</body>
</html>"""


# ── 分块页面生成（渐进加载）────────────────────────────────────────────────

_CHUNKED_JS = r"""
<script>
(function(){
'use strict';
var chunks = %CHUNKS_JSON%;
var idx = 0, loading = false, BUFFER = 600, BATCH = 5;

function loadMore() {
  if (loading || idx >= chunks.length) return;
  var remain = document.body.scrollHeight - (window.innerHeight + window.scrollY);
  if (remain > BUFFER) return;
  loading = true;
  var content = document.getElementById('content');
  if (!content) { loading = false; return; }
  for (var i = 0; i < BATCH && idx < chunks.length; i++, idx++) {
    var d = document.createElement('div');
    d.innerHTML = chunks[idx];
    content.appendChild(d);
  }
  loading = false;
  // 如果加载一批后仍不足视口高度，继续加载
  var r2 = document.body.scrollHeight - (window.innerHeight + window.scrollY);
  if (r2 < BUFFER && idx < chunks.length) loadMore();
}

window.addEventListener('scroll', loadMore, {passive:true});
loadMore();

// TOC 锚点点击时确保目标可见（如果目标在未加载区块中，自动加载到它）
document.querySelectorAll('#toc a').forEach(function(a){
  a.addEventListener('click', function(e){
    var id = this.getAttribute('href').replace(/.*#/, '');
    var el = document.getElementById(id);
    if (el) return;
    // 目标元素不在 DOM 中，逐块加载直到出现
    (function loadUntil(){
      if (idx >= chunks.length) return;
      var content = document.getElementById('content');
      if (!content) return;
      for (var i = 0; i < BATCH && idx < chunks.length; i++, idx++) {
        var d = document.createElement('div');
        d.innerHTML = chunks[idx];
        content.appendChild(d);
      }
      if (!document.getElementById(id)) loadUntil();
    })();
  });
});
})();
</script>
"""


def build_chunked_page(initial_body: str, remaining_json: str, toc: str, theme: str, title: str = '') -> str:
    """构建带渐进加载的分块预览页面。"""
    css_content = _load_css()
    js_content = _load_js()
    toc_block = f'<nav id="toc">{toc}</nav><div id="toc-resize"></div>' if toc.strip() else ''
    # 注入分块 JS（替换占位符，防止 </script> 提前闭合标签）
    loader = _CHUNKED_JS.replace('%CHUNKS_JSON%', _json_safe_embed(remaining_json))
    return f"""<!DOCTYPE html>
<html class="{theme}">
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>{css_content}</style>
<style>{pygments_css(theme)}</style>
<style>
#content-loading {{ text-align:center; padding:2em; color:var(--text-muted); font-size:14px; }}
</style>
</head>
<body>
<div id="layout">
  {toc_block}
  <article id="content">{initial_body}</article>
</div>
<div id="content-loading" style="display:{'none' if remaining_json == '[]' else 'block'}">加载中…</div>
<script>{js_content}</script>
{loader}
</body>
</html>"""


# ── 拖拽过滤器 ────────────────────────────────────────────────────────────────

class DragFilter(QObject):

    def __init__(self, win: 'TypeRedWindow'):
        super().__init__(win)
        self._win = win

    def eventFilter(self, obj, event):
        t = event.type()
        if t == QEvent.Type.DragEnter:
            for u in event.mimeData().urls():
                if u.toLocalFile().lower().endswith(SUPPORTED_EXTS):
                    event.acceptProposedAction()
                    return True
        elif t == QEvent.Type.Drop:
            for u in event.mimeData().urls():
                path = u.toLocalFile()
                if path.lower().endswith(SUPPORTED_EXTS):
                    self._win.load_file(path)
                    return True
        return False



# ── 自定义页面（链接拦截）────────────────────────────────────────────────────

#260526 Red MarkdownPage 移入 _init_view 延迟加载，避免模块级导入 QtWebEngine


# ── 行号区 ────────────────────────────────────────────────────────────────────

class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self._editor = editor

    def sizeHint(self):
        return QSize(self._editor._line_number_width(), 0)

    def paintEvent(self, e):
        self._editor._paint_line_numbers(e)


# ── Markdown 编辑器 ───────────────────────────────────────────────────────────

class Editor(QPlainTextEdit):
    """带 Markdown 格式快捷键的纯文本编辑器。"""
    _IMG_EXTS = ('.png', '.jpg', '.jpeg', '.gif', '.webp', '.bmp', '.svg', '.ico', '.tiff')

    def __init__(self, on_change):
        super().__init__()
        self._on_change = on_change
        self._theme = 'light'
        self.setFont(QFont('Cascadia Code, JetBrains Mono, Consolas, Courier New', 13))
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth)
        self.setTabStopDistance(28)  # 约4个字符宽
        self.textChanged.connect(on_change)

        self._line_num_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_width(0)



    # ── 行号 ──────────────────────────────────────────────────────────────────

    def _line_number_width(self) -> int:
        digits = len(str(max(1, self.blockCount())))
        return 10 + self.fontMetrics().horizontalAdvance('9') * digits

    def _update_line_number_width(self, _):
        self.setViewportMargins(self._line_number_width(), 0, 0, 0)

    def refresh_line_numbers(self):
        """同步 viewportMargins 与行号区 geometry，两者用同一宽度。"""
        w = self._line_number_width()
        self.setViewportMargins(w, 0, 0, 0)
        cr = self.contentsRect()
        self._line_num_area.setGeometry(QRect(cr.left(), cr.top(), w, cr.height()))

    def set_text(self, text: str):
        """整篇替换正文而不触发 on_change，并立刻校正行号宽度。

        #260828 Red blockSignals 会连 blockCountChanged 一起屏蔽，viewportMargins
        因此停在旧行数算出的宽度（空文档=1 位数），而 _line_num_area 的 geometry
        在 resizeEvent 里按实时行数算（几百行=3 位数）。行号区比左边距宽，就会
        压住正文左侧两三个字符（如行首的 **），直到滚动触发 updateRequest 才恢复。
        """
        self.blockSignals(True)
        self.setPlainText(text)
        self.blockSignals(False)
        self.refresh_line_numbers()

    def _update_line_number_area(self, rect, dy):
        if dy:
            self._line_num_area.scroll(0, dy)
        else:
            self._line_num_area.update(0, rect.y(), self._line_num_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self._update_line_number_width(0)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self._line_num_area.setGeometry(
            QRect(cr.left(), cr.top(), self._line_number_width(), cr.height())
        )

    def _paint_line_numbers(self, event):
        painter = QPainter(self._line_num_area)
        bg, fg = THEME_LINENO.get(self._theme, ('#f0f0f2', '#aaaaaa'))
        painter.fillRect(event.rect(), QColor(bg))

        block     = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top    = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())
        line_h = self.fontMetrics().height()

        painter.setFont(self.font())
        painter.setPen(QColor(fg))
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.drawText(
                    QRect(0, top, self._line_num_area.width() - 5, line_h),
                    Qt.AlignRight | Qt.AlignVCenter,
                    str(block_num + 1)
                )
            block = block.next()
            top    = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_num += 1

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
        # Ctrl+Alt+S 删除线
        if e.key() == Qt.Key_S and e.modifiers() == (Qt.ControlModifier | Qt.AltModifier):
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
        self._theme = theme
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
        self._line_num_area.update()

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
        self._btn_normal_style = ''
        self.setFixedHeight(32)
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
        # #260601 Red 0.6.2 标题栏透明，桌面穿透
        _, fg, border, btn_border, _ = THEME_TB[theme]
        self.setStyleSheet(f"""
            TitleBar {{ background: transparent; border-bottom: 1px solid {border}; }}
            #tb_title {{ color: {fg}; font-size: 12px; font-weight: 600; }}
        """)
        self._btn_normal_style = f"""
            QPushButton {{
                background: transparent;
                color: {fg};
                border: 1px solid {btn_border};
                border-radius: 5px;
                font-size: 12px;
                font-weight: 500;
            }}
            QPushButton:hover   {{ background: rgba(128,128,128,0.15); }}
            QPushButton:pressed {{ background: rgba(128,128,128,0.25); }}
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
            if self._btn_normal_style:
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
    _TOG_STYLE = """
        QPushButton {{ background: transparent; color: {fg}; border: 1px solid {border}; border-radius: 4px; font-size: 11px; font-weight: 600; padding: 0; }}
        QPushButton:hover {{ background: rgba(128,128,128,0.15); }}
        QPushButton:checked {{ background: rgba(91,124,247,0.25); border-color: rgba(91,124,247,0.7); color: #3a5ad4; }}
    """

    def __init__(self, win: 'TypeRedWindow', view=None):
        super().__init__(win)
        self._view   = view
        self._win    = win
        self._editor = None
        self._case_sensitive = False
        self._whole_word = False
        self.setVisible(False)

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

        self._btn_case = QPushButton('Aa')
        self._btn_case.setCheckable(True)
        self._btn_case.setFixedSize(26, 26)
        self._btn_case.setToolTip('大小写匹配')
        self._btn_case.toggled.connect(self._on_toggle_changed)
        h1.addWidget(self._btn_case)

        self._btn_word = QPushButton('W')
        self._btn_word.setCheckable(True)
        self._btn_word.setFixedSize(26, 26)
        self._btn_word.setToolTip('全词匹配')
        self._btn_word.toggled.connect(self._on_toggle_changed)
        h1.addWidget(self._btn_word)

        self._toggle_style()

        for label, fn in [('↑', self._prev), ('↓', self._next), ('✕', self.hide_bar)]:
            btn = QPushButton(label)
            btn.setFixedSize(26, 26)
            btn.clicked.connect(fn)
            h1.addWidget(btn)
        vbox.addWidget(row1)

        # 替换行
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

    def _toggle_style(self):
        bg, fg, border, btn_border, _ = THEME_TB[self._win.theme]
        self._btn_case.setStyleSheet(self._TOG_STYLE.format(fg=fg, border=btn_border))
        self._btn_word.setStyleSheet(self._TOG_STYLE.format(fg=fg, border=btn_border))

    def set_view(self, view):
        self._view = view

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
        elif self._view:
            self._view.findText('')
            self._view.setFocus()

    def _editor_flags(self):
        flags = QTextDocument.FindFlag(0)
        if self._case_sensitive:
            flags |= QTextDocument.FindFlag.FindCaseSensitively
        if self._whole_word:
            flags |= QTextDocument.FindFlag.FindWholeWords
        return flags

    def _view_flags(self):
        from PySide6.QtWebEngineCore import QWebEnginePage
        flags = QWebEnginePage.FindFlag(0)
        if self._case_sensitive:
            flags |= QWebEnginePage.FindFlag.FindCaseSensitively
        return flags

    def _on_toggle_changed(self):
        self._case_sensitive = self._btn_case.isChecked()
        self._whole_word = self._btn_word.isChecked()
        self._search(self.input.text())

    def _search(self, text: str):
        if self._editor:
            self._editor.find(text, self._editor_flags())
        elif self._view:
            self._view.findText(text, self._view_flags())

    def _next(self):
        text = self.input.text()
        if self._editor:
            self._editor.find(text, self._editor_flags())
        elif self._view:
            self._view.findText(text, self._view_flags())

    def _prev(self):
        text = self.input.text()
        if self._editor:
            self._editor.find(text, self._editor_flags() | QTextDocument.FindFlag.FindBackward)
        elif self._view:
            from PySide6.QtWebEngineCore import QWebEnginePage
            self._view.findText(text, self._view_flags() | QWebEnginePage.FindFlag.FindBackward)

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
        # 根据大小写/全词开关构建替换模式
        flags = re.IGNORECASE if not self._case_sensitive else 0
        if self._whole_word:
            pattern = r'\b' + re.escape(find_text) + r'\b'
        else:
            pattern = re.escape(find_text)
        new_text, count = re.subn(pattern, replace_text, text, flags=flags)
        if count == 0:
            self._win.statusBar().showMessage('未找到匹配项')
            return
        cur_pos  = self._editor.textCursor().position()
        self._editor.setPlainText(new_text)
        cur = self._editor.textCursor()
        cur.setPosition(min(cur_pos, len(new_text)))
        self._editor.setTextCursor(cur)
        self._win.statusBar().showMessage(f'已替换 {count} 处')

    def apply_theme(self, theme: str):
        # #260601 Red 0.6.2 搜索栏透明，桌面穿透
        bg, fg, border, btn_border, _ = THEME_TB[theme]
        self.setStyleSheet(f"""
            SearchBar {{
                background: transparent;
                border-top: 1px solid rgba(200,200,200,0.3);
            }}
            QLineEdit {{
                background: rgba(255,255,255,0.15);
                color: {fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                padding: 0 6px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                background: rgba(255,255,255,0.25);
                border-color: {btn_border};
            }}
            QPushButton {{
                background: transparent;
                color: {fg};
                border: 1px solid {btn_border};
                border-radius: 4px;
                font-size: 12px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ background: rgba(255,255,255,0.2); }}
        """)
        self._toggle_style()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.hide_bar()
        else:
            super().keyPressEvent(e)


# ── Toast 提示 ────────────────────────────────────────────────────────────────

class Toast(QLabel):
    """轻量级 toast 弹窗，2 秒后自动消失。"""
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setAlignment(Qt.AlignCenter)
        # #260601 Red 0.6.2 Toast 半透明渐变
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(50,50,50,0.82), stop:1 rgba(35,35,35,0.78));
                color: #fff;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                padding: 0 18px;
                font-size: 12px;
            }
        """)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, duration: int = 2000):
        self.setText(text)
        self.adjustSize()
        pw = self.parentWidget()
        if pw:
            x = (pw.width() - self.width()) // 2
            y = pw.height() - self.height() - 40
            self.move(x, y)
        self.show()
        self.raise_()
        self._timer.start(duration)


# ── 边缘缩放覆盖层（纯 Qt，不依赖 Windows API） ──────────────────────────────

class _EdgeOverlay(QWidget):
    """透明覆盖层，`setMask` 只在窗口边缘接收鼠标事件，
       中间区域事件穿透到子部件。处理边缘拖拽缩放。"""
    _MARGIN    = 8   # 上/下/左 边缘宽度
    _MARGIN_R  = 4   # 260522 Red 右侧用更小边距，避免与 WebView 滚动条重叠
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
        m, mr = self._MARGIN, self._MARGIN_R
        full  = QRegion(0, 0, w, h)
        inner = QRegion(m, m, w - m - mr, h - 2*m)  # 260522 Red 右侧用 mr
        self.setMask(full.subtracted(inner))

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._update_mask()

    def _edge_at(self, pos):
        w, h = self.width(), self.height()
        m, mr = self._MARGIN, self._MARGIN_R
        x, y = int(pos.x()), int(pos.y())
        on_l = x <= m; on_r = x >= w - mr - 1  # 260522 Red 右侧检测用 mr
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
        self._restore_last    = ''
        self._cached_text     = ''
        self._last_render_key = None
        self._pending_scroll_ratio = None
        self._skip_next_watch = False
        self._autosave_mtime  = 0.0
        self._is_xmind        = False
        self._render_worker   = None
        self._chunked_worker  = None
        self._tabs: list[_TabData] = []
        self._current_tab_idx = -1
        self._app_icon        = app_icon
        self._settings        = QSettings('Red', APP_NAME)
        self._watcher         = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._on_file_changed)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(400)
        self._preview_timer.timeout.connect(self._update_preview)

        self._autosave_timer = QTimer(self)
        self._autosave_timer.setInterval(30_000)
        self._autosave_timer.timeout.connect(self._autosave)
        self._autosave_timer.start()

        self._status_timer = QTimer(self)
        self._status_timer.setSingleShot(True)
        self._status_timer.setInterval(200)
        self._status_timer.timeout.connect(self._update_status_bar)

        self._build_ui()
        self._restore_state()
        self.setAcceptDrops(True)

    # ── UI 构建 ───────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
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

        self.view = None

        # QTextBrowser 欢迎页——原生 Qt 组件，即时渲染，无需等 WebView
        self._welcome_page = QTextBrowser()
        self._welcome_page.setOpenExternalLinks(True)
        self._welcome_page.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._build_welcome_page()

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setHandleWidth(1)
        self.splitter.addWidget(self.editor)
        self.splitter.addWidget(self._welcome_page)

        #260828 Red 第二参是 view，早先误传了 win 自己：WebView 懒加载完成前
        # _view 指向窗口，搜索栏任何 findText 分支都会 AttributeError 崩掉
        # （无文件启动后 600ms 内按 Ctrl+E / Ctrl+F 即可复现）。留空，等
        # _ensure_view() 里 set_view() 注入真正的 view。
        self.search_bar = SearchBar(self)
        self.search_bar.apply_theme(self.theme)

        self.statusBar().setSizeGripEnabled(False)
        self.statusBar().addPermanentWidget(QSizeGrip(self))
        self.statusBar().setStyleSheet("QStatusBar{background:transparent;}")
        #260609 Red v0.7.0 常驻状态栏
        self._status_label = QLabel(f'{APP_NAME} v{VERSION}  |  拖入 .md 文件或点击「打开」')
        self._status_label.setStyleSheet('color: inherit;')
        self.statusBar().addWidget(self._status_label, 1)

        central = QWidget()
        layout  = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        layout.addWidget(self.titlebar)

        #260609 Red v0.7.0 多标签页
        self.tab_bar = QTabBar()
        self.tab_bar.setTabsClosable(False)  # 自定义红色圆点关闭按钮
        self.tab_bar.setMovable(True)
        self.tab_bar.setDocumentMode(True)
        self.tab_bar.setExpanding(False)
        self.tab_bar.tabMoved.connect(self._rewire_close_btns)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_bar)

        layout.addWidget(self.search_bar)
        layout.addWidget(self.splitter, 1)
        self.setCentralWidget(central)

        #260525 Red 左侧猫猫（阅读/编辑模式都可见）
        cat_path = os.path.join(BASE_DIR, 'frontend', 'mona-loading.gif')
        self._cat_movie = QMovie(cat_path)
        self._cat_movie.setScaledSize(QSize(60, 60))
        self._cat_label = QLabel(central)
        self._cat_label.setFixedSize(64, 64)
        self._cat_label.setMovie(self._cat_movie)
        self._cat_label.setStyleSheet('')
        self._cat_label.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self._cat_movie.start()
        self._cat_movie.stop()

        #260525 Red 猫猫：空闲时 GIF 循环，打字时左右弹跳
        self._cat_bounce_active = False
        self._cat_bounce_phase = 0
        self._cat_bounce_timer = QTimer(self)
        self._cat_bounce_timer.setInterval(60)
        self._cat_bounce_timer.timeout.connect(self._cat_bounce_step)
        self._cat_idle_timer = QTimer(self)
        self._cat_idle_timer.setSingleShot(True)
        self._cat_idle_timer.setInterval(1500)
        self._cat_idle_timer.timeout.connect(self._cat_stop_bounce)
        self._cat_movie.start()
        self.editor.textChanged.connect(self._cat_typing)
        self.editor.cursorPositionChanged.connect(self._sync_preview_from_cursor)
        self.splitter.splitterMoved.connect(self._reposition_cat)

        # 边缘缩放覆盖层（透明，只捕获边缘 8px）
        # 父控件设为主窗口本身，覆盖含 StatusBar 在内的完整窗口区域
        self._edge_overlay = _EdgeOverlay(self, self)
        self._edge_overlay.setGeometry(self.rect())
        self._edge_overlay.show()
        self._edge_overlay.raise_()

        # Toast 提示
        self._toast = Toast(central)

        # #260601 Red 0.6.2 Loading 半透明渐变
        self._loading_overlay = QLabel(' Rendering... ', central)
        self._loading_overlay.setAlignment(Qt.AlignCenter)
        self._loading_overlay.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(248,248,248,0.88), stop:1 rgba(238,238,238,0.84));
                color: #888;
                font-size: 11px;
                border: 1px solid rgba(200,200,200,0.5);
                border-radius: 4px;
                padding: 2px 8px;
            }
        """)
        self._loading_overlay.adjustSize()
        self._loading_overlay.hide()

        self._register_shortcuts()

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

    # ── 多标签页 ──────────────────────────────────────────────────────────────

    def _tab(self) -> _TabData | None:
        """当前标签页数据，无标签时返回 None。"""
        if 0 <= self._current_tab_idx < len(self._tabs):
            return self._tabs[self._current_tab_idx]
        return None

    def _new_tab(self, path: str = '', text: str = '', is_xmind: bool = False) -> _TabData:
        """新建标签页并切换到它。"""
        td = _TabData(path=path, text=text, is_xmind=is_xmind)
        self._tabs.append(td)
        name = os.path.basename(path) if path else 'untitled.md'
        idx = self.tab_bar.addTab(name)
        self._setup_close_btn(idx)
        self._current_tab_idx = len(self._tabs) - 1
        self.tab_bar.setCurrentIndex(self._current_tab_idx)
        return td

    def _setup_close_btn(self, idx: int):
        """给标签页 idx 添加红色圆点关闭按钮。"""
        btn = QPushButton()
        btn.setFixedSize(12, 12)
        btn.setCursor(Qt.ArrowCursor)
        btn.setStyleSheet("""
            QPushButton {
                background: #ff5f57;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: #ff3b30;
            }
            QPushButton:pressed {
                background: #cc2a22;
            }
        """)
        btn.clicked.connect(lambda checked, i=idx: self._close_tab(i))
        self.tab_bar.setTabButton(idx, QTabBar.RightSide, btn)

    def _rewire_close_btns(self):
        """标签拖拽重排后重新挂载关闭按钮。"""
        for i in range(self.tab_bar.count()):
            self._setup_close_btn(i)

    def _close_tab(self, idx: int):
        """关闭指定索引的标签页。"""
        if not (0 <= idx < len(self._tabs)):
            return
        td = self._tabs[idx]
        if td.modified:
            ret = QMessageBox.question(
                self, '未保存的更改',
                f'「{os.path.basename(td.path) if td.path else "untitled.md"}」'
                f'有未保存的更改，是否保存？',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
            )
            if ret == QMessageBox.Save:
                # 同步编辑器最新内容到 td
                if idx == self._current_tab_idx and self._edit_mode:
                    td.text = self.editor.toPlainText()
                path = td.path
                if not path:
                    path, _ = QFileDialog.getSaveFileName(
                        self, '保存', 'untitled.md', 'Markdown 文件 (*.md)'
                    )
                    if not path:
                        return
                try:
                    with open(path, 'w', encoding='utf-8') as f:
                        f.write(td.text)
                except Exception as ex:
                    self.statusBar().showMessage(f'保存失败：{ex}')
                    return
                td.path = path
                td.modified = False
            elif ret == QMessageBox.Cancel:
                return
        self._tabs.pop(idx)
        self.tab_bar.removeTab(idx)
        if self._tabs:
            self._rewire_close_btns()
            new_idx = min(idx, len(self._tabs) - 1)
            self._switch_to_tab(new_idx)
        else:
            self._current_tab_idx = -1
            self.current_file = ''
            self._current_text = ''
            self._modified = False
            self._show_welcome()
            self._update_title()
            self._update_status_bar()

    def _on_tab_changed(self, idx: int):
        """QTabBar.currentChanged 信号。"""
        if idx < 0 or idx >= len(self._tabs):
            return
        self._switch_to_tab(idx)

    def _switch_to_tab(self, idx: int):
        """保存当前标签状态，切到目标标签。"""
        # 保存当前
        old = self._tab()
        if old is not None:
            old.text = self.editor.toPlainText() if self._edit_mode else self._current_text
            old.modified = self._modified
            old.nav_history = self._nav_history[:]
            old.nav_idx = self._nav_idx
            old.render_key = self._last_render_key

        self._suspend_watcher()
        self._current_tab_idx = idx
        td = self._tabs[idx]
        self.current_file = td.path
        self._current_text = td.text
        self._modified = td.modified
        self._is_xmind = td.is_xmind
        if td.path and td.path not in self._watcher.files() and not td.is_xmind:
            self._watcher.addPath(td.path)
        self._nav_history = td.nav_history[:]
        self._nav_idx = td.nav_idx
        self._last_render_key = td.render_key

        if self._edit_mode:
            self.editor.set_text(td.text)

        self._update_preview()
        self._update_title()
        self._update_status_bar()

    def _apply_tab_theme(self, theme: str):
        _, fg, border, _, _ = THEME_TB[theme]
        self.tab_bar.setStyleSheet(f"""
            QTabBar {{
                background: transparent;
                border-bottom: 1px solid {border};
                padding: 0 4px;
                font-size: 12px;
            }}
            QTabBar::tab {{
                background: transparent;
                color: {fg};
                border: none;
                padding: 3px 10px;
                min-width: 40px;
            }}
            QTabBar::tab:selected {{
                border-bottom: 2px solid #5b7cf7;
                color: #5b7cf7;
            }}
            QTabBar::tab:hover {{
                background: rgba(128,128,128,0.1);
            }}
        """)

    def _update_tab_name(self):
        """将当前文件名同步到标签栏。"""
        td = self._tab()
        if td is None or self._current_tab_idx < 0:
            return
        name = os.path.basename(td.path) if td.path else 'untitled.md'
        if td.modified:
            name = '* ' + name
        self.tab_bar.setTabText(self._current_tab_idx, name)

    def _reposition_cat(self):
        cw = self.centralWidget()
        if not cw:
            return
        if self._edit_mode:
            editor_w = self.splitter.widget(0).width()
            x = editor_w + 8
        else:
            x = 8
        self._cat_label.move(x, cw.height() - self._cat_label.height() - 8)

    # #260601 Red 0.6.2 真毛玻璃：半透明背景让桌面穿透
    def paintEvent(self, e):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self.theme in ('dark', 'night'):
            painter.setBrush(QColor(30, 30, 35, 200))
        else:
            painter.setBrush(QColor(245, 245, 245, 210))
        painter.setPen(Qt.NoPen)
        painter.drawRect(self.rect())
        painter.end()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._edge_overlay.setGeometry(self.rect())
        self._reposition_cat()

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

    #260526 Red 延迟初始化 QWebEngineView
    def _init_view(self):
        """懒加载 WebView 并显示初始内容（命令行文件 > 恢复文件 > 欢迎页）。"""
        self._ensure_view()
        if self._initial_file:
            self.load_file(self._initial_file)
        elif self._restore_last:
            self.load_file(self._restore_last)
        elif self.current_file:
            self._update_preview()
        else:
            self._show_welcome()

    # ── 状态持久化 ────────────────────────────────────────────────────────────

    def _restore_state(self):
        theme = self._settings.value('theme', 'light')
        if theme in THEMES:
            self.theme = theme
            self.titlebar.apply_theme(theme)
            self._apply_tab_theme(theme)
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

        self._restore_last = self._settings.value('last_file', '')
        if self._restore_last and not os.path.isfile(self._restore_last):
            self._restore_last = ''

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
        # 先把编辑器最新内容同步到当前标签
        cur = self._tab()
        if cur is not None and self._edit_mode:
            cur.text = self.editor.toPlainText()
            cur.modified = self._modified

        # 收集所有未保存的标签
        unsaved = [i for i, td in enumerate(self._tabs) if td.modified]
        if not unsaved:
            self._save_state()
            super().closeEvent(e)
            return

        # 逐个询问
        for idx in unsaved:
            td = self._tabs[idx]
            name = os.path.basename(td.path) if td.path else 'untitled.md'
            ret = QMessageBox.question(
                self, '未保存的更改',
                f'「{name}」有未保存的更改，是否保存？',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save,
            )
            if ret == QMessageBox.Save:
                if idx != self._current_tab_idx:
                    self._switch_to_tab(idx)
                self.save_file()
                if self._modified:
                    e.ignore()
                    return
            elif ret == QMessageBox.Cancel:
                e.ignore()
                return
            # Discard → 继续下一个

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


    def _goto_line(self):
        """Ctrl+G 跳转到指定行"""
        if not self._edit_mode:
            return
        from PySide6.QtWidgets import QInputDialog
        total = self.editor.blockCount()
        line, ok = QInputDialog.getInt(
            self, '跳转到行', f'行号 (1-{total}):',
            self.editor.textCursor().blockNumber() + 1, 1, total
        )
        if ok:
            cursor = self.editor.textCursor()
            cursor.movePosition(cursor.MoveOperation.Start)
            cursor.movePosition(cursor.MoveOperation.Down, cursor.MoveMode.MoveAnchor, line - 1)
            self.editor.setTextCursor(cursor)
            self.editor.centerCursor()

    def _register_shortcuts(self):
        QShortcut(QKeySequence('Ctrl+N'),       self).activated.connect(self._new_file)
        QShortcut(QKeySequence('Ctrl+O'),       self).activated.connect(self.open_file_dialog)
        QShortcut(QKeySequence('Ctrl+T'),       self).activated.connect(self._cycle_theme)
        QShortcut(QKeySequence('Ctrl+F'),       self).activated.connect(self._toggle_search)
        QShortcut(QKeySequence('Ctrl+H'),       self).activated.connect(self._toggle_replace)
        QShortcut(QKeySequence('Ctrl+P'),       self).activated.connect(self.export_pdf)
        QShortcut(QKeySequence('Ctrl+R'),       self).activated.connect(self._reload_from_disk)
        QShortcut(QKeySequence('Ctrl+E'),       self).activated.connect(self.toggle_edit)
        QShortcut(QKeySequence('Ctrl+S'),       self).activated.connect(self.save_file)
        QShortcut(QKeySequence('Ctrl+Shift+S'), self).activated.connect(self._save_as_file)
        QShortcut(QKeySequence('Ctrl+Shift+T'), self).activated.connect(self._insert_table_dialog)
        QShortcut(QKeySequence('Escape'),       self).activated.connect(self.search_bar.hide_bar)
        QShortcut(QKeySequence('Ctrl+G'),       self).activated.connect(self._goto_line)
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

    def _build_welcome_page(self):
        """用 QTextBrowser 渲染欢迎页（原生 Qt，无需 WebView，即时显示）。"""
        welcome_md = self._load_welcome_md()
        if not welcome_md:
            self._welcome_page.setPlainText(f'Welcome to {APP_NAME}')
            return
        body, toc = render_markdown(welcome_md)
        css_content = _load_css()
        toc_block = f'<nav id="toc">{toc}</nav>' if toc.strip() else ''
        html = f"""<!DOCTYPE html>
<html class="{self.theme}">
<head><meta charset="utf-8"><title>{APP_NAME}</title>
<style>{css_content}</style>
<style>{pygments_css(self.theme)}</style>
</head>
<body><div id="layout">{toc_block}<article id="content">{body}</article></div></body>
</html>"""
        self._welcome_page.setHtml(html)

    # ── 懒加载 WebView ────────────────────────────────────────────────────────

    def _ensure_view(self):
        """按需创建 QWebEngineView，替换 QTextBrowser 欢迎页。"""
        if self.view is not None:
            return
        from PySide6.QtWebEngineWidgets import QWebEngineView
        from PySide6.QtWebEngineCore import QWebEnginePage
        class _Page(QWebEnginePage):
            def __init__(self, win, parent=None):
                super().__init__(parent)
                self._win = win
            def acceptNavigationRequest(self, url, nav_type, _is_main):
                if nav_type == QWebEnginePage.NavigationType.NavigationTypeLinkClicked:
                    path = url.toLocalFile()
                    if path:
                        fragment = url.fragment()
                        if fragment and os.path.normpath(path) == self._win.current_file:
                            js = f'(function(){{var e=document.getElementById("{fragment}");if(e)e.scrollIntoView({{behavior:"smooth"}})}})();'
                            QTimer.singleShot(0, lambda s=js: self._win.view.page().runJavaScript(s))
                            return False
                        QTimer.singleShot(0, lambda p=path: self._win.load_file(p))
                        return False
                    if url.scheme() in ('http', 'https'):
                        QTimer.singleShot(0, lambda u=url: QDesktopServices.openUrl(u))
                        return False
                return True
        self.view = QWebEngineView()
        self.view.setPage(_Page(self, self.view))
        self.view.setAcceptDrops(False)
        self._drag_filter = DragFilter(self)
        self.view.installEventFilter(self._drag_filter)
        self._view_ready = True
        idx = self.splitter.indexOf(self._welcome_page)
        self.splitter.insertWidget(idx, self.view)
        self._welcome_page.hide()
        self._welcome_page.deleteLater()
        self._welcome_page = None
        self.search_bar.set_view(self.view)

    def _load_welcome_md(self) -> str:
        try:
            with open(os.path.join(BASE_DIR, 'frontend', 'welcome.md'), encoding='utf-8') as f:
                md = f.read()
        except Exception:
            return ''
        return md.replace('__APP_NAME__', APP_NAME).replace('__VERSION__', VERSION)

    def _show_welcome(self):
        welcome_md = self._load_welcome_md()
        if not welcome_md:
            return
        # 如果在 WebView 尚未就绪时被调用，直接返回（QTextBrowser 已显示欢迎页）
        if self.view is None:
            return
        body, toc = render_markdown(welcome_md)
        self.view.setHtml(build_page(body, toc, self.theme, APP_NAME),
                          QUrl(f'file:///{BASE_DIR}/'))

    # ── 文件监听器辅助 ────────────────────────────────────────────────────────

    def _suspend_watcher(self):
        if self.current_file and self.current_file in self._watcher.files():
            self._watcher.removePath(self.current_file)

    def _resume_watcher(self):
        if self.current_file and self.current_file not in self._watcher.files():
            self._watcher.addPath(self.current_file)

    # ── 文件操作 ──────────────────────────────────────────────────────────────

    def open_file_dialog(self):
        path, _ = QFileDialog.getOpenFileName(
            self, '打开 Markdown / XMind 文件', '',
            'Markdown / XMind 文件 (*.md *.markdown *.mdown *.txt *.xmind)'
        )
        if path:
            self.load_file(path)

    def load_file(self, path: str, _push_history: bool = True):
        path = os.path.normpath(path)
        if not os.path.isfile(path):
            self.statusBar().showMessage(f'文件不存在：{path}')
            return

        # 标签页：已打开则切过去
        norm = os.path.normcase(path)
        for i, td in enumerate(self._tabs):
            if td.path and os.path.normcase(td.path) == norm:
                self.tab_bar.setCurrentIndex(i)
                return

        # 保存当前标签状态
        old = self._tab()
        if old is not None:
            old.text = self.editor.toPlainText() if self._edit_mode else self._current_text
            old.modified = self._modified
            old.nav_history = self._nav_history[:]
            old.nav_idx = self._nav_idx

        # 复用 untitled 空标签或新建
        reuse = (old is not None and not old.path and not old.modified)
        if not reuse:
            td = self._new_tab()
        else:
            td = old

        ext = os.path.splitext(path)[1].lower()
        if ext == '.xmind':
            text = _xmind_to_markdown(path)
            if not text:
                if not reuse:
                    self._close_tab(self._current_tab_idx)
                self.statusBar().showMessage('无法解析 XMind 文件')
                return
            td.is_xmind = True
        else:
            try:
                with open(path, encoding='utf-8-sig') as f:
                    text = f.read()
            except UnicodeDecodeError:
                with open(path, encoding='gbk', errors='replace') as f:
                    text = f.read()
            td.is_xmind = False

        # 在存储/渲染前一次性完成 emoji 短代码替换，避免每次渲染重复处理
        text = emoji.emojize(text, language='alias')

        self._suspend_watcher()
        if path not in self._watcher.files() and not td.is_xmind:
            self._watcher.addPath(path)

        td.path   = path
        td.text   = text
        td.modified = False
        if _push_history:
            td.nav_history = td.nav_history[:td.nav_idx + 1]
            if not td.nav_history or td.nav_history[-1] != path:
                td.nav_history.append(path)
            td.nav_idx = len(td.nav_history) - 1

        # 读取到实例变量（下游方法依赖这些）
        self.current_file  = path
        self._current_text = text
        self._modified     = False
        self._is_xmind     = td.is_xmind
        self._nav_history  = td.nav_history[:]
        self._nav_idx      = td.nav_idx

        if self._edit_mode:
            self.editor.set_text(text)

        self._update_preview()
        self._update_title()
        self._update_tab_name()
        self._update_status_bar()
        self._add_recent(path)

    def save_file(self):
        if not self._edit_mode:
            return
        # 无当前文件则另存为
        if not self.current_file:
            self._save_as_file()
            return
        text = self.editor.toPlainText()
        try:
            self._suspend_watcher()
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as ex:
            self._resume_watcher()
            self.statusBar().showMessage(f'保存失败：{ex}')
            return
        self._resume_watcher()
        self._current_text = text
        self._modified     = False
        td = self._tab()
        if td:
            td.text = text
            td.modified = False
        self._update_title()
        self._update_status_bar()
        self.statusBar().showMessage(f'已保存：{os.path.basename(self.current_file)}')
        self._toast.show_message(f'已保存：{os.path.basename(self.current_file)}')

    def _save_as_file(self):
        path, _ = QFileDialog.getSaveFileName(
            self, '另存为', self.current_file or 'untitled.md', 'Markdown 文件 (*.md)'
        )
        if not path:
            return False
        self.current_file = path
        if path not in self._watcher.files():
            self._watcher.addPath(path)
        text = self.editor.toPlainText()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception as ex:
            self.statusBar().showMessage(f'保存失败：{ex}')
            return False
        self._current_text = text
        self._modified     = False
        td = self._tab()
        if td:
            td.path = path
            td.text = text
            td.modified = False
        self._update_title()
        self._update_tab_name()
        self._add_recent(path)
        self._update_status_bar()
        self.statusBar().showMessage(f'已保存：{path}')
        self._toast.show_message(f'已保存：{os.path.basename(path)}')
        return True

    def _new_file(self):
        """新建空白 untitled 标签页，自动切编辑模式。"""
        td = self._tab()
        if td is not None:
            td.text = self.editor.toPlainText() if self._edit_mode else self._current_text
            td.modified = self._modified
            if td.modified:
                ret = QMessageBox.question(
                    self, '未保存的更改',
                    f'「{os.path.basename(td.path) if td.path else "untitled.md"}」'
                    f'有未保存的更改，是否保存？',
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                )
                if ret == QMessageBox.Save:
                    self.save_file()
                    if self._modified:
                        return
                elif ret == QMessageBox.Cancel:
                    return

        self._suspend_watcher()
        td = self._new_tab(text='')
        self.current_file  = ''
        self._current_text = ''
        self._modified     = False
        self._is_xmind     = False

        self._edit_mode = True
        self.editor.set_text('')
        self.editor.setVisible(True)
        self.splitter.setSizes([self.width() // 2, self.width() // 2])
        self.editor.setFocus()
        self.titlebar.set_edit_active(True)
        self._update_title()
        self._update_tab_name()
        self._update_status_bar()
        self._reposition_cat()
        self._cat_movie.start()

    def _reload_from_disk(self):
        if self.current_file:
            self.load_file(self.current_file)

    def _autosave(self):
        if not (self._edit_mode and self._modified and self.current_file):
            return
        text = self.editor.toPlainText()
        try:
            self._suspend_watcher()
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(text)
        except Exception:
            self._resume_watcher()
            return
        self._resume_watcher()
        self._skip_next_watch = True
        try:
            self._autosave_mtime = os.path.getmtime(self.current_file)
        except OSError:
            self._autosave_mtime = 0.0
        self._current_text = text
        self._modified = False
        td = self._tab()
        if td:
            td.text = text
            td.modified = False
        self._update_title()
        self.statusBar().showMessage(
            f'自动保存：{os.path.basename(self.current_file)}', 2000
        )

    def _on_file_changed(self, path: str):
        if path != self.current_file or not os.path.isfile(path):
            return
        if self._modified:
            return
        # 跳过 autosave 自身触发的变更
        if self._skip_next_watch:
            self._skip_next_watch = False
            if path not in self._watcher.files():
                self._watcher.addPath(path)
            return
        # 防止 autosave 后外部修改被跳过：基于修改时间判断
        try:
            current_mtime = os.path.getmtime(path)
        except OSError:
            return
        if current_mtime <= self._autosave_mtime:
            if path not in self._watcher.files():
                self._watcher.addPath(path)
            return
        # 显示提示而非静默覆盖
        self.statusBar().showMessage(
            '文件已被外部修改 — Ctrl+R 刷新', 8000
        )

    # ── 编辑模式 ──────────────────────────────────────────────────────────────

    def toggle_edit(self):
        self.search_bar.hide_bar()
        if not self._edit_mode:
            self._edit_mode = True
            self.editor.set_text(self._current_text)  # 无文件时为空白
            self.editor.setVisible(True)
            w = self.width()
            self.splitter.setSizes([w // 2, w // 2])
            self.editor.setFocus()
        else:
            self._edit_mode = False
            text = self._cached_text or self.editor.toPlainText()
            self._current_text = text
            td = self._tab()
            if td:
                td.text = text
            self.editor.setVisible(False)
            self.splitter.setSizes([0, self.width()])
        self.titlebar.set_edit_active(self._edit_mode)
        if self._edit_mode:
            self._reposition_cat()
            self._cat_movie.start()
        else:
            self._cat_bounce_active = False
            self._cat_bounce_timer.stop()
            self._cat_idle_timer.stop()
            self._reposition_cat()
            self._cat_movie.start()

    def _cat_typing(self):
        if not self._edit_mode:
            return
        if not self._cat_bounce_active:
            self._cat_bounce_active = True
            self._cat_bounce_phase = 0
            self._cat_movie.stop()
            self._cat_bounce_timer.start()
        self._cat_idle_timer.start()

    def _cat_stop_bounce(self):
        self._cat_bounce_active = False
        self._cat_bounce_timer.stop()
        self._reposition_cat()
        self._cat_movie.start()

    def _cat_bounce_step(self):
        if not self._cat_bounce_active:
            return
        self._cat_bounce_phase += 1
        offset = math.sin(self._cat_bounce_phase * 0.25) * 10
        cw = self.centralWidget()
        if cw:
            if self._edit_mode:
                base_x = self.splitter.widget(0).width() + 8
            else:
                base_x = 8
            self._cat_label.move(int(base_x + offset), cw.height() - self._cat_label.height() - 8)

    def _on_editor_changed(self):
        if not self._modified:
            self._modified = True
            td = self._tab()
            if td:
                td.modified = True
            self._update_title()
        self._preview_timer.start()
        # 缓存 toPlainText 避免 _update_preview 重复调用
        self._cached_text = self.editor.toPlainText()
        self._status_timer.start()

    def _update_status_bar(self):
        #260828 Red 编辑中 _current_text 只在 load/save/切标签时更新，实时文本在
        # 编辑器里。原先一律读 _current_text，导致打字时行数/词数/字符数卡在上次
        # 保存的值（新建文档更是一直停在欢迎语）。这里直接问编辑器要当前内容——
        # 本方法有 200ms 去抖，不走 _cached_text 是为了避免切标签后残留旧文本。
        text = self.editor.toPlainText() if self._edit_mode else self._current_text
        if not self.current_file and not text:
            self._status_label.setText(
                f'{APP_NAME} v{VERSION}  |  拖入 .md 文件或点击「打开」'
            )
            return
        path = self.current_file
        fmt = 'XMind' if self._is_xmind else 'Markdown'
        size_kb = max(1, os.path.getsize(path) // 1024) if path and os.path.isfile(path) else 0
        lines = text.count('\n') + 1
        chars = len(text)
        words = len(text.split()) if text.strip() else 0
        self._status_label.setText(
            f'{os.path.basename(path) if path else "untitled.md"}'
            f'  |  {fmt}  |  {lines} 行  |  {size_kb} KB'
            f'  |  {words} 词  ·  {chars} 字符'
        )

    def _sync_preview_scroll(self):
        ratio = self._pending_scroll_ratio
        if ratio is None:
            return
        self._pending_scroll_ratio = None
        if not self.view:
            return
        js = f'''
            var ms = Math.max(0, document.body.scrollHeight - window.innerHeight);
            window.scrollTo(0, ms * {ratio});
        '''
        self.view.page().runJavaScript(js)

    def _sync_preview_from_cursor(self):
        if not self._edit_mode:
            return
        text = self._cached_text or self.editor.toPlainText()
        if not text:
            return
        ratio = self.editor.textCursor().position() / max(len(text), 1)
        self._pending_scroll_ratio = ratio
        QTimer.singleShot(50, self._sync_preview_scroll)

    def _update_preview(self):
        self._ensure_view()
        if self._edit_mode:
            text = self._cached_text or self.editor.toPlainText()
        else:
            text = self._current_text
        if not text and not self.current_file:
            return
        title = os.path.basename(self.current_file) if self.current_file else APP_NAME
        # 用 len+指纹 双重校验代替全文比较（hash() 跨进程不稳定）
        key = (self.theme, title, len(text), _content_fingerprint(text))
        if key == self._last_render_key:
            self._sync_preview_from_cursor()
            return
        self._last_render_key = key
        if self._edit_mode:
            self._pending_scroll_ratio = self.editor.textCursor().position() / max(len(text), 1)
        else:
            self._pending_scroll_ratio = None
        self._set_loading_theme()
        self._loading_overlay.move(self._loading_overlay.parent().width() - self._loading_overlay.width() - 20, 44)
        self._loading_overlay.show()
        self._loading_overlay.raise_()
        self._loading_overlay.repaint()

        # 三级渲染策略：
        #   小文件 ≤50KB  → 同步全量渲染
        #   中文件 50K-256K → 同步分块渲染（首屏快）
        #   大文件 >256KB  → 后台线程分块渲染（UI 不冻结）
        if len(text) > 256 * 1024:
            self._start_chunked_async_render(text, title)
        elif len(text) > CHUNK_THRESHOLD:
            try:
                body, remaining, toc = render_chunked(text, initial_chunks=CHUNK_INITIAL)
            except Exception as ex:
                self._loading_overlay.hide()
                self.statusBar().showMessage(f'渲染失败：{ex}')
                return
            self._apply_chunked_result(body, remaining, toc, title)
        else:
            try:
                body, toc = render_markdown(text)
            except Exception as ex:
                self._loading_overlay.hide()
                self.statusBar().showMessage(f'渲染失败：{ex}')
                return
            self._apply_render_result(body, toc, title)

    def _start_chunked_async_render(self, text: str, title: str):
        """后台线程分块渲染，避免大文件阻塞 UI。"""
        old = self._chunked_worker
        if old is not None and old.isRunning():
            old.finished.disconnect()
            old.quit()
            old.wait(200)
        worker = _ChunkedRenderWorker(text, title, parent=self)
        worker.finished.connect(self._on_chunked_render_done)
        self._chunked_worker = worker
        worker.start()

    def _apply_render_result(self, body, toc, title):
        """应用全量渲染结果到 WebView（0.7.6 旧路径）。"""
        self._loading_overlay.hide()
        if not self.view:
            return
        page_html = build_page(body, toc, self.theme, title, is_xmind=self._is_xmind)
        self._set_page_html(page_html)

    def _apply_chunked_result(self, body, remaining_json, toc, title):
        """应用分块渲染结果到 WebView。"""
        self._loading_overlay.hide()
        if not self.view:
            return
        page_html = build_chunked_page(body, remaining_json, toc, self.theme, title)
        self._set_page_html(page_html)

    def _set_page_html(self, page_html: str):
        """统一 setHtml / load 分发，处理 Chromium 2MB 限制。"""
        try:
            if len(page_html) > 1_500_000:
                if self.current_file:
                    base_dir = os.path.dirname(self.current_file).replace('\\', '/')
                    base_tag = f'<base href="file:///{base_dir}/">'
                else:
                    base_tag = f'<base href="file:///{BASE_DIR}/">'
                page_html = page_html.replace('<head>', f'<head>{base_tag}', 1)
                tmp = _TMP_PREVIEW
                _cleanup_typered_tmp(tmp)
                with open(tmp, 'w', encoding='utf-8') as f:
                    f.write(page_html)
                self.view.load(QUrl.fromLocalFile(tmp))
            else:
                if self.current_file:
                    base_url = QUrl.fromLocalFile(os.path.dirname(self.current_file) + '/')
                else:
                    base_url = QUrl(f'file:///{BASE_DIR}/')
                self.view.setHtml(page_html, base_url)
        except Exception as ex:
            self.statusBar().showMessage(f'渲染失败：{ex}')
            return
        if self._pending_scroll_ratio is not None:
            QTimer.singleShot(120, self._sync_preview_scroll)

    def _on_chunked_render_done(self, body: str, remaining: str, toc: str):
        """后台分块渲染完成，自动读取标题。"""
        title = os.path.basename(self.current_file) if self.current_file else APP_NAME
        self._apply_chunked_result(body, remaining, toc, title)

    def _update_title(self):
        if self.current_file:
            name   = os.path.basename(self.current_file)
            prefix = '* ' if self._modified else ''
            self.setWindowTitle(f'{prefix}{name} — {APP_NAME}')
            self.titlebar.lbl_title.setText(f'{prefix}{name}')
        else:
            self.setWindowTitle(f'{APP_NAME} v{VERSION}')
            self.titlebar.lbl_title.setText(APP_NAME)
        self._update_tab_name()

    # ── 导出 PDF ──────────────────────────────────────────────────────────────

    def export_pdf(self):
        if not self.current_file:
            self.statusBar().showMessage('请先打开一个文件')
            return
        self._ensure_view()
        default = os.path.splitext(self.current_file)[0] + '.pdf'
        save_path, _ = QFileDialog.getSaveFileName(self, '导出 PDF', default, 'PDF 文件 (*.pdf)')
        if save_path and self.view:
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
        self._apply_tab_theme(theme)
        self._set_loading_theme()
        #260525 Red 猫猫边框跟随主题
        _, _, border, _, _ = THEME_TB[theme]
        self._cat_label.setStyleSheet('border-radius: 10px;')
        if self.current_file or self._edit_mode:
            self._update_preview()
        else:
            if self.view:
                self._show_welcome()
            elif self._welcome_page:
                self._build_welcome_page()

    def _set_loading_theme(self):
        """Loading 覆盖层跟随主题。"""
        if self.theme in ('dark', 'night'):
            bg0, bg1, clr, bdr = 'rgba(20,20,30,0.88)', 'rgba(15,15,25,0.84)', '#8888aa', 'rgba(60,60,80,0.5)'
        else:
            bg0, bg1, clr, bdr = 'rgba(248,248,248,0.88)', 'rgba(238,238,238,0.84)', '#888', 'rgba(200,200,200,0.5)'
        self._loading_overlay.setStyleSheet(f"""
            QLabel {{
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 {bg0}, stop:1 {bg1});
                color: {clr};
                font-size: 11px;
                border: 1px solid {bdr};
                border-radius: 4px;
                padding: 2px 8px;
            }}
        """)

    # ── 拖拽 ──────────────────────────────────────────────────────────────────

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            for u in event.mimeData().urls():
                if u.toLocalFile().lower().endswith(SUPPORTED_EXTS):
                    event.acceptProposedAction()
                    return

    def dropEvent(self, event: QDropEvent):
        for u in event.mimeData().urls():
            path = u.toLocalFile()
            if path.lower().endswith(SUPPORTED_EXTS):
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
    # 有文件参数时提前初始化 WebView 以便加载内容；无文件时即刻弹窗（QTextBrowser 欢迎页）
    if initial_file:
        win._init_view()
    win.show()
    # 无文件时后台懒加载 WebView，用户感知不到
    if not initial_file:
        QTimer.singleShot(600, win._init_view)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
