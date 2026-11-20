import React from 'react';
import { Zap, Heart, Clock, Settings, Battery, BatteryCharging } from 'lucide-react';

export default function FloatingDock({ activeTab, onSelectTab, live }) {
  const pct = live?.percent ?? 100;
  const isCharging = live?.is_charging ?? false;
  const acConnected = live?.ac_connected ?? true;

  const tabs = [
    { id: 'power', label: 'Battery & Performance', icon: Zap },
    { id: 'health', label: 'Battery Health', icon: Heart },
    { id: 'history', label: 'Usage History', icon: Clock },
    { id: 'settings', label: 'Settings', icon: Settings }
  ];

  return (
    <nav className="pulse-floating-dock-wrapper" aria-label="Main Navigation">
      <div className="pulse-floating-dock">
        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              type="button"
              className={`pulse-dock-item ${isActive ? 'active' : ''}`}
              onClick={() => onSelectTab(tab.id)}
            >
              <div className={`pulse-dock-icon-wrap ${isActive ? 'active' : ''}`}>
                <Icon size={15} strokeWidth={isActive ? 2.5 : 2} />
              </div>
              <span className="pulse-dock-label">{tab.label}</span>
            </button>
          );
        })}

        {/* Minimal live battery badge on right */}
        <div className="pulse-dock-divider" />
        <div
          className="pulse-dock-live-pill"
          title={
            live?.has_battery === false
              ? 'Desktop Workstation · Continuous AC Grid Power'
              : acConnected
              ? isCharging
                ? 'Charging on AC Adapter'
                : 'AC Connected · Passthrough'
              : 'Discharging on Battery'
          }
        >
          {live?.has_battery === false ? (
            <Zap size={14} color="#38bdf8" />
          ) : isCharging ? (
            <BatteryCharging size={14} color="#38bdf8" />
          ) : (
            <Battery size={14} color={pct > 20 ? '#34d399' : '#f87171'} />
          )}
          <span>{live?.has_battery === false ? 'AC Power' : `${pct}%`}</span>
          <span
            className="pulse-dock-live-dot"
            style={{
              background: acConnected ? '#38bdf8' : '#34d399',
              boxShadow: acConnected ? '0 0 8px rgba(56, 189, 248, 0.7)' : '0 0 8px rgba(52, 211, 153, 0.7)'
            }}
          />
        </div>
      </div>
    </nav>
  );
}
