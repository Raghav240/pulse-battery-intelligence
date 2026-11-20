import React from 'react';
import { Cpu, Zap, Wind, Flame } from 'lucide-react';

export default function HardwareThermalsFanCard({ hardware }) {
  const cpu = hardware?.cpu || {};
  const gpu = hardware?.gpu || {};
  const fans = hardware?.fans || {};
  const power = hardware?.power_flow || {};

  // Thermal Color helper
  const getTempColor = (t) => {
    if (t >= 80) return '#ef4444'; // Red
    if (t >= 65) return '#f97316'; // Orange
    if (t >= 50) return '#38bdf8'; // Cyan
    return '#34d399'; // Green
  };

  return (
    <div className="glass-group-card">
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        <div>
          <h3 style={{ fontSize: 15, fontWeight: 700, color: '#ffffff' }}>Thermals & Fan Telemetry</h3>
          <p style={{ fontSize: 11, color: 'var(--text-secondary)', marginTop: 2 }}>
            Real-time wattage push, silicon temperatures, and dual-fan speeds
          </p>
        </div>
      </div>

      {/* Row 1: Dual Silicon Sensors (CPU & GPU) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, padding: '16px 20px', borderBottom: '1px solid var(--border-subtle)' }}>
        {/* CPU Box */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="glass-icon-circle blue" style={{ width: 30, height: 30 }}>
                <Cpu size={16} />
              </div>
              <div>
                <h4 style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>CPU Package</h4>
                <p style={{ fontSize: 10, color: 'var(--text-secondary)' }}>Load: {cpu.usage_pct}% • {cpu.freq_mhz || 3200} MHz</p>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: 17, fontWeight: 800, color: getTempColor(cpu.temp_c || 0) }}>{cpu.temp_c != null ? `${cpu.temp_c}°C` : 'N/A'}</span>
              <p style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{cpu.power_watts != null ? `${cpu.power_watts} W est.` : 'Power N/A'}</p>
            </div>
          </div>
          <div style={{ width: '100%', height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, marginTop: 10, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${cpu.temp_c != null ? Math.min(100, Math.max(10, (cpu.temp_c / 100) * 100)) : 0}%`, background: getTempColor(cpu.temp_c || 0), borderRadius: 2 }} />
          </div>
        </div>

        {/* GPU Box */}
        <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid var(--border-subtle)', borderRadius: 'var(--radius-md)', padding: '14px 16px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <div className="glass-icon-circle cyan" style={{ width: 30, height: 30 }}>
                <Flame size={16} />
              </div>
              <div>
              <h4 style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>{gpu.available ? (gpu.name || 'GPU') : 'GPU not detected'}</h4>
                <p style={{ fontSize: 10, color: 'var(--text-secondary)' }}>{gpu.available ? `Load: ${gpu.usage_pct}% • VRAM: ${gpu.vram_used_mb} MB` : 'Install a supported sensor provider for GPU telemetry'}</p>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span style={{ fontSize: 17, fontWeight: 800, color: getTempColor(gpu.temp_c || 0) }}>{gpu.temp_c != null ? `${gpu.temp_c}°C` : 'N/A'}</span>
              <p style={{ fontSize: 10, color: 'var(--text-tertiary)' }}>{gpu.power_watts != null ? `${gpu.power_watts} W` : 'Power N/A'}</p>
            </div>
          </div>
          <div style={{ width: '100%', height: 4, background: 'rgba(255, 255, 255, 0.08)', borderRadius: 2, marginTop: 10, overflow: 'hidden' }}>
              <div style={{ height: '100%', width: `${gpu.temp_c != null ? Math.min(100, Math.max(10, (gpu.temp_c / 100) * 100)) : 0}%`, background: getTempColor(gpu.temp_c || 0), borderRadius: 2 }} />
          </div>
        </div>
      </div>

      {/* Row 2: Live Dual Fans Speeds (RPM) & Charger Push */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14, padding: '16px 20px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 6, background: 'rgba(56, 189, 248, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
            <Wind size={15} />
          </div>
          <div>
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>CPU Fan</span>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>{fans.available ? `${fans.cpu_fan_rpm} RPM` : 'N/A'}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 6, background: 'rgba(56, 189, 248, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#38bdf8' }}>
            <Wind size={15} />
          </div>
          <div>
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>GPU Fan</span>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>{fans.available ? `${fans.gpu_fan_rpm} RPM` : 'N/A'}</div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 28, height: 28, borderRadius: 6, background: 'rgba(0, 122, 255, 0.12)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--accent-blue)' }}>
            <Zap size={15} />
          </div>
          <div>
            <span style={{ fontSize: 10, color: 'var(--text-tertiary)', textTransform: 'uppercase' }}>Charger Push</span>
            <div style={{ fontSize: 14, fontWeight: 700, color: '#ffffff' }}>{power.charger_push_watts != null ? `${power.charger_push_watts} W (estimated)` : 'N/A'}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
