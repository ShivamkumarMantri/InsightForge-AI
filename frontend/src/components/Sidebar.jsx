import React from 'react';
import {
  Sparkles,
  Database,
  History,
  Settings,
  X,
  Layers,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';
import StatusIndicator from './StatusIndicator';

/**
 * Sidebar Component
 * Refined, subtle dark luxury navigation sidebar with Lucide icons.
 */
export default function Sidebar({
  activeTab = 'new-analysis',
  onSelectTab = () => {},
  isOpenMobile = false,
  onCloseMobile = () => {},
  datasetCount = 1
}) {
  const navItems = [
    {
      id: 'new-analysis',
      label: 'New Analysis',
      icon: Sparkles,
      badge: 'AI'
    },
    {
      id: 'datasets',
      label: 'Datasets',
      icon: Database,
      count: String(datasetCount)
    },
    {
      id: 'history',
      label: 'Analysis History',
      icon: History
    }
  ];

  return (
    <>
      {/* Mobile backdrop */}
      {isOpenMobile && (
        <div
          className="sidebar-backdrop"
          onClick={onCloseMobile}
          aria-hidden="true"
        />
      )}

      <aside className={`app-sidebar ${isOpenMobile ? 'mobile-open' : ''}`}>
        {/* Brand Header */}
        <div className="sidebar-brand-wrapper">
          <div className="sidebar-brand">
            <div className="brand-logo-mark rgb-subtle-glow">
              <span className="brand-inner-glow"></span>
              <Sparkles size={17} className="brand-icon" />
            </div>
            <div className="brand-text-block">
              <div className="brand-title-row">
                <span className="brand-name">InsightForge</span>
                <span className="brand-badge">AI</span>
              </div>
              <span className="brand-subtext">Data Intelligence</span>
            </div>
          </div>

          <button
            className="mobile-close-btn"
            onClick={onCloseMobile}
            aria-label="Close sidebar"
          >
            <X size={18} />
          </button>
        </div>

        {/* Navigation Section */}
        <div className="sidebar-section-title">WORKSPACE</div>
        <nav className="sidebar-nav" aria-label="Main Navigation">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                className={`nav-btn ${isActive ? 'active' : ''}`}
                onClick={() => {
                  onSelectTab(item.id);
                  if (isOpenMobile) onCloseMobile();
                }}
              >
                <div className="nav-btn-content">
                  <Icon size={16} className="nav-icon" />
                  <span className="nav-label">{item.label}</span>
                </div>
                {item.badge && <span className="nav-badge-ai rgb-badge-pulse">{item.badge}</span>}
                {item.count && <span className="nav-count">{item.count}</span>}
              </button>
            );
          })}
        </nav>

        {/* Middle Context Area */}
        <div className="sidebar-middle-card">
          <div className="middle-card-header">
            <Layers size={13} className="middle-card-icon" />
            <span>Active Engine</span>
          </div>
          <p className="middle-card-text">
            Autonomous data profiling & analysis engine initialized.
          </p>
          <div className="middle-card-meta">
            <ShieldCheck size={12} className="meta-icon" />
            <span>Safe Pandas Sandbox</span>
          </div>
        </div>

        {/* Bottom Section */}
        <div className="sidebar-bottom">
          <div className="sidebar-status-container">
            <StatusIndicator label="API Ready" status="ready" latency="18ms" showDetails={true} />
          </div>

          <button
            className={`nav-btn settings-btn ${activeTab === 'settings' ? 'active' : ''}`}
            onClick={() => {
              onSelectTab('settings');
              if (isOpenMobile) onCloseMobile();
            }}
          >
            <div className="nav-btn-content">
              <Settings size={16} className="nav-icon" />
              <span className="nav-label">Settings</span>
            </div>
            <ChevronRight size={14} className="nav-arrow" />
          </button>

          {/* User Profile Area */}
          <div className="user-profile-tile">
            <div className="user-avatar-frame">
              <span className="avatar-initials">IF</span>
              <span className="user-online-ping"></span>
            </div>
            <div className="user-meta-block">
              <span className="user-display-name">Research Lab</span>
              <span className="user-role-label">Enterprise Workspace</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
