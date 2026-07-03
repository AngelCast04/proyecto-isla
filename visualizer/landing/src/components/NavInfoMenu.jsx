import { useEffect, useRef, useState } from 'react';

const NAV_ITEMS = [
  {
    id: 'tratados',
    label: 'Tratados',
    group: 'Tratado',
    color: '#8b5cf6',
    description:
      'Convenios y pactos internacionales vinculantes que reconocen, garantizan o limitan derechos humanos.',
    detail:
      'En la red aparecen vinculados a poblaciones protegidas, derechos reconocidos y organismos supervisores.',
    examples: ['Pacto de Derechos Civiles y Políticos', 'Convención sobre los Derechos del Niño'],
    href: '/consulta?modo=explorar',
  },
  {
    id: 'resoluciones',
    label: 'Resoluciones',
    group: 'Resolución',
    color: '#ec4899',
    description:
      'Decisiones, observaciones y pronunciamientos de comités, consejos y órganos internacionales.',
    detail:
      'Conectan casos concretos, interpretaciones normativas y recomendaciones a Estados y actores.',
    examples: ['Observaciones generales', 'Vistas de comités sobre casos'],
    href: '/consulta?modo=explorar',
  },
  {
    id: 'organismos',
    label: 'Organismos',
    group: 'Organismo',
    color: '#f59e0b',
    description:
      'Instituciones de la ONU, sistemas regionales y entidades que monitorean el cumplimiento de derechos.',
    detail:
      'Articulan mecanismos de protección, relatorías especiales y procedimientos de denuncia.',
    examples: ['Comité de Derechos Humanos', 'Corte Interamericana de Derechos Humanos'],
    href: '/consulta?modo=explorar',
  },
  {
    id: 'consulta-ia',
    label: 'Consulta IA',
    color: '#a068ff',
    description:
      'Formula preguntas en lenguaje natural sobre el corpus; el sistema recupera contexto del grafo y genera una respuesta.',
    detail:
      'Combina búsqueda semántica, PageRank y relaciones del grafo para explicar, argumentar y visualizar el subconjunto impactado.',
    examples: [
      '¿Qué instrumentos protegen a personas indígenas?',
      '¿Cuáles son los mecanismos de la ONU para migrantes?',
    ],
    href: '/consulta?modo=consulta',
  },
];

const METODOLOGIA = {
  id: 'metodologia',
  label: 'Metodología',
  color: '#ffffff',
  description:
    'Pipeline GraphRAG: ingesta de PDFs, extracción tipada de entidades y relaciones, índices vectoriales y grafo persistente.',
  detail:
    'Las consultas activan recuperación híbrida (embeddings + grafo) y una interfaz de visualización interactiva.',
  steps: [
    'Extracción desde documentos en libros/',
    'Grafo igraph con tipos de entidad',
    'Consulta con contexto explicable',
  ],
  href: '/consulta?modo=consulta',
};

function formatCount(n) {
  if (typeof n !== 'number') return null;
  return n.toLocaleString('es-ES');
}

function NavInfoItem({ item, stats, variant = 'default' }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);
  const count = item.group ? stats?.groups?.[item.group] : null;

  useEffect(() => {
    function onDocClick(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onDocClick);
    return () => document.removeEventListener('mousedown', onDocClick);
  }, []);

  const panelId = `nav-panel-${item.id}`;

  return (
    <div
      ref={rootRef}
      className={`nav-info-item nav-info-item--${variant}${open ? ' nav-info-item--open' : ''}`}
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className={`nav-link nav-info-trigger${variant === 'light' ? ' nav-link--light' : ''}`}
        aria-expanded={open}
        aria-controls={panelId}
        onClick={() => setOpen((v) => !v)}
      >
        {item.label}
        <span className="nav-info-chevron" aria-hidden="true">
          ▾
        </span>
      </button>

      <div id={panelId} className="nav-info-panel" role="region" aria-label={item.label}>
        <div className="nav-info-panel-inner">
          <div className="nav-info-head">
            <span className="nav-info-dot" style={{ background: item.color }} />
            <div>
              <strong>{item.label}</strong>
              {count != null && (
                <span className="nav-info-stat">
                  {formatCount(count)} en la red
                </span>
              )}
            </div>
          </div>

          <p className="nav-info-text">{item.description}</p>
          <p className="nav-info-detail">{item.detail}</p>

          {item.examples && (
            <ul className="nav-info-list">
              {item.examples.map((ex) => (
                <li key={ex}>{ex}</li>
              ))}
            </ul>
          )}

          {item.steps && (
            <ol className="nav-info-steps">
              {item.steps.map((step) => (
                <li key={step}>{step}</li>
              ))}
            </ol>
          )}

          <a href={item.href} className="nav-info-cta">
            {item.id === 'consulta-ia' ? 'Abrir consulta' : 'Explorar en el grafo'} →
          </a>
        </div>
      </div>
    </div>
  );
}

export default function NavInfoMenu({ variant = 'default', item = null }) {
  const [stats, setStats] = useState(null);

  useEffect(() => {
    fetch('/api/grafo/stats')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data) setStats(data);
      })
      .catch(() => {});
  }, []);

  if (item) {
    return <NavInfoItem item={item} stats={stats} variant={variant} />;
  }

  return (
    <>
      {NAV_ITEMS.map((navItem) => (
        <NavInfoItem key={navItem.id} item={navItem} stats={stats} variant={variant} />
      ))}
    </>
  );
}

export { METODOLOGIA, NAV_ITEMS };
