(() => {
  // Pequeño debounce para no spamear al servidor
  function debounce(fn, ms) {
    let t;
    return (...a) => { clearTimeout(t); t = setTimeout(() => fn(...a), ms); };
  }

  class Autocomplete {
    constructor(input, opts = {}) {
      this.ta = (typeof input === 'string') ? document.querySelector(input) : input;
      if (!this.ta) return;

      this.endpointMention = opts.endpointMention || '/autocomplete/mention/';
      this.endpointHashtag = opts.endpointHashtag || '/autocomplete/hashtag/';
      this.minChars = opts.minChars ?? 1;

      this.menu = this._buildMenu();
      this.items = [];
      this.active = -1;
      this.open = false;

      this._bind();
    }

    _buildMenu() {
      const d = document.createElement('div');
      d.className = 'ac-menu hidden absolute z-50 w-72 max-h-64 overflow-auto rounded-xl border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 shadow-soft text-sm';
      d.setAttribute('role', 'listbox');
      document.body.appendChild(d);
      return d;
    }

    _bind() {
      this.ta.addEventListener('input', debounce(this._onInput.bind(this), 120));
      this.ta.addEventListener('keydown', this._onKey.bind(this));

      document.addEventListener('click', (e) => {
        if (!this.menu.contains(e.target) && e.target !== this.ta) this._hide();
      });

      window.addEventListener('resize', () => this._pos());
      this.ta.addEventListener('blur', () => setTimeout(() => this._hide(), 100));
    }

    // Detecta el token actual (@algo o #algo) justo antes del caret
    _token() {
      const pos = this.ta.selectionStart;
      const text = this.ta.value.slice(0, pos);
      // permite letras, números, guion, punto y acentos, hasta 64 chars
      const m = /(^|\s)([@#][\wáéíóúÁÉÍÓÚñÑ.-]{0,64})$/u.exec(text);
      if (!m) return null;
      const token = m[2];
      return { prefix: token[0], term: token.slice(1), start: pos - token.length, end: pos };
    }

    async _onInput() {
      const t = this._token();
      if (!t || t.term.length < this.minChars) { this._hide(); return; }

      const url = (t.prefix === '@') ? this.endpointMention : this.endpointHashtag;

      try {
        const resp = await fetch(url + `?q=${encodeURIComponent(t.term)}`, {
          headers: { 'X-Requested-With': 'XMLHttpRequest' }
        });
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const data = await resp.json();

        // Normalizamos a objetos {value,label}
        const raw = data.results || [];
        this.items = raw.map(r =>
          typeof r === 'string'
            ? { value: (t.prefix + r), label: (t.prefix + r) }
            : { value: r.value ?? r.label ?? '', label: r.label ?? r.value ?? '' }
        );

        if (!this.items.length) {
          // Item no seleccionable “Sin resultados”
          this.items = [{ value: '__no_results__', label: 'Sin resultados' }];
          this.active = 0;
          this._render(true);
          this._show(); this._pos();
          return;
        }

        this.active = 0;
        this._render(false);
        this._show(); this._pos();
      } catch (e) {
        console.error('Autocomplete fetch error:', e);
        this._hide();
      }
    }

    _render(isEmpty) {
      this.menu.innerHTML = '';
      this.items.forEach((it, i) => {
        const isActive = i === this.active;
        const base =
          'px-3 py-2 cursor-pointer select-none text-slate-900 dark:text-slate-100';
        const hover = 'hover:bg-slate-100 dark:hover:bg-slate-700';
        const active = isActive ? 'bg-slate-100 dark:bg-slate-700' : '';
        const classes = isEmpty
          ? 'px-3 py-2 text-slate-500 dark:text-slate-400 select-none'
          : `${base} ${hover} ${active}`;

        const el = document.createElement('div');
        el.className = classes;
        el.setAttribute('role', 'option');
        el.textContent = it.label;

        if (!isEmpty && it.value !== '__no_results__') {
          el.addEventListener('mousedown', (e) => {
            e.preventDefault();
            this._apply(it.value);
          });
        }

        this.menu.appendChild(el);
      });
    }

    _pos() {
      if (!this.open) return;
      const r = this.ta.getBoundingClientRect();
      this.menu.style.left = `${r.left + window.scrollX}px`;
      this.menu.style.top  = `${r.bottom + window.scrollY + 4}px`;
      this.menu.style.width = `${r.width}px`;
    }

    _show() { this.open = true; this.menu.classList.remove('hidden'); }
    _hide() { this.open = false; this.menu.classList.add('hidden'); }

    _onKey(e) {
      if (!this.open) return;

      if (e.key === 'ArrowDown') {
        e.preventDefault();
        this.active = (this.active + 1) % this.items.length;
        this._render(this.items[0]?.value === '__no_results__');
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        this.active = (this.active - 1 + this.items.length) % this.items.length;
        this._render(this.items[0]?.value === '__no_results__');
      } else if (e.key === 'Enter') {
        const t = this._token();
        if (t) {
          e.preventDefault();
          const it = this.items[this.active];
          if (it && it.value !== '__no_results__') this._apply(it.value);
        }
      } else if (e.key === 'Escape') {
        this._hide();
      }
    }

    _apply(value) {
      const t = this._token(); if (!t) return;
      const before = this.ta.value.slice(0, t.start);
      const after  = this.ta.value.slice(t.end);
      const insert = value + ' ';
      this.ta.value = before + insert + after;
      const caret = (before + insert).length;
      this.ta.setSelectionRange(caret, caret);
      this._hide();
      this.ta.dispatchEvent(new Event('input'));
    }
  }

  // API pública
  window.setupAutocomplete = (selectorOrEl, opts) => new Autocomplete(selectorOrEl, opts);
})();
