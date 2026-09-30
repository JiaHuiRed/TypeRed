/* author Red */
/* TypeRed — Markdown Reader & Editor v0.8.3 — 事件委托版 */
/* 使用事件委托支持动态加载的内容块 */

(function() {
  'use strict';

  // #260828 Red 0.8.0 尊重系统「减少动态效果」
  var reduceMotion = window.matchMedia &&
    window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var scrollOpts = reduceMotion ? {behavior: 'auto'} : {behavior: 'smooth'};

  // ── TOC 锚点跳转 ──
  var toc = document.getElementById('toc');
  if (toc) {
    toc.addEventListener('click', function(e) {
      var a = e.target.closest('a[href^="#"]');
      if (!a) return;
      e.preventDefault();
      var id = a.getAttribute('href').replace(/.*#/, '');
      var el = document.getElementById(id);
      if (el) { el.scrollIntoView(scrollOpts); }
    });
  }

  // ── TOC 当前标题高亮（IntersectionObserver，覆盖分块后插入的标题） ──
  (function() {
    var tocLinks = toc ? toc.querySelectorAll('a[href^="#"]') : [];
    if (!tocLinks.length) return;
    var linkById = {};
    tocLinks.forEach(function(a) {
      var id = a.getAttribute('href').replace(/.*#/, '');
      linkById[id] = a;
    });
    var activeLink = null;
    function activate(link) {
      if (activeLink === link) return;
      if (activeLink) activeLink.classList.remove('active');
      activeLink = link;
      if (link) link.classList.add('active');
    }
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) activate(linkById[entry.target.id]);
      });
    }, {rootMargin: '-64px 0px -60% 0px'});
    function watch(el) {
      if (el.__tocObserved || !linkById[el.id]) return;
      el.__tocObserved = true;
      observer.observe(el);
    }
    var HEADING_SEL = '#content h1, #content h2, #content h3, #content h4, #content h5, #content h6';
    function watchAll() {
      document.querySelectorAll(HEADING_SEL).forEach(watch);
    }
    watchAll();
    //260930 Red 分块加载会陆续插入标题，用 MutationObserver 补挂观察器
    var content = document.getElementById('content');
    if (content) {
      new MutationObserver(watchAll).observe(content, {childList: true, subtree: true});
    }
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
    overlay.innerHTML = '<button class="img-close" type="button" aria-label="关闭">&times;</button>' +
                        '<img src="" alt="">';
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
  // ── #260828 Red 0.8.0 代码块复制按钮（事件委托，兼容渐进加载） ──
  if (content) {
    content.addEventListener('click', function(e) {
      var btn = e.target.closest('.code-copy');
      if (!btn) return;
      e.stopPropagation();
      var box = btn.closest('.codehilite');
      var code = box && box.querySelector('pre code');
      if (!code) return;
      var text = code.textContent;
      var done = function() {
        btn.textContent = '已复制';
        btn.classList.add('copied');
        setTimeout(function() {
          btn.textContent = '复制';
          btn.classList.remove('copied');
        }, 1600);
      };
      var fallback = function() {
        // QWebEngineView 未授予 clipboard 权限时退回 execCommand
        var ta = document.createElement('textarea');
        ta.value = text;
        ta.setAttribute('readonly', '');
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); done(); }
        catch (err) { btn.textContent = '失败'; setTimeout(function() { btn.textContent = '复制'; }, 1600); }
        document.body.removeChild(ta);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(done, fallback);
      } else {
        fallback();
      }
    });
  }

})();