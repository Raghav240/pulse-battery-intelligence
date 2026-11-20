import React from 'react';
import { BatteryCharging, Minus, Square, X } from 'lucide-react';

export default function TitleBar() {
  const handleMinimize = () => {
    // In Edge app mode, window.blur or window.minimize
    try { window.blur(); } catch {}
  };

  const handleMaximize = () => {
    try {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      } else {
        document.documentElement.requestFullscreen();
      }
    } catch {}
  };

  const handleClose = () => {
    try { window.close(); } catch {}
  };

  return (
    <header className="win-titlebar">
      <div className="win-titlebar-title">
        <BatteryCharging className="win-titlebar-icon" />
        <span>Power & battery</span>
      </div>

      <div className="win-titlebar-controls">
        <button className="win-titlebar-btn" title="Minimize" onClick={handleMinimize}>
          <Minus size={14} />
        </button>
        <button className="win-titlebar-btn" title="Maximize" onClick={handleMaximize}>
          <Square size={12} />
        </button>
        <button className="win-titlebar-btn close" title="Close" onClick={handleClose}>
          <X size={14} />
        </button>
      </div>
    </header>
  );
}
