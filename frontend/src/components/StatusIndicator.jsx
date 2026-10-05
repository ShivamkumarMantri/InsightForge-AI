import React, { useState } from 'react';
import { Cpu, ShieldCheck, Sparkles, CheckCircle2 } from 'lucide-react';

/**
 * StatusIndicator Component
 * Futuristic "AI Core" Indicator:
 * - Controlled subtle cyan / green / blue status lighting
 * - Telemetry dots:
 *     ● Online
 *     ● Gemini Connected
 *     ● Safe Analysis Engine
 * - Apple Vision Pro-inspired floating glass capsule with inner specular glow
 */
export default function StatusIndicator({
  variant = 'ai',
  status = 'ready',
  label = 'AI Core Active',
  latency = '18ms',
  showDetails = false
}) {
  const [showTooltip, setShowTooltip] = useState(false);
  const isReady = status === 'ready' || status === 'online';

  return (
    <div
      className="ai-core-indicator-wrap"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      title="InsightForge AI Autonomous Processing Core"
    >
      <div className="ai-core-pill">
        {/* Ambient RGB halo */}
        <span className="ai-core-halo" aria-hidden="true"></span>

        {/* Pulsing AI Core Gem */}
        <span className="ai-core-gem">
          <span className="ai-core-ring"></span>
          <span className="ai-core-dot"></span>
        </span>

        {/* Core title */}
        <span className="ai-core-title">AI Core</span>

        <span className="ai-core-separator"></span>

        {/* Telemetry points */}
        <div className="ai-core-telemetry">
          <span className="telemetry-item item-online">
            <span className="telemetry-dot dot-online"></span>
            <span className="telemetry-label">Online</span>
          </span>

          <span className="telemetry-item item-gemini">
            <span className="telemetry-dot dot-gemini"></span>
            <span className="telemetry-label">Gemini connected</span>
          </span>

          <span className="telemetry-item item-engine">
            <span className="telemetry-dot dot-engine"></span>
            <span className="telemetry-label">Safe Engine</span>
          </span>
        </div>

        {latency && <span className="ai-core-latency">{latency}</span>}
      </div>

      {/* Floating Glass Tooltip Details */}
      {showTooltip && (
        <div className="ai-core-dropdown-card" role="tooltip">
          <div className="dropdown-header">
            <div className="dropdown-icon-box">
              <Cpu size={14} className="text-cyan-400" />
            </div>
            <div>
              <span className="dropdown-title">Autonomous AI Core</span>
              <span className="dropdown-sub">Real-Time Operational Telemetry</span>
            </div>
          </div>

          <div className="dropdown-specs-list">
            <div className="spec-row">
              <span className="spec-key">
                <span className="telemetry-dot dot-online"></span>
                System Status
              </span>
              <span className="spec-val status-green">Online · Optimal</span>
            </div>

            <div className="spec-row">
              <span className="spec-key">
                <span className="telemetry-dot dot-gemini"></span>
                LLM Reasoning
              </span>
              <span className="spec-val status-violet">Gemini 2.5 Active</span>
            </div>

            <div className="spec-row">
              <span className="spec-key">
                <span className="telemetry-dot dot-engine"></span>
                Execution Security
              </span>
              <span className="spec-val status-blue">AST Sandboxed</span>
            </div>

            <div className="spec-row">
              <span className="spec-key">
                <span className="telemetry-dot dot-cyan"></span>
                Kernel Latency
              </span>
              <span className="spec-val">{latency || '18ms'}</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
