import { useEffect, useRef, useState } from "react";

export function useAntiCheat({ enabled, thresholdSeconds = 4, onDisqualify }) {
  const [cheatWarning, setCheatWarning] = useState(false);
  const [timerCount, setTimerCount] = useState(thresholdSeconds);

  const intervalRef = useRef(null);
  const aliveRef = useRef(true);

  useEffect(() => {
    aliveRef.current = true;
    return () => {
      aliveRef.current = false;
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, []);

  useEffect(() => {
    if (!enabled) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        onDisqualify?.("Переключение вкладки или сворачивание окна.");
      }
    };

    const handleMouseLeave = () => {
      setCheatWarning(true);
      setTimerCount(thresholdSeconds);

      if (intervalRef.current) clearInterval(intervalRef.current);
      intervalRef.current = setInterval(() => {
        setTimerCount((prev) => {
          const next = prev - 1;
          if (next <= 0) {
            if (intervalRef.current) clearInterval(intervalRef.current);
            if (aliveRef.current) {
              onDisqualify?.(`Курсор мыши вне рабочей области более ${thresholdSeconds} секунд.`);
            }
            return 0;
          }
          return next;
        });
      }, 1000);
    };

    const handleMouseEnter = () => {
      setCheatWarning(false);
      setTimerCount(thresholdSeconds);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    document.body.addEventListener("mouseleave", handleMouseLeave);
    document.body.addEventListener("mouseenter", handleMouseEnter);

    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      document.body.removeEventListener("mouseleave", handleMouseLeave);
      document.body.removeEventListener("mouseenter", handleMouseEnter);
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [enabled, thresholdSeconds, onDisqualify]);

  return { cheatWarning, timerCount };
}
