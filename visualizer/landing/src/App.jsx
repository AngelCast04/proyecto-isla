import { useEffect } from 'react';
import Header from './components/Header';
import HeroLeft from './components/HeroLeft';
import HeroRight from './components/HeroRight';
import LogoTicker from './components/LogoTicker';
import './App.css';

const BG_URL =
  'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_111401_56af5012-2263-45d3-849a-8688084d7c2a.png&w=1280&q=85';

export default function App() {
  useEffect(() => {
    let cancelled = false;
    let tries = 0;
    if (!window.GYISCOTour) {
      const s = document.createElement('script');
      s.src = '/assets/js/product-tour.js';
      document.head.appendChild(s);
    }
    const id = setInterval(() => {
      tries += 1;
      if (cancelled) return;
      if (window.GYISCOTour) {
        clearInterval(id);
        window.GYISCOTour.initLanding();
      } else if (tries > 40) {
        clearInterval(id);
      }
    }, 50);
    return () => {
      cancelled = true;
      clearInterval(id);
    };
  }, []);

  return (
    <div className="app" style={{ backgroundImage: `url(${BG_URL})` }}>
      <Header />
      <main className="hero">
        <HeroLeft />
        <HeroRight />
      </main>
      <LogoTicker />
    </div>
  );
}
