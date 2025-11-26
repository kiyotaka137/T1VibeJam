import { useEffect, useState } from "react";

export function useResizablePanel({ initialHeight = 250 }) {
  const [height, setHeight] = useState(initialHeight);
  const [isResizing, setIsResizing] = useState(false);

  useEffect(() => {
    const onMove = (e) => {
      if (!isResizing) return;
      const newHeight = window.innerHeight - e.clientY;
      if (newHeight > 100 && newHeight < window.innerHeight - 150) {
        setHeight(newHeight);
      }
    };
    const onUp = () => setIsResizing(false);

    if (isResizing) {
      document.addEventListener("mousemove", onMove);
      document.addEventListener("mouseup", onUp);
    }
    return () => {
      document.removeEventListener("mousemove", onMove);
      document.removeEventListener("mouseup", onUp);
    };
  }, [isResizing]);

  return { height, isResizing, startResizing: () => setIsResizing(true) };
}
