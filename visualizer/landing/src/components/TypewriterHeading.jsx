import { useEffect, useRef, useState } from 'react';

export default function TypewriterHeading({
  darkText,
  lightText,
  speed = 35,
  startDelay = 400,
  onComplete,
}) {
  const fullText = darkText + lightText;
  const [displayed, setDisplayed] = useState('');
  const [showCursor, setShowCursor] = useState(false);
  const [done, setDone] = useState(false);
  const onCompleteRef = useRef(onComplete);

  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  useEffect(() => {
    let index = 0;
    let intervalId;

    const startTimeout = setTimeout(() => {
      setShowCursor(true);

      intervalId = setInterval(() => {
        index += 1;
        setDisplayed(fullText.slice(0, index));

        if (index >= fullText.length) {
          clearInterval(intervalId);
          setDone(true);
          setShowCursor(false);
          onCompleteRef.current?.();
        }
      }, speed);
    }, startDelay);

    return () => {
      clearTimeout(startTimeout);
      clearInterval(intervalId);
    };
  }, [fullText, speed, startDelay]);

  const darkPart = displayed.slice(0, darkText.length);
  const lightPart = displayed.slice(darkText.length);

  return (
    <h1 className="hero-heading">
      <span className="hero-heading-dark">{darkPart}</span>
      {lightPart ? <span className="hero-heading-light">{lightPart}</span> : null}
      {!done && showCursor && <span className="typewriter-cursor">|</span>}
    </h1>
  );
}
