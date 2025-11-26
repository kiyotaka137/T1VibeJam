import { useEffect, useState } from "react";

export function useMainTimer({ initialSeconds, paused }) {
  const [timeLeft, setTimeLeft] = useState(initialSeconds);
  const [timedOut, setTimedOut] = useState(false);

  useEffect(() => {
    if (paused) return;
    if (timeLeft <= 0) {
      setTimedOut(true);
      return;
    }
    const t = setInterval(() => setTimeLeft((p) => p - 1), 1000);
    return () => clearInterval(t);
  }, [paused, timeLeft]);

  return { timeLeft, setTimeLeft, timedOut };
}
