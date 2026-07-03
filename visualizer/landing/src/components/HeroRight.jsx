import { useEffect, useState } from 'react';
import { useCountUp } from '../hooks/useCountUp';
import avatar1 from '../assets/avatars/1.png';
import avatar2 from '../assets/avatars/2.png';
import avatar3 from '../assets/avatars/3.png';
import avatar4 from '../assets/avatars/4.png';
import avatar5 from '../assets/avatars/5.png';
import avatar6 from '../assets/avatars/6.png';
import avatar7 from '../assets/avatars/7.png';
import avatar8 from '../assets/avatars/8.png';
import avatar9 from '../assets/avatars/9.png';

const DEFAULT_STATS = { nodes: 806, edges: 1121 };

const AVATARS = [
  {
    src: avatar1,
    orbit: 1,
    angle: 270,
    radius: 177,
    size: 58,
    shape: 'square',
    glow: 'purple',
    delay: 0.6,
    title: 'Experto en tratados',
  },
  {
    src: avatar2,
    orbit: 2,
    angle: 60,
    radius: 251,
    size: 58,
    shape: 'round',
    glow: 'yellow',
    delay: 0.9,
    title: 'Comité de Derechos Humanos',
  },
  {
    src: avatar3,
    orbit: 2,
    angle: 180,
    radius: 251,
    size: 78,
    shape: 'round',
    glow: 'pink',
    delay: 1.1,
    title: 'Relatoría especial',
  },
  {
    src: avatar4,
    orbit: 2,
    angle: 300,
    radius: 251,
    size: 58,
    shape: 'square',
    glow: 'blue',
    delay: 1.3,
    title: 'Organismo de la ONU',
  },
  {
    src: avatar5,
    orbit: 3,
    angle: 130,
    radius: 325,
    size: 88,
    shape: 'round',
    glow: 'pink',
    delay: 1.5,
    title: 'Población protegida',
  },
  {
    src: avatar6,
    orbit: 4,
    angle: 30,
    radius: 399,
    size: 58,
    shape: 'round',
    glow: 'purple',
    delay: 1.7,
    title: 'Mecanismo regional',
  },
  {
    src: avatar7,
    orbit: 4,
    angle: 95,
    radius: 399,
    size: 88,
    shape: 'square-lg',
    glow: 'orange',
    delay: 1.9,
    title: 'Resolución de comité',
  },
  {
    src: avatar8,
    orbit: 4,
    angle: 220,
    radius: 399,
    size: 88,
    shape: 'square-lg',
    glow: 'pink',
    delay: 2.1,
    title: 'Concepto jurídico',
  },
  {
    src: avatar9,
    orbit: 4,
    angle: 320,
    radius: 399,
    size: 58,
    shape: 'round',
    glow: 'purple',
    delay: 2.3,
    title: 'Instrumento internacional',
  },
];

const ORBITS = [
  { id: 1, size: 353, duration: 30, direction: 'ccw' },
  { id: 2, size: 501, duration: 40, direction: 'cw' },
  { id: 3, size: 649, duration: 50, direction: 'cw' },
  { id: 4, size: 797, duration: 60, direction: 'ccw' },
];

function Avatar({ avatar, direction, duration }) {
  const { src, angle, radius, size, shape, glow, delay, title } = avatar;
  const counterSpin = direction === 'cw' ? 'counter-ccw' : 'counter-cw';

  return (
    <div
      className="orbit-slot"
      style={{
        '--avatar-angle': `${angle}deg`,
        '--avatar-radius': `${radius}px`,
        '--avatar-delay': `${delay}s`,
        '--orbit-duration': `${duration}s`,
      }}
    >
      <div className={`orbit-slot-inner ${counterSpin}`}>
        <div
          className={`orbit-avatar orbit-avatar--${shape} orbit-avatar--glow-${glow} animate-avatar-in`}
          style={{ width: size, height: size, '--avatar-delay': `${delay}s` }}
          title={title}
        >
          <img src={src} alt={title} width={size} height={size} loading="lazy" />
        </div>
      </div>
    </div>
  );
}

function CenterCounter({ duration, direction }) {
  const [stats, setStats] = useState(DEFAULT_STATS);
  const count = useCountUp(stats.nodes, 2000, 1200);
  const counterSpin = direction === 'cw' ? 'counter-ccw' : 'counter-cw';

  useEffect(() => {
    fetch('/api/grafo/stats')
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => {
        if (data?.nodes) setStats(data);
      })
      .catch(() => {});
  }, []);

  return (
    <div
      className="orbit-slot orbit-slot--center"
      style={{ '--orbit-duration': `${duration}s` }}
    >
      <div className={`orbit-slot-inner ${counterSpin}`}>
        <div className="orbit-center-inner">
          <span className="orbit-count">{count.toLocaleString('es-ES')}</span>
          <span className="orbit-label">Entidades</span>
          <span className="orbit-sublabel">
            {stats.edges.toLocaleString('es-ES')} relaciones
          </span>
        </div>
      </div>
    </div>
  );
}

function OrbitRing({ orbit }) {
  return (
    <div
      className={`orbit-ring orbit-ring--${orbit.direction}`}
      style={{
        '--orbit-size': `${orbit.size}px`,
        '--orbit-duration': `${orbit.duration}s`,
      }}
    >
      {orbit.id === 1 && (
        <CenterCounter duration={orbit.duration} direction={orbit.direction} />
      )}
      {AVATARS.filter((a) => a.orbit === orbit.id).map((avatar) => (
        <Avatar
          key={`${avatar.orbit}-${avatar.angle}`}
          avatar={avatar}
          direction={orbit.direction}
          duration={orbit.duration}
        />
      ))}
    </div>
  );
}

export default function HeroRight() {
  return (
    <div className="hero-right animate-scale-in">
      <div className="orbits-container">
        {ORBITS.map((orbit) => (
          <OrbitRing key={orbit.id} orbit={orbit} />
        ))}
      </div>
    </div>
  );
}
