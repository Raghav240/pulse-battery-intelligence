import React, { useState } from 'react';
import { Bell, Shield, Sliders, Info, Check } from 'lucide-react';

export default function SettingsView() {
  const [protectLimit, setProtectLimit] = useState(80);
  const [lowAlert, setLowAlert] = useState(20);
  const [autoRefreshSec, setAutoRefreshSec] = useState(15);
  const [savedMsg, setSavedMsg] = useState(false);
  const [apiToken, setApiToken] = useState('');

  // Fetch initial settings from backend
  React.useEffect(() => {
    fetch('http://127.0.0.1:5055/api/session')
      .then(r => r.json())
      .then(d => setApiToken(d.token || ''))
      .catch(() => {});
    fetch('http://127.0.0.1:5055/api/settings')
      .then(r => r.json())
      .then(d => {
        if (d.protect_limit) setProtectLimit(d.protect_limit);
        if (d.low_alert) setLowAlert(d.low_alert);
        if (d.refresh_sec) setAutoRefreshSec(d.refresh_sec);
      })
      .catch(() => {});
  }, []);

  const handleSave = async () => {
    try {
      await fetch('http://127.0.0.1:5055/api/settings', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Pulse-Token': apiToken },
        body: JSON.stringify({
          protect_limit: protectLimit,
          low_alert: lowAlert,
          refresh_sec: autoRefreshSec
        })
      });
      setSavedMsg(true);
      setTimeout(() => setSavedMsg(false), 2500);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="win-card">
        <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>Battery alerts & thresholds</h3>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 20 }}>
          Manage notifications for charge limits, low power warnings, and telemetry update intervals
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 18 }}>
          {/* Charge Limit Notification */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 16, borderBottom: '1px solid var(--border-subtle)' }}>
            <div>
              <h4 style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Shield size={16} color="var(--accent-blue)" />
                Charge Limit Alert
              </h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                Notify when battery reaches this level while connected to AC power
              </p>
            </div>
            <select
              value={protectLimit}
              onChange={(e) => setProtectLimit(Number(e.target.value))}
              style={{
                background: 'var(--bg-card-hover)',
                border: '1px solid var(--border-card)',
                color: 'var(--text-primary)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              <option value={80} style={{ background: '#222' }}>Limit to 80% (Maximum Longevity)</option>
              <option value={85} style={{ background: '#222' }}>Limit to 85% (Balanced)</option>
              <option value={90} style={{ background: '#222' }}>Limit to 90%</option>
              <option value={100} style={{ background: '#222' }}>Disabled (Charge to 100%)</option>
            </select>
          </div>

          {/* Low Battery Alert */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', paddingBottom: 16, borderBottom: '1px solid var(--border-subtle)' }}>
            <div>
              <h4 style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Bell size={16} color="var(--warning-amber)" />
                Low Battery Warning Threshold
              </h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                Trigger an alert to connect AC power before critical suspension
              </p>
            </div>
            <select
              value={lowAlert}
              onChange={(e) => setLowAlert(Number(e.target.value))}
              style={{
                background: 'var(--bg-card-hover)',
                border: '1px solid var(--border-card)',
                color: 'var(--text-primary)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              <option value={15} style={{ background: '#222' }}>15% Battery</option>
              <option value={20} style={{ background: '#222' }}>20% Battery (Recommended)</option>
              <option value={25} style={{ background: '#222' }}>25% Battery</option>
            </select>
          </div>

          {/* Polling Interval */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div>
              <h4 style={{ fontSize: 13, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8 }}>
                <Sliders size={16} color="var(--text-secondary)" />
                Telemetry Refresh Frequency
              </h4>
              <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>
                Polling interval for kernel power status and discharge telemetry
              </p>
            </div>
            <select
              value={autoRefreshSec}
              onChange={(e) => setAutoRefreshSec(Number(e.target.value))}
              style={{
                background: 'var(--bg-card-hover)',
                border: '1px solid var(--border-card)',
                color: 'var(--text-primary)',
                padding: '6px 12px',
                borderRadius: 'var(--radius-sm)',
                fontSize: 12,
                cursor: 'pointer'
              }}
            >
              <option value={10} style={{ background: '#222' }}>Every 10 seconds</option>
              <option value={15} style={{ background: '#222' }}>Every 15 seconds (Standard)</option>
              <option value={30} style={{ background: '#222' }}>Every 30 seconds (Ultra-low resource)</option>
            </select>
          </div>
        </div>

        <div style={{ marginTop: 24, display: 'flex', alignItems: 'center', gap: 12 }}>
          <button
            onClick={handleSave}
            style={{
              background: 'var(--accent-blue)',
              color: '#000',
              border: 'none',
              padding: '8px 20px',
              borderRadius: 'var(--radius-sm)',
              fontSize: 13,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 8
            }}
          >
            {savedMsg ? <Check size={16} /> : null}
            {savedMsg ? 'Settings Applied' : 'Save Preferences'}
          </button>
        </div>
      </div>

      {/* Hardware Charging Thresholds Guide */}
      <div className="win-card" style={{ borderLeft: '3px solid var(--accent-blue)' }}>
        <h4 style={{ fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <Shield size={16} color="var(--accent-blue)" />
          Hardware Battery Care & Firmware Limits
        </h4>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          • <strong>Software Notification:</strong> This application actively alerts you the moment your battery reaches the target charge percentage.
          <br />• <strong>Hardware Cut-Off:</strong> To physically prevent AC power from charging past 80% at the motherboard level on HP laptops, restart your computer, press <strong style={{ color: '#fff' }}>F10</strong> to enter <strong>BIOS &gt; Configuration &gt; Battery Care Function</strong> (or Adaptive Battery Optimizer), and select <strong>80%</strong>.
        </p>
      </div>

      {/* Architecture Info Card */}
      <div className="win-card" style={{ background: 'rgba(255, 255, 255, 0.02)' }}>
        <h4 style={{ fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <Info size={16} color="var(--accent-blue)" />
          System Integration Details
        </h4>
        <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          • <strong>Win32 Telemetry:</strong> Uses <code style={{ color: 'var(--accent-blue)' }}>GetSystemPowerStatus</code> for real-time AC and charge level telemetry.
          <br />• <strong>Kernel Discharge Logging:</strong> Analyzes <code style={{ color: 'var(--accent-blue)' }}>powercfg /batteryreport</code> to calculate active display duration and standby drain.
          <br />• <strong>Process Power Allocation:</strong> Tracks foreground window focus and CPU consumption to attribute energy consumption across running applications.
        </p>
      </div>
    </div>
  );
}
