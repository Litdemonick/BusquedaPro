
;(function(){
  const root = document.documentElement
  const stored = localStorage.getItem('theme')
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches
  const set = (dark) => {
    root.classList.toggle('dark', dark)
    localStorage.setItem('theme', dark ? 'dark' : 'light')
    document.getElementById('iconSun').classList.toggle('hidden', !dark)
    document.getElementById('iconMoon').classList.toggle('hidden', dark)
  }
  set(stored ? stored === 'dark' : prefersDark)
  const btn = document.getElementById('themeToggle')
  if (btn) btn.addEventListener('click', () => set(!root.classList.contains('dark')))
})();


;(function(){
  var btn = document.getElementById('menuToggle');
  var panel = document.getElementById('mobileMenu');
  if (!btn || !panel) return;
  btn.addEventListener('click', function(){
    var open = panel.classList.contains('hidden');
    panel.classList.toggle('hidden', !open);
    btn.setAttribute('aria-expanded', String(open));
  });
})();
