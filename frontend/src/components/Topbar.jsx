import React from 'react';
import { Menu, Terminal } from 'lucide-react';
import StatusIndicator from './StatusIndicator';

/**
 * Topbar Component
 * Header bar displaying system breadcrumb, environment indicators,
 * animated AI status indicator, and profile status.
 */
export default function Topbar({ onToggleMobileSidebar = () => {} }) {
  return (
    <header className="app-topbar">
      <div className="topbar-left">
        <button
          className="mobile-menu-trigger"
          onClick={onToggleMobileSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={20} />
        </button>

        <div className="topbar-context-trail">
          <span className="trail-brand">InsightForge AI</span>
          <span className="trail-separator">/</span>
          <span className="trail-current">Data Intelligence Console</span>
        </div>
      </div>

      <div className="topbar-right">
        {/* Engine mode pill */}
        <div className="engine-badge-pill" title="Execution environment is active">
          <Terminal size={12} className="engine-icon" />
          <span className="engine-name">Sandbox Engine</span>
          <span className="engine-version">v0.1</span>
        </div>

        {/* Small animated AI status indicator (Blue -> Violet -> Cyan) */}
        <StatusIndicator variant="ai" label="AI Engine Active" />

        {/* Profile avatar button */}
        <div className="topbar-profile-badge" title="Active workspace: Enterprise">
          <span className="topbar-avatar-ring">
            <span className="topbar-avatar-core">IF</span>
          </span>
        </div>
      </div>
    </header>
  );
}
