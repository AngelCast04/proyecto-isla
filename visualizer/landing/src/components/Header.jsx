import NavInfoMenu from './NavInfoMenu';

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
        <a href="/" className="header-logos" title="Inicio" aria-label="Inicio">
          <img
            src="/logos/UJAT_logo.png"
            alt="Universidad Juárez Autónoma de Tabasco"
            className="header-logo header-logo--ujat"
          />
          <span className="header-logos-rule" aria-hidden="true" />
          <img
            src="/logos/DACSyH_logo.png"
            alt="DACSyH — División Académica de Ciencias Sociales y Humanidades"
            className="header-logo header-logo--dacsyh"
          />
          <img
            src="/logos/DACyTI_logo.png"
            alt="DACyTI — División Académica de Ciencias y Tecnologías de la Información"
            className="header-logo header-logo--dacyti"
          />
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
