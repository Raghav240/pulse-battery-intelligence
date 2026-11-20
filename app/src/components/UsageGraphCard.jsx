import React, { useState, useRef, useMemo } from 'react';
import { Smartphone, Moon, TrendingDown } from 'lucide-react';

export default function UsageGraphCard({ stats, activeMode, onModeChange }) {
  const [hoveredPoint, setHoveredPoint] = useState(null);
  const svgRef = useRef(null);

  const rawGraphPoints = stats?.graph_points || [];

  const width = 1000;
  const height = 230;
  const padding = { top: 24, right: 42, bottom: 40, left: 14 };

  const plotWidth = width - padding.left - padding.right;
  const plotHeight = height - padding.top - padding.bottom;

  let graphPoints = rawGraphPoints;
  if (!graphPoints || graphPoints.length < 2) {
    const live = stats?.live;
    graphPoints = live ? [{
      time_label: 'Now',
      percent: live.percent,
      is_charging: live.is_charging
    }] : [];
  }

  // Calculate coordinates spanning edge-to-edge
  const pointsWithCoords = useMemo(() => {
    return graphPoints.map((pt, idx) => {
      const x = padding.left + (idx / Math.max(1, graphPoints.length - 1)) * plotWidth;
      const clampedPct = Math.max(0, Math.min(100, pt.percent));
      const y = padding.top + plotHeight - (clampedPct / 100.0) * plotHeight;
      const label = pt.time_label || pt.time || '';
      return { ...pt, x, y, label, clampedPct };
    });
  }, [graphPoints, plotWidth, plotHeight, padding.left, padding.top]);

  // Smooth Catmull-Rom to Cubic Bézier spline path generator
  const { pathD, areaD } = useMemo(() => {
    if (!pointsWithCoords || pointsWithCoords.length === 0) return { pathD: '', areaD: '' };
    if (pointsWithCoords.length === 1) {
      const p = pointsWithCoords[0];
      return {
        pathD: `M ${padding.left} ${p.y} L ${padding.left + plotWidth} ${p.y}`,
        areaD: `M ${padding.left} ${p.y} L ${padding.left + plotWidth} ${p.y} L ${padding.left + plotWidth} ${padding.top + plotHeight} L ${padding.left} ${padding.top + plotHeight} Z`
      };
    }

    let pStr = `M ${pointsWithCoords[0].x.toFixed(1)} ${pointsWithCoords[0].y.toFixed(1)}`;
    for (let i = 0; i < pointsWithCoords.length - 1; i++) {
      const p0 = i > 0 ? pointsWithCoords[i - 1] : pointsWithCoords[i];
      const p1 = pointsWithCoords[i];
      const p2 = pointsWithCoords[i + 1];
      const p3 = i < pointsWithCoords.length - 2 ? pointsWithCoords[i + 2] : p2;

      const tension = 0.26;
      const cp1x = p1.x + (p2.x - p0.x) * tension;
      let cp1y = p1.y + (p2.y - p0.y) * tension;
      const cp2x = p2.x - (p3.x - p1.x) * tension;
      let cp2y = p2.y - (p3.y - p1.y) * tension;

      // Ensure spline doesn't overshoot top/bottom bounds
      cp1y = Math.max(padding.top, Math.min(padding.top + plotHeight, cp1y));
      cp2y = Math.max(padding.top, Math.min(padding.top + plotHeight, cp2y));

      pStr += ` C ${cp1x.toFixed(1)} ${cp1y.toFixed(1)}, ${cp2x.toFixed(1)} ${cp2y.toFixed(1)}, ${p2.x.toFixed(1)} ${p2.y.toFixed(1)}`;
    }

    const last = pointsWithCoords[pointsWithCoords.length - 1];
    const first = pointsWithCoords[0];
    const aStr = `${pStr} L ${last.x.toFixed(1)} ${(padding.top + plotHeight).toFixed(1)} L ${first.x.toFixed(1)} ${(padding.top + plotHeight).toFixed(1)} Z`;

    return { pathD: pStr, areaD: aStr };
  }, [pointsWithCoords, plotWidth, plotHeight, padding.left, padding.top]);

  // Mouse scrubbing & interpolation for 144 FPS responsiveness
  const handleMouseMove = (e) => {
    if (!svgRef.current || pointsWithCoords.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = Math.max(padding.left, Math.min(padding.left + plotWidth, ((e.clientX - rect.left) / rect.width) * width));

    // Find bounding segments
    let i = 0;
    while (i < pointsWithCoords.length - 1 && pointsWithCoords[i + 1].x < mouseX) {
      i++;
    }
    const pA = pointsWithCoords[i];
    const pB = pointsWithCoords[Math.min(pointsWithCoords.length - 1, i + 1)];

    if (pA === pB || pB.x === pA.x) {
      setHoveredPoint({ ...pA, interpX: pA.x, interpY: pA.y, displayPct: Math.round(pA.clampedPct) });
      return;
    }

    const t = Math.max(0, Math.min(1, (mouseX - pA.x) / (pB.x - pA.x)));
    // Linear interpolation for exact tracking
    const interpY = pA.y + (pB.y - pA.y) * t;
    const interpPct = pA.clampedPct + (pB.clampedPct - pA.clampedPct) * t;
    const isCharging = (t > 0.5 ? pB.is_charging : pA.is_charging) || pB.clampedPct > pA.clampedPct;
    const label = t > 0.5 ? (pB.label || pA.label) : (pA.label || pB.label);

    setHoveredPoint({
      interpX: mouseX,
      interpY,
      displayPct: Math.round(interpPct),
      label,
      is_charging: isCharging
    });
  };

  const firstPt = pointsWithCoords[0] || { x: padding.left, y: padding.top, label: '' };
  const lastPt = pointsWithCoords[pointsWithCoords.length - 1] || { x: width - padding.right, y: padding.top + plotHeight, label: '' };

  const screenOnFmt = stats?.screen_on_fmt || stats?.screen_on_formatted || '—';
  const screenOffFmt = stats?.screen_off_fmt || stats?.screen_off_formatted || '—';
  const dischargedPct = stats?.total_drain_pct !== undefined ? `${Math.round(stats.total_drain_pct)}%` : '—';
  const sinceLabel = stats?.since_label || (activeMode === 'today' ? 'Last 24 hours' : activeMode === 'week' ? 'Last 7 days' : 'Waiting for battery history');

  return (
    <div className="glass-group-card" style={{ overflow: 'hidden' }}>
      {/* Top Header Row with Segmented Controls */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '18px 24px 0 24px' }}>
        <div>
          <h3 style={{ fontSize: 16, fontWeight: 700, color: '#ffffff' }}>Battery Levels</h3>
          <p style={{ fontSize: 12, color: 'var(--text-secondary)', marginTop: 2 }}>{sinceLabel}</p>
        </div>

        <div className="samsung-segmented-bar">
          <button
            type="button"
            className={`samsung-seg-item ${activeMode === 'since_charge' ? 'active' : ''}`}
            onClick={() => onModeChange('since_charge')}
          >
            Full charge
          </button>
          <button
            type="button"
            className={`samsung-seg-item ${activeMode === 'today' ? 'active' : ''}`}
            onClick={() => onModeChange('today')}
          >
            24 hours
          </button>
          <button
            type="button"
            className={`samsung-seg-item ${activeMode === 'week' ? 'active' : ''}`}
            onClick={() => onModeChange('week')}
          >
            7 days
          </button>
        </div>
      </div>

      {/* 3 Stat Sub-cards */}
      <div className="pulse-stats-row" style={{ padding: '0 24px' }}>
        <div className="pulse-stat-card">
          <div className="pulse-stat-icon-box">
            <Smartphone size={16} />
          </div>
          <div className="pulse-stat-info">
            <p>Screen on</p>
            <h4>{screenOnFmt}</h4>
          </div>
        </div>

        <div className="pulse-stat-card">
          <div className="pulse-stat-icon-box">
            <Moon size={16} />
          </div>
          <div className="pulse-stat-info">
            <p>Screen off</p>
            <h4>{screenOffFmt}</h4>
          </div>
        </div>

        <div className="pulse-stat-card">
          <div className="pulse-stat-icon-box">
            <TrendingDown size={16} />
          </div>
          <div className="pulse-stat-info">
            <p>Battery discharged</p>
            <h4>{dischargedPct}</h4>
          </div>
        </div>
      </div>

      {/* Discharge Curve Graph Container - Expanded & Widescreen Aligned */}
      <div
        style={{ width: '100%', height: 230, position: 'relative', marginTop: 12, padding: '0 12px' }}
        onMouseMove={handleMouseMove}
        onMouseLeave={() => setHoveredPoint(null)}
      >
        <svg
          ref={svgRef}
          viewBox={`0 0 ${width} ${height}`}
          style={{ width: '100%', height: '100%', display: 'block', overflow: 'visible' }}
        >
          <defs>
            <linearGradient id="blueAreaGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#007aff" stopOpacity="0.32" />
              <stop offset="60%" stopColor="#007aff" stopOpacity="0.08" />
              <stop offset="100%" stopColor="#007aff" stopOpacity="0.0" />
            </linearGradient>
            <filter id="blueGlow" x="-20%" y="-20%" width="140%" height="140%">
              <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="#007aff" floodOpacity="0.75" />
            </filter>
            <filter id="cursorDotGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feDropShadow dx="0" dy="0" stdDeviation="5" floodColor="#38bdf8" floodOpacity="0.9" />
            </filter>
          </defs>

          {/* Reference Grid Lines */}
          <line
            x1={padding.left}
            y1={padding.top}
            x2={padding.left + plotWidth}
            y2={padding.top}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
          <text
            x={padding.left + plotWidth + 6}
            y={padding.top + 4}
            fill="rgba(255, 255, 255, 0.3)"
            fontSize="10"
            fontFamily="monospace"
          >
            100%
          </text>

          <line
            x1={padding.left}
            y1={padding.top + plotHeight * 0.5}
            x2={padding.left + plotWidth}
            y2={padding.top + plotHeight * 0.5}
            stroke="rgba(255, 255, 255, 0.05)"
            strokeDasharray="4 4"
            strokeWidth="1"
          />
          <text
            x={padding.left + plotWidth + 6}
            y={padding.top + plotHeight * 0.5 + 4}
            fill="rgba(255, 255, 255, 0.2)"
            fontSize="10"
            fontFamily="monospace"
          >
            50%
          </text>

          <line
            x1={padding.left}
            y1={padding.top + plotHeight}
            x2={padding.left + plotWidth}
            y2={padding.top + plotHeight}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="1"
          />
          <text
            x={padding.left + plotWidth + 6}
            y={padding.top + plotHeight + 4}
            fill="rgba(255, 255, 255, 0.3)"
            fontSize="10"
            fontFamily="monospace"
          >
            0%
          </text>

          {/* Area Fill */}
          {areaD && (
            <path
              d={areaD}
              fill="url(#blueAreaGradient)"
            />
          )}

          {/* Smooth Bézier Curve Stroke */}
          {pathD && (
            <path
              d={pathD}
              fill="none"
              stroke="#007aff"
              strokeWidth="2.8"
              strokeLinecap="round"
              strokeLinejoin="round"
              filter="url(#blueGlow)"
            />
          )}

          {/* Discrete Key Frame Points */}
          {pointsWithCoords.map((pt, i) => (
            <circle
              key={i}
              cx={pt.x}
              cy={pt.y}
              r={i === 0 || i === pointsWithCoords.length - 1 ? 4.5 : 3}
              fill={pt.is_charging ? '#34d399' : '#007aff'}
              stroke="#080c14"
              strokeWidth="1.8"
              filter="url(#blueGlow)"
            />
          ))}

          {/* X Axis Time Labels */}
          {activeMode === 'week' ? (
            pointsWithCoords.map((pt, i) => (
              <text
                key={i}
                x={pt.x}
                y={height - 10}
                fill="var(--text-tertiary)"
                fontSize="11"
                fontWeight="500"
                textAnchor={i === 0 ? 'start' : i === pointsWithCoords.length - 1 ? 'end' : 'middle'}
              >
                {pt.label}
              </text>
            ))
          ) : (
            <>
              <text x={firstPt.x} y={height - 10} fill="var(--text-tertiary)" fontSize="11" fontWeight="500" textAnchor="start">
                {firstPt.label || '12:04 PM'}
              </text>

              {pointsWithCoords.length > 4 && (
                <text
                  x={pointsWithCoords[Math.floor(pointsWithCoords.length / 2)]?.x}
                  y={height - 10}
                  fill="var(--text-tertiary)"
                  fontSize="11"
                  fontWeight="500"
                  textAnchor="middle"
                >
                  {pointsWithCoords[Math.floor(pointsWithCoords.length / 2)]?.label || '03:00 PM'}
                </text>
              )}

              <text x={lastPt.x} y={height - 10} fill="var(--text-tertiary)" fontSize="11" fontWeight="500" textAnchor="end">
                {lastPt.label || 'Now'}
              </text>
            </>
          )}

          {/* Interactive Scrubbing Cursor Line & Beacon */}
          {hoveredPoint && (
            <g>
              <line
                x1={hoveredPoint.interpX}
                y1={padding.top}
                x2={hoveredPoint.interpX}
                y2={padding.top + plotHeight}
                stroke="rgba(56, 189, 248, 0.55)"
                strokeDasharray="4 3"
                strokeWidth="1.5"
              />
              <circle
                cx={hoveredPoint.interpX}
                cy={hoveredPoint.interpY}
                r="6.5"
                fill="#38bdf8"
                stroke="#ffffff"
                strokeWidth="2.5"
                filter="url(#cursorDotGlow)"
              />
            </g>
          )}
        </svg>

        {/* Floating Glass Tooltip Box */}
        {hoveredPoint && (
          <div
            style={{
              position: 'absolute',
              left: `${(hoveredPoint.interpX / width) * 100}%`,
              top: `${(hoveredPoint.interpY / height) * 100}%`,
              transform: `translate(${hoveredPoint.interpX > width * 0.75 ? '-105%' : hoveredPoint.interpX < width * 0.25 ? '5%' : '-50%'}, -135%)`,
              background: 'rgba(8, 14, 26, 0.94)',
              backdropFilter: 'blur(20px)',
              border: '1px solid rgba(56, 189, 248, 0.35)',
              borderRadius: 'var(--radius-sm)',
              padding: '6px 12px',
              fontSize: '11px',
              color: '#ffffff',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.7), 0 0 1px rgba(255, 255, 255, 0.3)',
              pointerEvents: 'none',
              whiteSpace: 'nowrap',
              zIndex: 30,
              display: 'flex',
              flexDirection: 'column',
              gap: 3
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <span style={{ fontSize: 15, fontWeight: 800, color: '#ffffff' }}>
                {hoveredPoint.displayPct}%
              </span>
              <span
                style={{
                  fontSize: 10,
                  fontWeight: 600,
                  padding: '2px 7px',
                  borderRadius: 999,
                  background: hoveredPoint.is_charging ? 'rgba(56, 189, 248, 0.2)' : 'rgba(52, 211, 153, 0.2)',
                  color: hoveredPoint.is_charging ? '#38bdf8' : '#34d399',
                  border: `1px solid ${hoveredPoint.is_charging ? 'rgba(56, 189, 248, 0.4)' : 'rgba(52, 211, 153, 0.4)'}`
                }}
              >
                {hoveredPoint.is_charging ? '⚡ Charging' : '● Battery'}
              </span>
            </div>
            <span style={{ color: 'var(--text-secondary)', fontSize: 11 }}>
              {hoveredPoint.label}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
