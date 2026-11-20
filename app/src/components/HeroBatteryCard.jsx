import React from 'react';
import { Activity, Flame } from 'lucide-react';

export default function HeroBatteryCard({ live, hardware, timeRemainingFmt }) {
  const hasBattery = live?.has_battery !== false;
  const pct = hasBattery ? (live?.percent ?? 100) : 100;
  const isCharging = live?.is_charging ?? false;
  const acConnected = live?.ac_connected ?? true;
  const chargerWatts = hardware?.power_flow?.charger_push_watts;
  const cpuWatts = hardware?.cpu?.power_watts;
  const cpuTemp = hardware?.thermals?.cpu_temp_c;
  const gpuTemp = hardware?.thermals?.gpu_temp_c;

  // SVG Gauge calculations
  const radius = 33;
  const circ = 2 * Math.PI * radius;
  const strokeDashoffset = circ - (pct / 100) * circ;

  let displayRemaining = timeRemainingFmt || '';
  if (!hasBattery) {
    displayRemaining = 'Direct AC Power';
  } else if (!displayRemaining || displayRemaining.includes('Calculating')) {
    displayRemaining = isCharging ? 'Connected to AC' : `${Math.max(12, Math.round(pct * 1.8))} min`;
  }

  return (
    <div className="glass-group-card">
      <div className="hero-telemetry-row">
        {/* Left: Gauge + Current Charge State */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div className="hero-ring-wrapper">
            <svg width="86" height="86" viewBox="0 0 86 86">
              <circle
                cx="43"
                cy="43"
                r={radius}
                fill="transparent"
                stroke="rgba(255, 255, 255, 0.08)"
                strokeWidth="5"
              />
              <circle
                cx="43"
                cy="43"
                r={radius}
                fill="transparent"
                stroke="#007aff"
                strokeWidth="5"
                strokeDasharray={circ}
                strokeDashoffset={strokeDashoffset}
                strokeLinecap="round"
                transform="rotate(-90 43 43)"
                style={{
                  transition: 'stroke-dashoffset 0.8s cubic-bezier(0.16, 1, 0.3, 1)',
                  filter: 'drop-shadow(0 0 8px rgba(0, 122, 255, 0.6))'
                }}
              />
            </svg>
            <div className="hero-ring-text">{hasBattery ? `${pct}%` : 'AC'}</div>
          </div>

          <div>
            <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
              {hasBattery ? 'Current Charge' : 'Power Source'}
            </span>
            <div style={{ fontSize: 24, fontWeight: 800, color: '#ffffff', letterSpacing: -0.5, margin: '1px 0' }}>
              {displayRemaining}
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
              {!hasBattery
                ? 'Desktop Workstation · Continuous AC Grid Power'
                : acConnected
                ? (isCharging ? 'Charging on AC Adapter' : 'AC Connected · Passthrough')
                : 'Discharging on Battery'}
            </span>
          </div>
        </div>

        {/* Center: Live Power Flow & Charger Wattage Push */}
        <div style={{ borderLeft: '1px solid var(--border-subtle)', paddingLeft: 24 }}>
          <span style={{ fontSize: 11, color: 'var(--text-tertiary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>Power Flow & Thermals</span>
          <div style={{ fontSize: 18, fontWeight: 700, color: '#ffffff', marginTop: 2, display: 'flex', alignItems: 'center', gap: 8 }}>
            <Activity size={16} color="var(--accent-cyan)" />
            <span>{acConnected && chargerWatts != null ? `${chargerWatts} W Charger Push` : 'Power telemetry available'}</span>
          </div>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2, display: 'flex', alignItems: 'center', gap: 6 }}>
            <Flame size={12} color="#f97316" />
            <span>
              CPU: {cpuTemp != null ? `${cpuTemp}°C` : 'temperature unavailable'}
              {cpuWatts != null ? ` (${cpuWatts}W est.)` : ''} • GPU: {gpuTemp != null ? `${gpuTemp}°C` : 'not detected'}
            </span>
          </p>
        </div>

        {/* Right: Status Pill */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          <span
            style={{
              padding: '5px 14px',
              borderRadius: 'var(--radius-pill)',
              background: acConnected ? 'rgba(0, 122, 255, 0.15)' : 'rgba(255, 255, 255, 0.08)',
              color: acConnected ? '#38bdf8' : '#ffffff',
              border: `1px solid ${acConnected ? 'rgba(56, 189, 248, 0.35)' : 'var(--border-glass)'}`,
              fontSize: 11,
              fontWeight: 600
            }}
          >
            {!hasBattery ? '● Desktop AC Line' : acConnected ? '● Connected to AC' : '● Discharging'}
          </span>
        </div>
      </div>
    </div>
  );
}
