/* author Red */
/* TypeRed — Markdown Reader & Editor */

document.querySelectorAll('#toc a, #content a[href^="#"]').forEach(a => {
  a.addEventListener('click', e => {
    e.preventDefault();
    const id = a.getAttribute('href').replace(/.*#/, '');
    const el = document.getElementById(id);
    if (el) { el.scrollIntoView({behavior:'smooth'}); }
  });
});
(function() {
  const handle = document.getElementById('toc-resize');
  const toc = document.getElementById('toc');
  if (!handle || !toc) return;
  let dragging = false, startX = 0, startW = 0;
  handle.addEventListener('mousedown', function(e) {
    dragging = true; startX = e.clientX; startW = toc.offsetWidth;
    handle.classList.add('dragging');
    document.body.style.userSelect = 'none';
    e.preventDefault();
  });
  document.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    const w = Math.max(120, Math.min(480, startW + e.clientX - startX));
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

/* #260601 Red 0.6.5 可点击任务列表复选框 */
(function() {
  document.querySelectorAll('#content .task-list-item input[type="checkbox"]').forEach(cb => {
    cb.removeAttribute('disabled');
    cb.addEventListener('change', function(e) {
      /* 状态变化已自动反映在 checked 属性上 */
    });
  });
})();

/* #260601 Red 0.6.5 图片点击放大遮罩层 */
(function() {
  const overlay = document.createElement('div');
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

  document.querySelectorAll('#content img').forEach(img => {
    img.style.cursor = 'zoom-in';
    img.addEventListener('click', function(e) {
      e.stopPropagation();
      overlay.querySelector('img').src = this.src;
      overlay.querySelector('img').alt = this.alt;
      overlay.classList.add('active');
    });
  });
})();
