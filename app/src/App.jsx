import React, { useState, useEffect } from 'react';
import FloatingDock from './components/FloatingDock';
import HeroBatteryCard from './components/HeroBatteryCard';
import GroupedSettingsCard from './components/GroupedSettingsCard';
import HardwareThermalsFanCard from './components/HardwareThermalsFanCard';
import UsageGraphCard from './components/UsageGraphCard';
import AppUsageCard from './components/AppUsageCard';
import BatteryHealthCard from './components/BatteryHealthCard';
import SettingsView from './components/SettingsView';

const API_BASE = 'http://127.0.0.1:5055';

export default function App() {
  const [activeTab, setActiveTab] = useState(() => {
    try {
      const urlTab = new URLSearchParams(window.location.search).get('tab');
      if (urlTab && ['power', 'health', 'history', 'settings'].includes(urlTab)) {
        return urlTab;
      }
    } catch {}
    return 'power';
  }); // 'power', 'health', 'history'

  const [activeMode, setActiveMode] = useState('since_charge'); // 'since_charge', 'today', 'week'

  const [live, setLive] = useState(null);
  const [specs, setSpecs] = useState(null);
  const [stats, setStats] = useState(null);
  const [apps, setApps] = useState([]);
  const [hardware, setHardware] = useState(null);
  const [timeRemainingFmt, setTimeRemainingFmt] = useState('');
  const [apiToken, setApiToken] = useState('');
  const [refreshSec, setRefreshSec] = useState(15);

  // Fetch live battery and hardware status
  const fetchLiveStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/battery/status`);
      if (res.ok) {
        const data = await res.json();
        setLive(data.live);
        setTimeRemainingFmt(data.time_remaining_formatted);
        if (data.settings?.refresh_sec) setRefreshSec(data.settings.refresh_sec);
        if (data.specs && Object.keys(data.specs).length > 0) {
          setSpecs(data.specs);
        }
        if (data.hardware) {
          setHardware(data.hardware);
        }
      }
    } catch {
      console.warn('Backend live status query failed:', e);
    }
  };

  // Dedicated hardware telemetry polling (for thermals & fan speeds)
  const fetchTelemetry = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/hardware/telemetry`);
      if (res.ok) {
        const tel = await res.json();
        setHardware(tel);
      }
    } catch {
      // Background retry
    }
  };

  // Fetch detailed stats and app usage
  const fetchDetailedStats = async (mode = activeMode) => {
    try {
      const [statsRes, appsRes] = await Promise.all([
        fetch(`${API_BASE}/api/battery/stats?mode=${mode}`),
        fetch(`${API_BASE}/api/apps/usage?mode=${mode}`)
      ]);

      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
        if (statsData.battery_specs) {
          setSpecs(statsData.battery_specs);
        }
      }

      if (appsRes.ok) {
        const appsData = await appsRes.json();
        setApps(appsData.apps || []);
      }
    } catch (e) {
      console.warn('Backend detailed stats query failed:', e);
    }
  };

  useEffect(() => {
    fetch(`${API_BASE}/api/session`)
      .then(r => r.json())
      .then(d => setApiToken(d.token || ''))
      .catch(() => {});
    const initialLoad = window.setTimeout(() => {
      fetchLiveStatus();
      fetchDetailedStats(activeMode);
      fetchTelemetry();
    }, 0);

    // Polling intervals
    const interval = setInterval(fetchLiveStatus, Math.max(5000, refreshSec * 1000));
    const telInterval = setInterval(fetchTelemetry, 2500);

    // Heartbeat to keep backend alive
    const hbInterval = setInterval(() => {
      fetch(`${API_BASE}/api/heartbeat`).catch(() => {});
    }, 2500);

    return () => {
      clearTimeout(initialLoad);
      clearInterval(interval);
      clearInterval(telInterval);
      clearInterval(hbInterval);
    };
  }, [activeMode, refreshSec]);

  const handleModeChange = (newMode) => {
    setActiveMode(newMode);
    fetchDetailedStats(newMode);
  };

  const handleOpenSettings = async () => {
    try {
      await fetch(`${API_BASE}/api/action/open_windows_settings`, {
        method: 'POST', headers: { 'X-Pulse-Token': apiToken }
      });
    } catch {
      try {
        window.location.href = 'ms-settings:batterysaver';
      } catch {}
    }
  };

  return (
    <div className="pulse-app">
      {/* Main Full-Width Fluid Scrollable Content */}
      <main className="pulse-main-content">
        <div className="pulse-content-container">
          {/* Top Header */}
          <div className="pulse-main-heading">
            <h1>
              {activeTab === 'health' && 'Battery Health'}
              {activeTab === 'history' && 'Usage History'}
              {activeTab === 'settings' && 'Settings'}
              {activeTab === 'power' && 'Battery & Performance'}
            </h1>
            <p>
              {activeTab === 'health' && 'Review hardware degradation, cycle count, and factory capacities.'}
              {activeTab === 'history' && 'Review your discharge timeline and screen-on intervals.'}
              {activeTab === 'settings' && 'Configure alerts, sampling frequency, and Windows power integration.'}
              {activeTab === 'power' && 'Manage power profiles, monitor health, and customize battery longevity.'}
            </p>
          </div>

          {/* TAB: BATTERY & PERFORMANCE (Main Fluid View) */}
          {activeTab === 'power' && (
            <div className="pulse-tab-view" key="tab-power">
              {/* Hero Live Battery Gauge with real-time wattage push and thermals */}
              <HeroBatteryCard
                live={live}
                hardware={hardware}
                specs={specs}
                timeRemainingFmt={timeRemainingFmt}
                onOpenSettings={handleOpenSettings}
              />

              {/* Grouped Settings Cards */}
              <GroupedSettingsCard
                onOpenSettings={handleOpenSettings}
              />

              {/* Hardware Thermals & Fan Speed Monitoring Card */}
              <HardwareThermalsFanCard
                hardware={hardware}
              />

              {/* Interactive Timeline Graph Card */}
              <UsageGraphCard
                stats={stats}
                activeMode={activeMode}
                onModeChange={handleModeChange}
              />

              {/* 2-Column Split: App Usage & Health */}
              <div className="pulse-bottom-split">
                <AppUsageCard apps={apps} />
                <BatteryHealthCard specs={specs} isExpanded={false} />
              </div>
            </div>
          )}

          {/* TAB: BATTERY HEALTH */}
          {activeTab === 'health' && (
            <div className="pulse-tab-view" key="tab-health">
              <BatteryHealthCard specs={specs} isExpanded={true} />
            </div>
          )}

          {/* TAB: USAGE HISTORY */}
          {activeTab === 'history' && (
            <div className="pulse-tab-view" key="tab-history">
              <UsageGraphCard
                stats={stats}
                activeMode={activeMode}
                onModeChange={handleModeChange}
              />
              <AppUsageCard apps={apps} />
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="pulse-tab-view" key="tab-settings">
              <SettingsView />
            </div>
          )}

          {/* Bottom clearance spacer for floating dock */}
          <div style={{ height: 50, flexShrink: 0 }} />
        </div>
      </main>

      {/* Floating Bottom Center Glassmorphic Navigation Dock */}
      <FloatingDock
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        live={live}
      />
    </div>
  );
}
