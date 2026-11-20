import React, { useState } from 'react';
import { Sparkles, Terminal, Globe, Music, MessageSquare, Cpu, Layers, ChevronDown } from 'lucide-react';

const APP_ICONS = {
  'ChatGPT': Sparkles,
  'Antigravity': Terminal,
  'Google': Globe,
  'Google Chrome': Globe,
  'Microsoft Edge': Globe,
  'Java': Cpu,
  'Spotify': Music,
  'Discord': MessageSquare,
  'Visual Studio Code': Terminal,
  'Windows Terminal': Terminal,
  'PowerShell': Terminal,
};

export default function AppUsageCard({ apps = [] }) {
  const [sortBy, setSortBy] = useState('percent');

  let displayApps = apps;
  if (!displayApps || displayApps.length === 0) displayApps = [];

  const sortedApps = [...displayApps].sort((a, b) => {
    if (sortBy === 'name') return a.name.localeCompare(b.name);
    return (b.percent || 0) - (a.percent || 0);
  });

  return (
    <div className="glass-group-card">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#ffffff' }}>Battery Usage Per App</h3>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>Ranked by energy consumed today</p>
        </div>

        <div
          onClick={() => setSortBy(sortBy === 'percent' ? 'name' : 'percent')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'rgba(255, 255, 255, 0.06)',
            border: '1px solid var(--border-glass)',
            borderRadius: 'var(--radius-pill)',
            padding: '4px 12px',
            fontSize: '11px',
            color: 'var(--text-secondary)',
            cursor: 'pointer'
          }}
        >
          <span>Sort: {sortBy === 'percent' ? 'Battery %' : 'Name'}</span>
          <ChevronDown size={12} />
        </div>
      </div>

      <div>
        {sortedApps.length === 0 && (
          <div className="glass-row">
            <div className="glass-row-text">
              <h4>Collecting app usage</h4>
              <p>Usage attribution will appear after the first tracking interval.</p>
            </div>
          </div>
        )}
        {sortedApps.slice(0, 5).map((app, idx) => {
          const IconComp = APP_ICONS[app.name] || Layers;
          const inUseStr = app.active_time || app.in_use || (app.active_sec ? `${Math.round(app.active_sec / 60)}m` : '0s');
          const bgStr = app.background_time || app.bg || (app.bg_sec ? `${Math.round(app.bg_sec / 60)}m` : '0s');
          const catStr = app.category || 'Application';
          const pct = typeof app.percent === 'number' ? app.percent.toFixed(1) : '10.0';

          return (
            <div key={idx} className="glass-row interactive">
              <div className="glass-row-left">
                <div className="glass-icon-circle dark">
                  <IconComp size={16} />
                </div>
                <div className="glass-row-text">
                  <h4>{app.name}</h4>
                  <p>In use: {inUseStr} • Background: {bgStr} • {catStr}</p>
                </div>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 5, width: 110 }}>
                <span style={{ fontSize: 12, fontWeight: 700, color: '#ffffff' }}>{pct}%</span>
                <div style={{ width: '100%', height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 'var(--radius-pill)', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: '100%',
                      transformOrigin: 'left center',
                      transform: `scaleX(${Math.min(1, Math.max(0.08, (app.percent || 10) / 30))})`,
                      background: 'var(--accent-blue)',
                      borderRadius: 'var(--radius-pill)',
                      boxShadow: '0 0 8px rgba(0, 122, 255, 0.6)',
                      transition: 'transform 0.4s cubic-bezier(0.16, 1, 0.3, 1)',
                      willChange: 'transform'
                    }}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
