import React from 'react';
import { Laptop, Zap, Heart, Clock, Search } from 'lucide-react';

export default function Sidebar({ deviceModel, activeTab, onSelectTab, batteryPct, isCharging }) {
  let modelName = deviceModel ? deviceModel : 'Victus HP 15';
  modelName = modelName
    .replace(/by HP/gi, 'HP')
    .replace(/Gaming Laptop/gi, '')
    .replace(/Notebook/gi, '')
    .replace(/Laptop/gi, '')
    .replace(/-[a-z0-9]+$/gi, '')
    .trim();
  if (!modelName || modelName.toLowerCase() === 'windows') modelName = 'Victus HP 15';

  return (
    <aside className="pulse-sidebar">
      {/* Brand Header */}
      <div className="pulse-brand-header">
        <img src="/icon.png" alt="Pulse" className="pulse-brand-icon" />
        <div className="pulse-brand-text">
          <span className="pulse-brand-title">Pulse</span>
          <span className="pulse-brand-subtitle">Power Intelligence</span>
        </div>
      </div>

      {/* Search Bar Pill */}
      <div className="pulse-search-box">
        <Search size={14} color="var(--text-tertiary)" />
        <input type="text" placeholder="Search Settings..." readOnly />
      </div>

      {/* Device Capsule */}
      <div className="pulse-device-capsule">
        <div className="pulse-device-avatar">
          <Laptop size={17} />
        </div>
        <div className="pulse-device-meta">
          <h4 title={deviceModel || 'Windows PC'}>{modelName}</h4>
          <p>
            <span
              className="status-indicator-dot"
              style={{
                background: isCharging ? 'var(--accent-cyan)' : 'var(--accent-green)',
                boxShadow: isCharging ? '0 0 6px var(--accent-cyan)' : '0 0 6px var(--accent-green)'
              }}
            />
            {batteryPct}% • {isCharging ? 'Charging' : 'On battery'}
          </p>
        </div>
      </div>

      {/* Navigation List */}
      <nav className="pulse-nav-list">
        <div
          className={`pulse-nav-btn ${activeTab === 'power' ? 'active' : ''}`}
          onClick={() => onSelectTab('power')}
        >
          <div className="pulse-nav-icon-circle">
            <Zap size={14} />
          </div>
          <span>Battery & Performance</span>
        </div>

        <div
          className={`pulse-nav-btn ${activeTab === 'health' ? 'active' : ''}`}
          onClick={() => onSelectTab('health')}
        >
          <div className="pulse-nav-icon-circle">
            <Heart size={14} />
          </div>
          <span>Battery Health</span>
        </div>

        <div
          className={`pulse-nav-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => onSelectTab('history')}
        >
          <div className="pulse-nav-icon-circle">
            <Clock size={14} />
          </div>
          <span>Usage History</span>
        </div>
      </nav>
    </aside>
  );
}
