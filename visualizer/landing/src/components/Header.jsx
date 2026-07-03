import NavInfoMenu from './NavInfoMenu';

function HomeIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path
        d="M4 10.5L12 4l8 6.5V19a1.5 1.5 0 0 1-1.5 1.5H15v-5.5H9V20.5H5.5A1.5 1.5 0 0 1 4 19v-8.5Z"
        stroke="currentColor"
        strokeWidth="1.75"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function PillButton({ href, children, variant = 'join' }) {
  return (
    <div className="btn-border-wrap">
      <a href={href} className={`pill-btn pill-btn--${variant}`}>
        {children}
      </a>
    </div>
  );
}

export default function Header() {
  return (
    <header className="header animate-fade-down">
      <div className="header-left">
        <a href="/" className="logo" title="Inicio" aria-label="Inicio">
          <span className="logo-mark">
            <HomeIcon />
          </span>
          <span className="logo-text">Bienvenido</span>
        </a>
        <nav className="nav" aria-label="Principal">
          <NavInfoMenu />
        </nav>
      </div>
      <div className="header-right">
        <PillButton href="/consulta?modo=consulta">Iniciar Consulta</PillButton>
      </div>
    </header>
  );
}

export { PillButton };
