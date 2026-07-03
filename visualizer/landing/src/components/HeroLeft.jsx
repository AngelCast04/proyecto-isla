import { useState } from 'react';
import TypewriterHeading from './TypewriterHeading';

const HEADING_DARK =
  'Derechos Humanos a Partir de Instrumentos Internacionales y Resoluciones de Cómite de Derechos Humanos de la ONU ';

const HEADING_LIGHT = '¡Consulta la Red con IA!';

function ChevronIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none" aria-hidden="true">
      <path
        d="M6.75 4.5L11.25 9L6.75 13.5"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function CursorPointer() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" aria-hidden="true">
      <path
        d="M5 3L22 14L13 16L11 24L5 3Z"
        fill="#A068FF"
        stroke="#A068FF"
        strokeWidth="1"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function HeroLeft() {
  const [typingDone, setTypingDone] = useState(false);

  return (
    <div className="hero-left animate-fade-up">
      <TypewriterHeading
        darkText={HEADING_DARK}
        lightText={HEADING_LIGHT}
        speed={35}
        startDelay={400}
        onComplete={() => setTypingDone(true)}
      />

      <div className={`hero-cta ${typingDone ? 'hero-cta--visible' : ''}`}>
        <div className="btn-border-wrap">
          <a href="/consulta?modo=explorar" className="pill-btn pill-btn--start">
            Explorar Red Semántica
            <ChevronIcon />
          </a>
        </div>
      </div>
    </div>
  );
}
