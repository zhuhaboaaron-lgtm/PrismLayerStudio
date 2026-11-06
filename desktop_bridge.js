/* Desktop compatibility only. The original v2.6 page and calculation engine are unchanged. */
(() => {
  'use strict';
  if (window.PrismDesktopReady) return;
  const api = window.pywebview.api;
  function notify(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 4000);
  }
  const originalClick = HTMLAnchorElement.prototype.click;
  HTMLAnchorElement.prototype.click = function (...args) {
    if (this.download && this.href.startsWith('blob:')) {
      const name = this.download, href = this.href;
      fetch(href).then(response => response.blob()).then(async blob => {
        let contents = await blob.text();
        if (name.endsWith('.csv') && !contents.startsWith('\ufeff')) contents = '\ufeff' + contents;
        const result = await api.save_file(name, contents, blob.type);
        if (result.ok) notify('已保存：' + result.path);
        else if (result.cancelled) notify('已取消导出');
        else notify('导出失败：' + result.error);
      }).catch(error => notify('导出失败：' + error.message));
      return;
    }
    return originalClick.apply(this, args);
  };
  const clipboard = navigator.clipboard || {};
  Object.defineProperty(clipboard, 'writeText', { configurable: true, value: async text => {
    const result = await api.copy_text(String(text));
    if (!result.ok) throw new Error(result.error || '复制失败');
  }});
  if (!navigator.clipboard) Object.defineProperty(navigator, 'clipboard', { value: clipboard });
  // Native MathML font metrics differ slightly at fractional Windows scales.
  // Fit only expressions that exceed their existing grid cell; preserve all
  // original cards, alignment, symbols and default typography when they fit.
  function fitMath() {
    if (!document.getElementById('mathSection').open) return;
    for (const math of document.querySelectorAll('.equation .eq-rhs math')) {
      math.style.removeProperty('font-size');
      const available = math.parentElement.getBoundingClientRect().width;
      const natural = math.getBoundingClientRect().width;
      if (available > 0 && natural > available + 1) {
        const size = parseFloat(getComputedStyle(math).fontSize);
        math.style.fontSize = (size * available / natural * 0.98).toFixed(3) + 'px';
      }
    }
  }
  let fitFrame;
  function scheduleFit() {
    cancelAnimationFrame(fitFrame);
    fitFrame = requestAnimationFrame(fitMath);
  }
  document.getElementById('mathSection').addEventListener('toggle', scheduleFit);
  window.addEventListener('resize', scheduleFit);
  new ResizeObserver(scheduleFit).observe(document.documentElement);
  document.fonts.ready.then(scheduleFit);
  window.PrismDesktopReady = true;
})();
