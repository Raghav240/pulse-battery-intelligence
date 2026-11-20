import React from 'react';
import { Sliders, ExternalLink } from 'lucide-react';

export default function GroupedSettingsCard({ onOpenSettings }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Grouped Card: Windows Power & System Settings */}
      <div className="glass-group-card">
        <div className="glass-row interactive" onClick={onOpenSettings} style={{ cursor: 'pointer' }}>
          <div className="glass-row-left">
            <div className="glass-icon-circle dark">
              <Sliders size={18} />
            </div>
            <div className="glass-row-text">
              <h4>Windows Power & Battery Settings</h4>
              <p>Configure screen timeout, sleep intervals, and brightness thresholds</p>
            </div>
          </div>
          <div className="glass-action-btn">
            <span>Configure</span>
            <ExternalLink size={12} />
          </div>
        </div>
      </div>
    </div>
  );
}
