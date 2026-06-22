/* author Red */
/* TypeRed — Markdown Reader & Editor v0.7.7 — 事件委托版 */
/* 使用事件委托支持动态加载的内容块 */

(function() {
  'use strict';

  // ── TOC 锚点跳转 ──
  var toc = document.getElementById('toc');
  if (toc) {
    toc.addEventListener('click', function(e) {
      var a = e.target.closest('a[href^="#"]');
      if (!a) return;
      e.preventDefault();
      var id = a.getAttribute('href').replace(/.*#/, '');
      var el = document.getElementById(id);
      if (el) { el.scrollIntoView({behavior:'smooth'}); }
    });
  }

  // ── TOC 当前标题高亮（IntersectionObserver） ──
  (function() {
    var tocLinks = toc ? toc.querySelectorAll('a[href^="#"]') : [];
    if (!tocLinks.length) return;
    var headings = [];
    tocLinks.forEach(function(a) {
      var id = a.getAttribute('href').replace(/.*#/, '');
      var el = document.getElementById(id);
      if (el) headings.push({el: el, link: a});
    });
    if (!headings.length) return;
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          tocLinks.forEach(function(a) { a.classList.remove('active'); });
          var h = headings.find(function(h) { return h.el === entry.target; });
          if (h) h.link.classList.add('active');
        }
      });
    }, {rootMargin: '-64px 0px -60% 0px'});
    headings.forEach(function(h) { observer.observe(h.el); });
  })();

  // ── TOC 拖拽调整宽度 ──
  (function() {
    var handle = document.getElementById('toc-resize');
    if (!handle) return;
    var dragging = false, startX = 0, startW = 0;
    handle.addEventListener('mousedown', function(e) {
      dragging = true; startX = e.clientX; startW = toc.offsetWidth;
      handle.classList.add('dragging');
      document.body.style.userSelect = 'none';
      e.preventDefault();
    });
    document.addEventListener('mousemove', function(e) {
      if (!dragging) return;
      var w = Math.max(120, Math.min(480, startW + e.clientX - startX));
      toc.style.width = w + 'px';
      toc.style.minWidth = w + 'px';
    });
    document.addEventListener('mouseup', function() {
      if (!dragging) return;
      dragging = false;
      handle.classList.remove('dragging');
      document.body.style.userSelect = '';
    });
  })();

  // ── 可点击任务列表复选框（事件委托） ──
  var content = document.getElementById('content');
  if (content) {
    content.addEventListener('change', function(e) {
      if (e.target.matches('.task-list-item input[type="checkbox"]')) {
        /* 状态变化已自动反映在 checked 属性上 */
      }
    });
  }

  // ── 图片点击放大遮罩层（事件委托） ──
  (function() {
    var overlay = document.createElement('div');
    overlay.id = 'img-overlay';
    overlay.innerHTML = '<span class="img-close">&times;</span><img src="" alt="">';
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay || e.target.classList.contains('img-close')) {
        overlay.classList.remove('active');
      }
    });
    document.body.appendChild(overlay);

    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && overlay.classList.contains('active')) {
        overlay.classList.remove('active');
      }
    });

    // 事件委托：content 内的任何 img 点击
    if (content) {
      content.addEventListener('click', function(e) {
        var img = e.target.closest('img');
        if (!img) return;
        if (img.closest('.img-close')) return;
        e.stopPropagation();
        overlay.querySelector('img').src = img.src;
        overlay.querySelector('img').alt = img.alt;
        overlay.classList.add('active');
      });
    }
  })();

})();
