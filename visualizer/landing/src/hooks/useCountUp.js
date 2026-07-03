import { useEffect, useState } from 'react';

export function useCountUp(target, duration = 2000, delay = 0) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    const end = Number(target) || 0;
    if (end <= 0) {
      setValue(0);
      return undefined;
    }

    let frameId = 0;
    let startTime = null;

    const timeoutId = setTimeout(() => {
      const animate = (timestamp) => {
        if (startTime === null) startTime = timestamp;
        const elapsed = timestamp - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - (1 - progress) ** 3;
        setValue(Math.round(end * eased));

        if (progress < 1) {
          frameId = requestAnimationFrame(animate);
        }
      };

      frameId = requestAnimationFrame(animate);
    }, delay);

    return () => {
      clearTimeout(timeoutId);
      cancelAnimationFrame(frameId);
    };
  }, [target, duration, delay]);

  return value;
}
