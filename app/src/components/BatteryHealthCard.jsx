import React from 'react';
import { ShieldCheck, Cpu, Zap } from 'lucide-react';

export default function BatteryHealthCard({ specs, isExpanded = false }) {
  const hasBattery = specs?.has_battery !== false;

  if (!hasBattery) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div className="glass-group-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
            <div>
              <h3 style={{ fontSize: 15, fontWeight: 700, color: '#ffffff' }}>Power System Status</h3>
              <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>Desktop Workstation AC Power Line</p>
            </div>
            <span
              style={{
                padding: '4px 12px',
                borderRadius: 'var(--radius-pill)',
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.35)',
                fontSize: 11,
                fontWeight: 600,
                letterSpacing: 0.3
              }}
            >
              ● 100% Operational
            </span>
          </div>
          <div style={{ padding: '20px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
              <div style={{ width: 44, height: 44, borderRadius: 12, background: 'rgba(56, 189, 248, 0.15)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                <Zap size={22} color="#38bdf8" />
              </div>
              <div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#ffffff' }}>Direct Continuous AC Line Power</div>
                <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 4, lineHeight: 1.5 }}>
                  This PC is a desktop workstation running on constant wall AC power. Chemical lithium-ion battery wear and cycle limits do not apply.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const full = specs?.full_charge_capacity;
  const design = specs?.design_capacity || specs?.factory_design_capacity;
  const fullWh = specs?.full_charge_wh ?? (full ? Math.round(full / 1000) : null);
  const designWh = specs?.design_wh ?? (design ? Math.round(design / 1000) : null);
  const cycles = specs?.cycle_count;
  const maxCycles = specs?.cycle_count_max || 1000;
  const healthPct = specs?.health_percent ?? (design > 0 && full > 0 ? Math.round((full / design) * 100) : null);
  const mfg = specs?.manufacturer || 'Unknown';
  const chem = specs?.chemistry || 'Unknown';
  const serialNumber = specs?.serial_number || 'Unavailable';
  const designVoltage = specs?.design_voltage_mv ? `${(specs.design_voltage_mv / 1000).toFixed(1)} V (${specs.design_voltage_mv} mV)` : 'Unavailable';
  const deviceModel = specs?.device_model || 'Windows PC';
  const deviceName = specs?.device_name || 'Unavailable';

  // Adaptive Optimizer & Charge Limiter status
  const adaptiveStatus = specs?.adaptive_battery_optimizer || 'Unknown';
  const limiterName = specs?.charge_limiter_name || 'Charge limiter status';
  const isLimiterActive = specs?.charge_limiter_active === true;

  const isOptimizerActivated = adaptiveStatus === 'Enabled/Activated' || adaptiveStatus.includes('Activated');
  const isOptimizerStandby = adaptiveStatus.includes('Not Activated');

  // Condition Badge
  const healthStatus = healthPct == null ? 'Unavailable' : healthPct >= 80 ? 'Normal' : healthPct >= 70 ? 'Fair' : 'Service Recommended';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Primary Battery Health Card */}
      <div className="glass-group-card">
        {/* Header */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
          <div>
            <h3 style={{ fontSize: 15, fontWeight: 700, color: '#ffffff' }}>Battery Health</h3>
            <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>Long-term hardware capacity & firmware care</p>
          </div>

          <span
            style={{
              padding: '4px 12px',
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(52, 211, 153, 0.15)',
              color: '#34d399',
              border: '1px solid rgba(52, 211, 153, 0.35)',
              fontSize: 11,
              fontWeight: 600,
              letterSpacing: 0.3
            }}
          >
            ● {healthStatus}
          </span>
        </div>

        {/* Big Health % & Capacity Comparison */}
        <div style={{ padding: '18px 20px 14px 20px' }}>
          <div style={{ display: 'flex', alignItems: 'baseline', gap: 12 }}>
            <div style={{ fontSize: 36, fontWeight: 800, color: '#ffffff', letterSpacing: -0.5 }}>{healthPct != null ? `${healthPct}%` : 'N/A'}</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-secondary)' }}>
              ({fullWh != null ? `${fullWh} WHr` : 'N/A'} / {designWh != null ? `${designWh} WHr` : 'N/A'})
            </div>
          </div>
          
          <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, marginTop: 4, marginBottom: 8 }}>
            {isLimiterActive
              ? `A charge limiter is active: ${limiterName}.`
              : healthPct != null && full != null && design != null
              ? `Battery health is ${healthPct}% (${full.toLocaleString()} mWh of ${design.toLocaleString()} mWh).`
              : 'Capacity information is not available from this device.'}
          </div>

          {/* Progress bar visual */}
          <div style={{ height: 6, width: '100%', background: 'rgba(255, 255, 255, 0.08)', borderRadius: 3, overflow: 'hidden', marginTop: 10 }}>
            <div
              style={{
                height: '100%',
                width: `${healthPct != null ? Math.min(100, Math.max(0, healthPct)) : 0}%`,
                background: healthPct != null && healthPct >= 80 ? 'linear-gradient(90deg, #10b981, #34d399)' : 'linear-gradient(90deg, #f59e0b, #fbbf24)',
                borderRadius: 3,
                transition: 'width 0.6s cubic-bezier(0.16, 1, 0.3, 1)'
              }}
            />
          </div>
        </div>

        {/* Adaptive Battery Optimizer Status Block */}
        <div style={{ padding: '0 20px 14px 20px' }}>
          <div
            style={{
              padding: '12px 14px',
              borderRadius: 'var(--radius-sm)',
              background: isLimiterActive ? 'rgba(16, 185, 129, 0.08)' : 'rgba(255, 255, 255, 0.03)',
              border: `1px solid ${isLimiterActive ? 'rgba(16, 185, 129, 0.25)' : 'var(--border-subtle)'}`,
              display: 'flex',
              flexDirection: 'column',
              gap: 6
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                <ShieldCheck size={16} color={isLimiterActive ? '#34d399' : 'var(--text-tertiary)'} />
                <span style={{ fontSize: 13, fontWeight: 600, color: '#ffffff' }}>{limiterName}</span>
              </div>
              <span
                style={{
                  padding: '2px 10px',
                  borderRadius: 'var(--radius-pill)',
                  background: isOptimizerActivated
                    ? 'rgba(16, 185, 129, 0.2)'
                    : isOptimizerStandby
                    ? 'rgba(56, 189, 248, 0.15)'
                    : 'rgba(255, 255, 255, 0.08)',
                  color: isOptimizerActivated ? '#34d399' : isOptimizerStandby ? '#38bdf8' : 'var(--text-tertiary)',
                  border: `1px solid ${isOptimizerActivated ? 'rgba(16, 185, 129, 0.4)' : isOptimizerStandby ? 'rgba(56, 189, 248, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
                  fontSize: 11,
                  fontWeight: 600
                }}
              >
                {adaptiveStatus === 'Enabled/Activated' ? '● Enabled / Activated' : adaptiveStatus}
              </span>
            </div>

            <p style={{ fontSize: 11, color: 'var(--text-secondary)', lineHeight: 1.4, margin: 0 }}>
              {isOptimizerActivated
                ? 'Firmware Embedded Controller (EC) is actively protecting battery cells against thermal swelling and premature wear.'
                : isLimiterActive
                ? 'Charge limiter active to maximize lifespan.'
                : 'Adaptive protection is inactive or standard unrestricted mode.'}
            </p>
          </div>
        </div>

        {/* Detailed Hardware Spec Rows */}
        <div>
          <div className="glass-row">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Full charge capacity</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{full != null ? `${full.toLocaleString()} mWh (${fullWh} WHr)` : 'Unavailable'}</span>
          </div>

          <div className="glass-row">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Factory design capacity</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{design != null ? `${design.toLocaleString()} mWh (${designWh} WHr)` : 'Unavailable'}</span>
          </div>

          <div className="glass-row">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Cycle count</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>
              {cycles != null ? <>{cycles} <span style={{ color: 'var(--text-tertiary)', fontWeight: 400 }}>/ {maxCycles} cycles ({Math.round((cycles / maxCycles) * 100)}% used)</span></> : 'Unavailable'}
            </span>
          </div>

          <div className="glass-row">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Design voltage</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{designVoltage}</span>
          </div>

          <div className="glass-row">
            <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Serial number</span>
            <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff', fontFamily: 'monospace' }}>{serialNumber}</span>
          </div>

          {isExpanded && (
            <>
              <div className="glass-row">
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Device model</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{deviceModel}</span>
              </div>

              <div className="glass-row">
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Battery hardware model</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{deviceName}</span>
              </div>

              <div className="glass-row">
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Manufacturer</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{mfg}</span>
              </div>

              <div className="glass-row">
                <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>Chemistry</span>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#ffffff' }}>{chem}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Expanded BIOS / Firmware Care Guide for All Laptops */}
      {isExpanded && (
        <div className="glass-group-card" style={{ borderLeft: '3px solid var(--accent-blue)', padding: '16px 20px' }}>
          <h4 style={{ fontSize: 14, fontWeight: 600, display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, color: '#ffffff' }}>
            <Cpu size={16} color="var(--accent-blue)" />
            OEM Firmware & BIOS Battery Care
          </h4>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
            Modern laptops regulate battery chemistry through UEFI Firmware and the Embedded Controller (EC) directly:
            <br /><br />
            • <strong style={{ color: '#fff' }}>HP (Adaptive Battery Optimizer):</strong> Monitored in BIOS Setup (press <strong>F10</strong> on boot &gt; Configuration &gt; Adaptive Battery Optimizer). When enabled, the EC cuts top-end charging voltage to maintain cell health.
            <br />• <strong style={{ color: '#fff' }}>Lenovo (Conservation Mode):</strong> Controlled via Lenovo Vantage or BIOS (F2) to stop charging at 80%.
            <br />• <strong style={{ color: '#fff' }}>ASUS / Samsung / Dell:</strong> Managed via ASUS MyASUS (80%/60%), Samsung Settings (Protect Battery 85%), or Dell Command | Power Manager.
          </p>
        </div>
      )}
    </div>
  );
}
