import Header from './components/Header';
import HeroLeft from './components/HeroLeft';
import HeroRight from './components/HeroRight';
import LogoTicker from './components/LogoTicker';
import './App.css';

const BG_URL =
  'https://images.higgs.ai/?default=1&output=webp&url=https%3A%2F%2Fd8j0ntlcm91z4.cloudfront.net%2Fuser_38xzZboKViGWJOttwIXH07lWA1P%2Fhf_20260624_111401_56af5012-2263-45d3-849a-8688084d7c2a.png&w=1280&q=85';

export default function App() {
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
