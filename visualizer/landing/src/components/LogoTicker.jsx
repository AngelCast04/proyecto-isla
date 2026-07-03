const DERECHOS = [
  'Derecho de los Indígenas',
  'Derecho de Migrantes',
  'Derecho a la Vivienda',
  'Derecho a la Educación',
  'Derecho a la Privacidad',
  'Derecho a la Familia',
  'Derecho a la Dignidad',
  'Derechos Lingüísticos',
  'Derecho de los Adultos mayores',
  'Derecho al Medio Ambiente',
  'Derecho a la Libertad de Expresión',
  'Derecho a la Salud',
  'Derechos de los Refugiados',
  'Derecho humano al Agua',
  'Prohibición a la Trata de Personas',
  'Derecho a la Igualdad',
  'Derecho a la No Discriminación',
  'Derechos de las Personas con Discapacitadas',
  'Derecho al Descanso',
  'Derechos de los Niños',
  'Derecho de las Mujeres',
  'Derechos de los Reclusos',
  'Derechos de la Libertad',
  'Libertad de Cultos',
  'Libertad de Movilidad',
  'Libertad Personal',
  'Derecho de Propiedad y Pensiones',
  'Derecho de Petición',
  'Derecho a ser Diferente',
  'Derecho al debido Proceso',
  'Derecho al Acceso a la Justicia',
  'Derecho a la Vida',
  'Prohibición de Ejecución Sumaria',
  'Protección contra la Tortura',
  'Derecho a la Legalidad',
  'Derecho al Trabajo',
  'Derecho a la Alimentación',
  'Derecho a la Paz',
  'Derecho al Desarrollo',
  'Derecho de Asociación',
  'Prohibición a la Desaparición Forzada',
];

const REPEAT_COUNT = 2;

export default function LogoTicker() {
  const items = Array.from({ length: REPEAT_COUNT }, () => DERECHOS).flat();

  return (
    <section
      className="logo-ticker animate-fade-up-delayed"
      aria-label="Derechos humanos cubiertos en la red semántica"
    >
      <div className="logo-ticker-mask">
        <div className="logo-ticker-track">
          {items.map((derecho, i) => (
            <a
              key={`${derecho}-${i}`}
              className="logo-ticker-item"
              href={`/consulta?derecho=${encodeURIComponent(derecho)}`}
              title={`Ver grafo de «${derecho}»`}
            >
              {derecho}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}
