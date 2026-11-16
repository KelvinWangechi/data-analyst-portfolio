(() => {
  'use strict';
  const el = id => document.getElementById(id);
  const theme = el('theme-toggle');
  function setTheme(dark) {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light';
    theme.textContent = dark ? 'Light view' : 'Dark view';
    theme.setAttribute('aria-label',dark ? 'Switch to light appearance' : 'Switch to dark appearance');
  }
  theme.addEventListener('click',() => setTheme(document.documentElement.dataset.theme !== 'dark'));
  setTheme(window.matchMedia('(prefers-color-scheme: dark)').matches);
  theme.hidden=false;
  const links=[...document.querySelectorAll('.contents a')];
  const observer=new IntersectionObserver(entries => {
    const visible=entries.filter(e => e.isIntersecting).sort((a,b) => a.boundingClientRect.top-b.boundingClientRect.top);
    if (!visible.length) return;
    for (const link of links) {
      if (link.hash === `#${visible[0].target.id}`) link.setAttribute('aria-current','location');
      else link.removeAttribute('aria-current');
    }
  },{rootMargin:'-100px 0px -50% 0px',threshold:0});
  document.querySelectorAll('.chapter').forEach(chapter => observer.observe(chapter));
})();
