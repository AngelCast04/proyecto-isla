/* Recorrido guiado GYISCO (landing, consulta y grafo). */
(function (w) {
  var STORAGE = {
    landing: 'gyisco.tour.landing.v1',
    consulta: 'gyisco.tour.consulta.v1'
  };
  var PAD = 8;
  var GAP = 12;
  var VIEW_PAD = 12;
  var state = {
    steps: [],
    index: 0,
    root: null,
    storageKey: '',
    onFinish: null
  };

  function $(sel) {
    return document.querySelector(sel);
  }

  function wait(ms) {
    return new Promise(function (resolve) { setTimeout(resolve, ms); });
  }

  function seen(key) {
    try { return w.localStorage.getItem(key) === '1'; } catch (e) { return false; }
  }

  function markSeen(key) {
    try { w.localStorage.setItem(key, '1'); } catch (e) {}
  }

  function resolveEl(step) {
    if (!step) return null;
    if (typeof step.el === 'function') return step.el();
    if (typeof step.el === 'string') return $(step.el);
    return step.el || null;
  }

  function destroy() {
    if (state.root && state.root.parentNode) state.root.parentNode.removeChild(state.root);
    state.root = null;
    state.steps = [];
    state.index = 0;
    state.onFinish = null;
    w.removeEventListener('resize', onReflow);
    w.removeEventListener('keydown', onKey);
  }

  function finish() {
    var key = state.storageKey;
    if (key) markSeen(key);
    destroy();
  }

  function onKey(ev) {
    if (!state.root) return;
    if (ev.key === 'Escape') {
      ev.preventDefault();
      finish();
    } else if (ev.key === 'ArrowRight') {
      ev.preventDefault();
      next();
    } else if (ev.key === 'ArrowLeft') {
      ev.preventDefault();
      prev();
    }
  }

  function onReflow() {
    layout();
  }

  function layout() {
    if (!state.root) return;
    var step = state.steps[state.index];
    var el = resolveEl(step);
    var hole = state.root.querySelector('.gy-tour-hole');
    var pop = state.root.querySelector('.gy-tour-pop');
    if (!el || !hole || !pop) return;

    el.scrollIntoView({ block: 'nearest', inline: 'nearest', behavior: 'smooth' });
    var r = el.getBoundingClientRect();
    if (r.width < 2 && r.height < 2) {
      hole.style.display = 'none';
    } else {
      hole.style.display = 'block';
      hole.style.top = Math.max(0, r.top - PAD) + 'px';
      hole.style.left = Math.max(0, r.left - PAD) + 'px';
      hole.style.width = Math.max(24, r.width + PAD * 2) + 'px';
      hole.style.height = Math.max(24, r.height + PAD * 2) + 'px';
    }

    var hr = hole.style.display === 'none'
      ? { top: 80, left: 24, width: 0, height: 0, bottom: 80, right: 24 }
      : {
          top: Math.max(0, r.top - PAD),
          left: Math.max(0, r.left - PAD),
          width: Math.max(24, r.width + PAD * 2),
          height: Math.max(24, r.height + PAD * 2),
          bottom: Math.max(0, r.top - PAD) + Math.max(24, r.height + PAD * 2),
          right: Math.max(0, r.left - PAD) + Math.max(24, r.width + PAD * 2)
        };

    var pw = pop.offsetWidth;
    var ph = pop.offsetHeight;
    var vw = w.innerWidth;
    var vh = w.innerHeight;
    var place = step.place || 'auto';
    var top;
    var left;

    if (place === 'left' || place === 'right') {
      top = hr.top + hr.height / 2 - ph / 2;
      left = place === 'left' ? hr.left - GAP - pw : hr.right + GAP;
      if (left < VIEW_PAD) left = hr.right + GAP;
      if (left + pw > vw - VIEW_PAD) left = hr.left - GAP - pw;
    } else {
      left = hr.left + hr.width / 2 - pw / 2;
      var below = hr.bottom + GAP;
      var above = hr.top - GAP - ph;
      var useTop = place === 'top' || (place === 'auto' && below + ph > vh - VIEW_PAD && above >= VIEW_PAD);
      if (place === 'bottom') useTop = false;
      top = useTop ? above : below;
    }
    if (top < VIEW_PAD) top = VIEW_PAD;
    if (top + ph > vh - VIEW_PAD) top = Math.max(VIEW_PAD, vh - VIEW_PAD - ph);
    left = Math.min(Math.max(VIEW_PAD, left), vw - VIEW_PAD - pw);

    pop.style.top = top + 'px';
    pop.style.left = left + 'px';
  }

  function render() {
    if (!state.root) return;
    var step = state.steps[state.index];
    if (!step) {
      finish();
      return;
    }
    var total = state.steps.length;
    var n = state.index + 1;
    var last = n === total;
    state.root.querySelector('#gy-tour-title').textContent = step.title;
    state.root.querySelector('.gy-tour-body').textContent = step.body;
    state.root.querySelector('.gy-tour-kicker span').textContent = n + ' / ' + total;
    var back = state.root.querySelector('.gy-tour-back');
    var nextBtn = state.root.querySelector('.gy-tour-next');
    back.disabled = state.index === 0;
    nextBtn.textContent = last ? (step.nextLabel || 'Listo') : 'Siguiente';
    var dots = state.root.querySelector('.gy-tour-dots');
    dots.innerHTML = '';
    for (var i = 0; i < total; i += 1) {
      var d = document.createElement('span');
      if (i === state.index) d.className = 'on';
      dots.appendChild(d);
    }
    layout();
  }

  async function go(i) {
    if (i < 0 || i >= state.steps.length) return;
    state.index = i;
    var step = state.steps[i];
    if (typeof step.before === 'function') {
      await step.before();
      await wait(140);
    }
    render();
  }

  function next() {
    var step = state.steps[state.index];
    if (state.index >= state.steps.length - 1) {
      var href = step && step.finishHref;
      finish();
      if (href) w.location.href = href;
      return;
    }
    go(state.index + 1);
  }

  function prev() {
    if (state.index <= 0) return;
    go(state.index - 1);
  }

  function mount() {
    destroy();
    var root = document.createElement('div');
    root.className = 'gy-tour-root';
    root.innerHTML =
      '<div class="gy-tour-overlay"></div>' +
      '<div class="gy-tour-hole"></div>' +
      '<div class="gy-tour-pop" role="dialog" aria-modal="true" aria-labelledby="gy-tour-title">' +
        '<p class="gy-tour-kicker">Tour <span></span></p>' +
        '<div class="gy-tour-dots"></div>' +
        '<h2 id="gy-tour-title"></h2>' +
        '<p class="gy-tour-body"></p>' +
        '<div class="gy-tour-actions">' +
          '<button type="button" class="gy-tour-skip">Saltar</button>' +
          '<div class="gy-tour-nav">' +
            '<button type="button" class="gy-tour-back">Atrás</button>' +
            '<button type="button" class="gy-tour-next">Siguiente</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(root);
    state.root = root;
    root.querySelector('.gy-tour-skip').addEventListener('click', finish);
    root.querySelector('.gy-tour-back').addEventListener('click', prev);
    root.querySelector('.gy-tour-next').addEventListener('click', next);
    w.addEventListener('resize', onReflow);
    w.addEventListener('keydown', onKey);
  }

  function start(steps, storageKey, opts) {
    var list = (steps || []).filter(function (s) { return resolveEl(s) || s.before; });
    if (!list.length) return;
    mount();
    state.steps = list;
    state.storageKey = storageKey || '';
    state.onFinish = null;
    go(0);
  }

  function landingSteps() {
    return [
      { el: '#tour-logos', title: 'Instituciones', body: 'Logos de las instituciones que respaldan GYISCO.', place: 'bottom' },
      { el: '#tour-nav', title: 'Menú', body: 'Son definiciones de derechos humanos que hay en la red, las tres primeras te llevan a explorar la red de conocimiento y Consulta IA define cómo formular las preguntas y abre el modo de consulta.', place: 'bottom' },
      { el: '#tour-iniciar', title: 'Iniciar consulta', body: 'Abre el chat para preguntar a la IA.', place: 'bottom' },
      { el: '#tour-heading', title: 'El proyecto', body: 'Derechos humanos a partir de instrumentos y resoluciones de la ONU.', place: 'bottom' },
      {
        el: '#tour-explorar',
        title: 'Explorar la red',
        body: 'Entra directo al grafo completo.',
        place: 'top',
        before: function () {
          var cta = document.querySelector('.hero-cta');
          if (cta) cta.classList.add('hero-cta--visible');
        }
      },
      { el: '#tour-orbitas .orbit-center-inner', title: 'La red hoy', body: 'Cuántas entidades y relaciones hay indexadas.', place: 'left' },
      {
        el: '#tour-ticker',
        title: 'Derechos del corpus',
        body: 'Un clic abre ese derecho en el grafo.',
        place: 'top',
        nextLabel: 'Ver la app',
        finishHref: '/consulta?tour=1'
      }
    ];
  }

  function showVista(nombre) {
    if (typeof w.mostrarVista === 'function') w.mostrarVista(nombre);
  }

  function consultaSteps() {
    var chat = function () { showVista('chat'); };
    var grafo = function () { showVista('grafo'); };
    return [
      { el: '.home-link', title: 'Inicio', body: 'Vuelve al landing.', place: 'bottom', before: chat },
      { el: '#tour-tabs', title: 'Pantallas', body: 'Consulta es el chat. Grafo es la red visual.', place: 'bottom', before: chat },
      { el: '#tour-acciones', title: 'Acciones', body: 'Exporta un PDF o empieza una consulta nueva.', place: 'bottom', before: chat },
      {
        el: function () {
          var empty = document.getElementById('chatEmpty');
          if (empty && empty.style.display === 'none') return document.getElementById('chatScroll');
          return document.getElementById('tour-sugerencias') || empty;
        },
        title: 'Ejemplos',
        body: 'Preguntas listas para empezar. Si ya consultaste, aquí ves el hilo.',
        place: 'bottom',
        before: chat
      },
      { el: '#chatComposer', title: 'Escribe aquí', body: 'Envía la pregunta. La respuesta sale en pestañas: explicación, marco, relaciones…', place: 'top', before: chat },
      { el: '#btnToggleListado', title: 'Listado de derechos', body: 'Elige un derecho y ves su subgrafo.', place: 'bottom', before: grafo },
      { el: '#btnToggleGuia', title: 'Categorías', body: 'Qué significa cada color o tipo de nodo.', place: 'bottom', before: grafo },
      { el: '#leyenda', title: 'Filtros', body: 'Muestra solo un tipo: derecho, tratado, población…', place: 'bottom', before: grafo },
      { el: '#tour-lienzo', title: 'El grafo', body: 'Red impactada por la consulta. Clic en un nodo para ver su ficha.', place: 'top', before: grafo },
      { el: '#tour-grafo-meta', title: 'Vista', body: 'Centra el dibujo o carga la red completa.', place: 'top', before: grafo }
    ];
  }

  var landingReady = false;
  var consultaReady = false;

  function bindLauncher(id, fn) {
    var btn = document.getElementById(id);
    if (!btn || btn.getAttribute('data-tour-bound') === '1') return;
    btn.setAttribute('data-tour-bound', '1');
    btn.addEventListener('click', function (ev) {
      ev.preventDefault();
      fn();
    });
  }

  function consumeTourParam() {
    var params = new URLSearchParams(w.location.search);
    if (params.get('tour') !== '1') return false;
    params.delete('tour');
    var q = params.toString();
    w.history.replaceState({}, '', w.location.pathname + (q ? '?' + q : ''));
    return true;
  }

  function initLanding() {
    if (landingReady) return;
    landingReady = true;
    bindLauncher('tour-launcher', startLanding);
    var force = consumeTourParam();
    if (force || !seen(STORAGE.landing)) {
      setTimeout(startLanding, force ? 400 : 1100);
    }
  }

  function startLanding() {
    start(landingSteps(), STORAGE.landing);
  }

  function initConsulta() {
    if (consultaReady) return;
    consultaReady = true;
    bindLauncher('btnTour', startConsulta);
    var params = new URLSearchParams(w.location.search);
    var force = consumeTourParam();
    var busy = params.get('modo') || params.get('derecho');
    if (force || (!busy && !seen(STORAGE.consulta))) {
      setTimeout(startConsulta, force ? 450 : 900);
    }
  }

  function startConsulta() {
    start(consultaSteps(), STORAGE.consulta);
  }

  w.GYISCOTour = {
    initLanding: initLanding,
    initConsulta: initConsulta,
    startLanding: startLanding,
    startConsulta: startConsulta,
    destroy: destroy
  };
})(window);
