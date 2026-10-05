import React, { useState, useEffect } from 'react';
import AIAnalystChat from './AIAnalystChat';
import ExecutiveDashboard from './ExecutiveDashboard';
import { apiFetch } from '../utils/api';
import {
  Layers,
  Columns,
  AlertCircle,
  CheckCircle2,
  Copy,
  Hash,
  Type,
  Calendar,
  Sparkles,
  ArrowLeft,
  RefreshCw,
  Table as TableIcon,
  Activity,
  ArrowRight,
  TrendingUp,
  Cpu,
  MessageSquare,
  BarChart3,
  FileSpreadsheet
} from 'lucide-react';

/**
 * DatasetIntelligence Component
 * Orchestrates the full analytical suite for an active dataset:
 * 1. EXECUTIVE DASHBOARD (AI Auto Insights, KPI Cards, Recharts, IQR Outliers, Data Quality)
 * 2. DATA PROFILING & PREVIEW (Structural Overview, Column Intelligence, Horizontally Scrollable Sample Records)
 * 3. CONVERSATIONAL AI ANALYST (Natural language exploration with Gemini & Pandas Sandbox)
 */
export default function DatasetIntelligence({
  datasetId,
  filename = 'dataset.csv',
  initialQuery = '',
  initialConversationId = null,
  onBack = () => {},
  onStartQuery = () => {},
  onConversationUpdated = () => {}
}) {
  const [activeTab, setActiveTab] = useState(initialQuery ? 'chat' : 'dashboard');
  const [currentChatQuery, setCurrentChatQuery] = useState(initialQuery);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [profile, setProfile] = useState(null);
  const [preview, setPreview] = useState(null);

  useEffect(() => {
    if (!datasetId) return;

    let isMounted = true;
    async function fetchDatasetIntelligence() {
      setLoading(true);
      setError(null);

      try {
        // Fetch profile
        const profileRes = await apiFetch(`/api/dataset/${datasetId}/profile`);
        const profileData = await profileRes.json();

        // Fetch preview rows
        const previewRes = await apiFetch(`/api/dataset/${datasetId}/preview?limit=15`);
        const previewData = await previewRes.json();

        if (isMounted) {
          setProfile(profileData);
          setPreview(previewData);
          setLoading(false);
        }
      } catch (err) {
        console.error('Dataset Intelligence error:', err);
        if (isMounted) {
          setError(err.message || 'Unable to analyze dataset. Please try again.');
          setLoading(false);
        }
      }
    }

    fetchDatasetIntelligence();

    return () => {
      isMounted = false;
    };
  }, [datasetId]);

  const handleAskAI = (prompt) => {
    if (prompt) {
      setCurrentChatQuery(prompt);
    }
    setActiveTab('chat');
    onStartQuery(prompt);
  };

  const getTypeIcon = (type) => {
    switch (type) {
      case 'numeric':
        return <Hash size={13} className="type-icon numeric" />;
      case 'datetime':
        return <Calendar size={13} className="type-icon datetime" />;
      default:
        return <Type size={13} className="type-icon categorical" />;
    }
  };

  const getTypeBadgeClass = (type) => {
    switch (type) {
      case 'numeric':
        return 'type-badge-numeric';
      case 'datetime':
        return 'type-badge-datetime';
      default:
        return 'type-badge-categorical';
    }
  };

  if (error && activeTab === 'profiling') {
    return (
      <div className="intelligence-container">
        <div className="intelligence-error-card rgb-glow-box">
          <AlertCircle size={32} className="error-icon" />
          <h3>Profiling Failed</h3>
          <p>{error}</p>
          <button className="choose-dataset-btn" onClick={onBack}>
            <ArrowLeft size={14} />
            <span>Return to Upload</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="intelligence-container" role="main" aria-label="Dataset Intelligence Console">
      {/* Top action navigation */}
      <div className="intelligence-header-nav">
        <button className="back-nav-btn" onClick={onBack} title="Upload or choose another dataset">
          <ArrowLeft size={14} />
          <span>New Analysis</span>
        </button>

        {/* View Switcher Tabs: Executive Dashboard | Data Profiling | Conversational Analyst */}
        <div className="intelligence-view-tabs" role="tablist" aria-label="Dataset views">
          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'dashboard'}
            className={`view-tab-btn ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
            id="tab-dashboard"
          >
            <Sparkles size={14} className="tab-icon rgb-sparkle" />
            <span>Executive Dashboard</span>
            <span className="tab-pill-badge">AI</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'profiling'}
            className={`view-tab-btn ${activeTab === 'profiling' ? 'active' : ''}`}
            onClick={() => setActiveTab('profiling')}
            id="tab-profiling"
          >
            <Layers size={14} className="tab-icon" />
            <span>Data Profiling & Schema</span>
          </button>

          <button
            type="button"
            role="tab"
            aria-selected={activeTab === 'chat'}
            className={`view-tab-btn ${activeTab === 'chat' ? 'active' : ''}`}
            onClick={() => setActiveTab('chat')}
            id="tab-chat"
          >
            <MessageSquare size={14} className="tab-icon" />
            <span>Conversational Analyst</span>
          </button>
        </div>

        <div className="header-meta-pill">
          <Activity size={12} className="meta-pill-icon rgb-sparkle" />
          <span>Pandas In-Memory Engine</span>
        </div>
      </div>

      {/* VIEW 1: EXECUTIVE DASHBOARD (AI Auto Insights + KPI Cards + Visualizations + Panels) */}
      {activeTab === 'dashboard' && (
        <ExecutiveDashboard
          datasetId={datasetId}
          filename={filename}
          onAskAI={handleAskAI}
          onSwitchToProfiling={() => setActiveTab('profiling')}
          onSwitchToChat={() => setActiveTab('chat')}
        />
      )}

      {/* VIEW 2: CONVERSATIONAL ANALYST */}
      {activeTab === 'chat' && (
        <div className="exec-chat-wrapper">
          <div className="chat-view-header-strip">
            <div className="chat-view-meta">
              <span className="section-eyebrow">CONVERSATIONAL AI ANALYST</span>
              <h2 className="chat-view-title">{filename}</h2>
            </div>
            <button
              type="button"
              className="return-dash-btn"
              onClick={() => setActiveTab('dashboard')}
            >
              <span>← Return to Executive Dashboard</span>
            </button>
          </div>

          <AIAnalystChat
            datasetId={datasetId}
            filename={filename}
            initialQuery={currentChatQuery}
            initialConversationId={initialConversationId}
            onNewAnalysis={onBack}
            onConversationUpdated={onConversationUpdated}
          />
        </div>
      )}

      {/* VIEW 3: DATA PROFILING & PREVIEW */}
      {activeTab === 'profiling' && (
        <div className="profiling-view-wrapper">
          {/* Title & Headline Block */}
          <div className="intelligence-title-row">
            <div>
              <span className="section-eyebrow">DATASET INTELLIGENCE CONSOLE</span>
              <h1 className="intelligence-heading">
                {filename || 'Active Dataset'}
              </h1>
              <p className="intelligence-subtext">
                Autonomous schema detection, anomaly checks, and distributional profiling.
              </p>
            </div>

            {/* Requirement 3: Ask InsightForge button */}
            <button
              className="analyze-dataset-btn rgb-glow-box"
              onClick={() => handleAskAI('Give me an overview of the schema and top variables.')}
            >
              <Sparkles size={15} />
              <span>Ask InsightForge</span>
              <ArrowRight size={15} className="btn-arrow" />
            </button>
          </div>

          {/* 1. DATASET OVERVIEW */}
          <section className="intelligence-section" aria-label="Dataset Overview">
            <div className="section-header-compact">
              <span className="section-label-glow">DATASET OVERVIEW</span>
              <span className="section-caption">Core structural dimensions and integrity score</span>
            </div>

            {loading ? (
              <div className="stat-cards-grid">
                {[1, 2, 3, 4].map((n) => (
                  <div key={n} className="stat-card skeleton-pulse">
                    <div className="skeleton-bar short"></div>
                    <div className="skeleton-bar tall"></div>
                    <div className="skeleton-bar"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="stat-cards-grid">
                {/* Card 1: Rows */}
                <div className="stat-card rgb-glow-box">
                  <div className="stat-top-row">
                    <span className="stat-label">Total Rows</span>
                    <div className="stat-icon-frame">
                      <Layers size={15} />
                    </div>
                  </div>
                  <div className="stat-main-value">
                    {profile?.overview?.total_rows?.toLocaleString() || '0'}
                  </div>
                  <div className="stat-footnote">
                    <span className="footnote-highlight">100%</span> sample analyzed
                  </div>
                </div>

                {/* Card 2: Columns */}
                <div className="stat-card rgb-glow-box">
                  <div className="stat-top-row">
                    <span className="stat-label">Total Columns</span>
                    <div className="stat-icon-frame">
                      <Columns size={15} />
                    </div>
                  </div>
                  <div className="stat-main-value">
                    {profile?.overview?.total_columns || '0'}
                  </div>
                  <div className="stat-footnote">
                    <span>{profile?.overview?.numeric_columns_count || 0} numeric</span>
                    <span className="dot-divider">·</span>
                    <span>{profile?.overview?.categorical_columns_count || 0} text</span>
                    {profile?.overview?.date_columns_count > 0 && (
                      <>
                        <span className="dot-divider">·</span>
                        <span>{profile?.overview?.date_columns_count} date</span>
                      </>
                    )}
                  </div>
                </div>

                {/* Card 3: Missing Values */}
                <div className="stat-card rgb-glow-box">
                  <div className="stat-top-row">
                    <span className="stat-label">Missing Values</span>
                    <div className={`stat-icon-frame ${profile?.overview?.missing_values === 0 ? 'clean' : 'warning'}`}>
                      {profile?.overview?.missing_values === 0 ? (
                        <CheckCircle2 size={15} />
                      ) : (
                        <AlertCircle size={15} />
                      )}
                    </div>
                  </div>
                  <div className="stat-main-value">
                    {profile?.overview?.missing_values?.toLocaleString() || '0'}
                  </div>
                  <div className="stat-footnote">
                    {profile?.overview?.missing_values === 0 ? (
                      <span className="footnote-clean">Clean dataset · 0 null cells</span>
                    ) : (
                      <span className="footnote-warning">Requires imputation or filtering</span>
                    )}
                  </div>
                </div>

                {/* Card 4: Duplicate Rows */}
                <div className="stat-card rgb-glow-box">
                  <div className="stat-top-row">
                    <span className="stat-label">Duplicate Rows</span>
                    <div className="stat-icon-frame">
                      <Copy size={15} />
                    </div>
                  </div>
                  <div className="stat-main-value">
                    {profile?.overview?.duplicate_rows?.toLocaleString() || '0'}
                  </div>
                  <div className="stat-footnote">
                    {profile?.overview?.duplicate_rows === 0 ? (
                      <span className="footnote-clean">Zero redundant records</span>
                    ) : (
                      <span className="footnote-warning">Duplicate entries detected</span>
                    )}
                  </div>
                </div>
              </div>
            )}
          </section>

          {/* 2. COLUMN INTELLIGENCE */}
          <section className="intelligence-section" aria-label="Column Intelligence">
            <div className="section-header-compact">
              <span className="section-label-glow">COLUMN INTELLIGENCE</span>
              <span className="section-caption">Automatic semantic type classification, missing % & sample values</span>
            </div>

            {loading ? (
              <div className="column-cards-list">
                {[1, 2, 3].map((n) => (
                  <div key={n} className="column-intel-card skeleton-pulse">
                    <div className="skeleton-bar tall"></div>
                    <div className="skeleton-bar medium"></div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="column-cards-list">
                {profile?.columns?.map((col) => (
                  <div key={col.name} className="column-intel-card rgb-glow-box">
                    <div className="col-card-header">
                      <div className="col-title-group">
                        <span className="col-name">{col.name}</span>
                        <span className={`col-type-tag ${getTypeBadgeClass(col.data_type)}`}>
                          {getTypeIcon(col.data_type)}
                          <span>{col.data_type.toUpperCase()}</span>
                        </span>
                        <span className="col-pandas-dtype">{col.pandas_dtype}</span>
                      </div>

                      <div className="col-metrics-group">
                        <div className="metric-item">
                          <span className="metric-label">Unique Values:</span>
                          <span className="metric-value">{col.unique_values.toLocaleString()}</span>
                        </div>
                        <div className="metric-divider"></div>
                        <div className="metric-item">
                          <span className="metric-label">Missing:</span>
                          <span className={`metric-value ${col.missing_percentage > 0 ? 'text-warning' : ''}`}>
                            {col.missing_percentage}% ({col.missing_count})
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Example Values */}
                    <div className="col-card-body">
                      <div className="examples-block">
                        <span className="examples-label">Example Values:</span>
                        <div className="examples-chips">
                          {col.examples && col.examples.length > 0 ? (
                            col.examples.map((ex, idx) => (
                              <span key={idx} className="example-chip" title={ex}>
                                {ex}
                              </span>
                            ))
                          ) : (
                            <span className="no-examples">-</span>
                          )}
                        </div>
                      </div>

                      {/* Numeric Stats */}
                      {col.stats && (
                        <div className="numeric-stats-row">
                          <span className="stats-indicator-label">Summary Statistics:</span>
                          <div className="stats-badges-cluster">
                            <div className="stat-pill">
                              <span className="pill-k">Mean:</span>
                              <span className="pill-v">{col.stats.mean !== null ? col.stats.mean.toLocaleString() : '-'}</span>
                            </div>
                            <div className="stat-pill">
                              <span className="pill-k">Median:</span>
                              <span className="pill-v">{col.stats.median !== null ? col.stats.median.toLocaleString() : '-'}</span>
                            </div>
                            <div className="stat-pill">
                              <span className="pill-k">Min:</span>
                              <span className="pill-v">{col.stats.min !== null ? col.stats.min.toLocaleString() : '-'}</span>
                            </div>
                            <div className="stat-pill">
                              <span className="pill-k">Max:</span>
                              <span className="pill-v">{col.stats.max !== null ? col.stats.max.toLocaleString() : '-'}</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </section>

          {/* 3. DATA PREVIEW */}
          <section className="intelligence-section" aria-label="Data Preview">
            <div className="section-header-compact">
              <div className="section-title-with-badge">
                <span className="section-label-glow">DATA PREVIEW</span>
                <span className="preview-count-tag">First {preview?.preview_count || 15} rows</span>
              </div>
              <span className="section-caption">Horizontally scrollable raw records view</span>
            </div>

            {loading ? (
              <div className="preview-table-card skeleton-pulse">
                <div className="skeleton-table-mock"></div>
              </div>
            ) : (
              <div className="preview-table-card rgb-glow-box">
                <div className="table-responsive-wrapper">
                  <table className="data-preview-table">
                    <thead>
                      <tr>
                        <th className="index-th">#</th>
                        {preview?.columns?.map((colName) => {
                          const colInfo = profile?.columns?.find((c) => c.name === colName);
                          return (
                            <th key={colName}>
                              <div className="th-content">
                                <span>{colName}</span>
                                {colInfo && (
                                  <span className={`th-type-mini ${getTypeBadgeClass(colInfo.data_type)}`}>
                                    {colInfo.data_type[0].toUpperCase()}
                                  </span>
                                )}
                              </div>
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody>
                      {preview?.rows?.map((row, rowIdx) => (
                        <tr key={rowIdx}>
                          <td className="index-td">{rowIdx + 1}</td>
                          {preview?.columns?.map((colName) => (
                            <td key={colName} className="cell-value">
                              {row[colName] !== undefined && row[colName] !== null ? String(row[colName]) : '-'}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="table-footer-status">
                  <span>Showing {preview?.rows?.length || 0} of {profile?.overview?.total_rows?.toLocaleString() || 0} records</span>
                  <span className="table-encoding-note">UTF-8 Pandas DataFrame Buffer</span>
                </div>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
