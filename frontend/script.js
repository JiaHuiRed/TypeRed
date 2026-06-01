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
