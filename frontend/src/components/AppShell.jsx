import React, { useState } from 'react';
import Sidebar from './Sidebar';
import Topbar from './Topbar';
import HeroSection from './HeroSection';
import DatasetUploader from './DatasetUploader';
import SuggestionCard from './SuggestionCard';
import DatasetIntelligence from './DatasetIntelligence';
import {
  TrendingUp,
  BarChart2,
  Award,
  Zap,
  Sparkles,
  History,
  FileSpreadsheet,
  CheckCircle2,
  Sliders,
  Cpu,
  ArrowRight
} from 'lucide-react';

/**
 * AppShell Component
 * Master layout frame orchestrating the topbar, sidebar, dynamic workspace,
 * and seamless transition to the Dataset Intelligence console.
 */
export default function AppShell() {
  const [activeTab, setActiveTab] = useState('new-analysis');
  const [workspaceMode, setWorkspaceMode] = useState('landing'); // 'landing' | 'intelligence'
  const [isMobileSidebarOpen, setIsMobileSidebarOpen] = useState(false);
  const [uploadedDataset, setUploadedDataset] = useState(null);
  const [activeNotice, setActiveNotice] = useState(null);
  const [initialQuery, setInitialQuery] = useState('');
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [recentAnalyses, setRecentAnalyses] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('insightforge_recent_analyses') || '[]');
    } catch {
      return [];
    }
  });

  // Sync recent analyses from server
  React.useEffect(() => {
    async function fetchServerHistory() {
      try {
        let res;
        try {
          res = await fetch('/api/chat/history');
        } catch (_) {
          res = await fetch('http://127.0.0.1:8000/api/chat/history');
        }
        if (res.ok) {
          const serverList = await res.json();
          if (Array.isArray(serverList) && serverList.length > 0) {
            setRecentAnalyses((prev) => {
              const combined = [...prev];
              serverList.forEach((s) => {
                if (!combined.some((c) => c.conversation_id === s.conversation_id)) {
                  combined.push({
                    conversation_id: s.conversation_id,
                    dataset_id: s.dataset_id,
                    filename: s.filename,
                    last_question: s.last_question,
                    timestamp: s.updated_at
                  });
                }
              });
              return combined;
            });
          }
        }
      } catch (e) {
        console.warn('Could not fetch server chat history:', e);
      }
    }
    fetchServerHistory();
  }, []);

  const suggestions = [
    {
      category: 'REVENUE DRIVERS',
      prompt: "Which product generated the highest revenue?",
      icon: TrendingUp
    },
    {
      category: 'TEMPORAL TRENDS',
      prompt: 'Show monthly revenue.',
      icon: BarChart2
    },
    {
      category: 'REGIONAL LEADER',
      prompt: 'Which region generated the most revenue?',
      icon: Award
    },
    {
      category: 'STATISTICAL METRIC',
      prompt: 'What is the average quantity sold?',
      icon: Zap
    }
  ];

  const handleSuggestionClick = (prompt) => {
    setInitialQuery(prompt);
    if (uploadedDataset) {
      setWorkspaceMode('intelligence');
      setActiveNotice(`Query active: "${prompt}"`);
      setTimeout(() => {
        setActiveNotice(null);
      }, 3500);
    } else {
      setActiveNotice(`Selected prompt: "${prompt}". Upload a dataset to analyze.`);
      setTimeout(() => {
        setActiveNotice(null);
      }, 3800);
    }
  };

  const handleUploadSuccess = (datasetInfo) => {
    setUploadedDataset(datasetInfo);
    setActiveNotice(`✓ Dataset "${datasetInfo.filename}" loaded (${datasetInfo.rows.toLocaleString()} rows · ${datasetInfo.columns} columns).`);
    setTimeout(() => {
      setActiveNotice(null);
    }, 4500);
  };

  const handleAnalyzeDataset = (datasetInfo) => {
    setWorkspaceMode('intelligence');
    setActiveNotice(`Profiling dataset "${datasetInfo.filename}" with Pandas.`);
    setTimeout(() => {
      setActiveNotice(null);
    }, 4000);
  };

  const handleBackToUpload = () => {
    setActiveConversationId(null);
    setWorkspaceMode('landing');
  };

  const handleRestoreConversation = (session) => {
    setActiveConversationId(session.conversation_id);
    setUploadedDataset({
      dataset_id: session.dataset_id,
      filename: session.filename || 'dataset.csv',
      rows: 0,
      columns: 0
    });
    setWorkspaceMode('intelligence');
    setActiveTab('new-analysis');
    setActiveNotice(`Restored analysis: "${session.last_question?.slice(0, 35)}..."`);
    setTimeout(() => setActiveNotice(null), 3500);
  };

  const handleSidebarTabSelect = (tabId) => {
    setActiveTab(tabId);
    if (tabId === 'new-analysis' && !uploadedDataset) {
      setWorkspaceMode('landing');
    }
  };

  return (
    <div className="app-shell-root">
      {/* Sidebar Navigation */}
      <Sidebar
        activeTab={activeTab}
        onSelectTab={handleSidebarTabSelect}
        isOpenMobile={isMobileSidebarOpen}
        onCloseMobile={() => setIsMobileSidebarOpen(false)}
        datasetCount={uploadedDataset ? 1 : 0}
      />

      {/* Main Body Area */}
      <div className="app-main-viewport">
        <Topbar
          onToggleMobileSidebar={() => setIsMobileSidebarOpen(!isMobileSidebarOpen)}
        />

        <main className="app-workspace-content">
          {/* Subtle Notification Toast */}
          {activeNotice && (
            <div className="system-toast" role="status">
              <Sparkles size={14} className="toast-sparkle rgb-sparkle" />
              <span>{activeNotice}</span>
            </div>
          )}

          {/* New Analysis View */}
          {activeTab === 'new-analysis' && (
            <>
              {workspaceMode === 'intelligence' && uploadedDataset ? (
                /* Step 3: Dataset Intelligence Console */
                <DatasetIntelligence
                  datasetId={uploadedDataset.dataset_id}
                  filename={uploadedDataset.filename}
                  initialQuery={initialQuery}
                  initialConversationId={activeConversationId}
                  onBack={handleBackToUpload}
                  onConversationUpdated={(updated) => setRecentAnalyses(updated)}
                  onStartQuery={(prompt) => {
                    setActiveNotice(prompt ? `Query queued: "${prompt}"` : 'AI Analyst ready for conversational analysis.');
                    setTimeout(() => setActiveNotice(null), 4000);
                  }}
                />
              ) : (
                /* Landing Workspace / Uploader */
                <div className="workspace-inner-container">
                  {/* Hero Section with very faint RGB atmosphere */}
                  <HeroSection />

                  {/* Upload Experience with functional upload & success UI */}
                  <DatasetUploader
                    onUploadSuccess={handleUploadSuccess}
                    onAnalyze={handleAnalyzeDataset}
                  />

                  {/* Explore Your Data / Suggested Questions */}
                  <section className="explore-section" aria-label="Explore Your Data">
                    <div className="explore-header">
                      <div className="section-eyebrow-row">
                        <span className="section-eyebrow">EXPLORE YOUR DATA</span>
                        <span className="section-eyebrow-divider">/</span>
                        <span className="section-eyebrow-sub">Intelligent Prompts</span>
                      </div>
                      <span className="explore-hint">Select a prompt or type your query</span>
                    </div>

                    <div className="suggestions-grid">
                      {suggestions.map((item, idx) => (
                        <SuggestionCard
                          key={item.prompt}
                          category={item.category}
                          prompt={item.prompt}
                          icon={item.icon}
                          index={idx}
                          accent={['blue', 'violet', 'cyan', 'magenta'][idx % 4]}
                          onSelect={handleSuggestionClick}
                        />
                      ))}
                    </div>
                  </section>

                  {/* Bottom System Specs bar */}
                  <footer className="workspace-system-footer">
                    <div className="footer-spec-item">
                      <span className="spec-label">Security:</span>
                      <span className="spec-val">Sandboxed Python Engine</span>
                    </div>
                    <div className="footer-spec-divider"></div>
                    <div className="footer-spec-item">
                      <span className="spec-label">Latency:</span>
                      <span className="spec-val">Sub-100ms In-Memory Profiling</span>
                    </div>
                    <div className="footer-spec-divider"></div>
                    <div className="footer-spec-item">
                      <span className="spec-label">Provider:</span>
                      <span className="spec-val">FastAPI + Pandas Session Cache</span>
                    </div>
                  </footer>
                </div>
              )}
            </>
          )}

          {/* Datasets View */}
          {activeTab === 'datasets' && (
            <div className="workspace-inner-container secondary-view">
              <div className="view-header">
                <div>
                  <span className="section-eyebrow">DATASET REPOSITORY</span>
                  <h2 className="view-title">Active Datasets</h2>
                </div>
                <button
                  className="choose-dataset-btn"
                  onClick={() => {
                    setWorkspaceMode('landing');
                    setActiveTab('new-analysis');
                  }}
                >
                  <Sparkles size={14} />
                  <span>Upload New</span>
                </button>
              </div>

              {uploadedDataset ? (
                <div className="dataset-list-card">
                  <div className="dataset-item-row">
                    <div className="dataset-icon-wrapper">
                      <FileSpreadsheet size={20} />
                    </div>
                    <div className="dataset-details">
                      <div className="dataset-title-line">
                        <span className="dataset-name">{uploadedDataset.filename}</span>
                        <span className="file-badge">
                          {uploadedDataset.filename.split('.').pop()?.toUpperCase()}
                        </span>
                        <span className="sample-tag">Active Session</span>
                      </div>
                      <span className="dataset-meta">
                        {Number(uploadedDataset.rows).toLocaleString()} rows · {Number(uploadedDataset.columns).toLocaleString()} columns · ID: {uploadedDataset.dataset_id.slice(0, 8)}...
                      </span>
                    </div>
                    <button
                      className="dataset-explore-action"
                      onClick={() => {
                        setWorkspaceMode('intelligence');
                        setActiveTab('new-analysis');
                      }}
                    >
                      <span>Explore Intelligence →</span>
                    </button>
                  </div>
                </div>
              ) : (
                <div className="history-empty-card">
                  <FileSpreadsheet size={32} className="history-icon" />
                  <h3>No datasets uploaded yet</h3>
                  <p>
                    Upload a CSV or Excel file on the New Analysis page to view schema details and start asking questions.
                  </p>
                  <button
                    className="choose-dataset-btn"
                    onClick={() => {
                      setWorkspaceMode('landing');
                      setActiveTab('new-analysis');
                    }}
                  >
                    Upload First Dataset
                  </button>
                </div>
              )}
            </div>
          )}

          {/* History View */}
          {activeTab === 'history' && (
            <div className="workspace-inner-container secondary-view">
              <div className="view-header">
                <div>
                  <span className="section-eyebrow">AUDIT & RECORD LOG</span>
                  <h2 className="view-title">Analysis History</h2>
                </div>
              </div>

              {recentAnalyses && recentAnalyses.length > 0 ? (
                <div className="recent-analyses-container">
                  <div className="recent-analyses-header">
                    <span className="recent-analyses-caption">
                      Recent Analyses ({recentAnalyses.length}) · Stored locally and synchronized with server session cache
                    </span>
                  </div>

                  <div className="recent-analyses-list">
                    {recentAnalyses.map((item, idx) => (
                      <div
                        key={item.conversation_id || idx}
                        className="recent-analysis-card rgb-glow-box"
                        onClick={() => handleRestoreConversation(item)}
                        role="button"
                        tabIndex={0}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRestoreConversation(item);
                        }}
                      >
                        <div className="analysis-card-left">
                          <div className="dataset-icon-wrapper">
                            <Sparkles size={16} className="rgb-sparkle" />
                          </div>
                          <div className="analysis-meta-info">
                            <div className="analysis-title-row">
                              <span className="analysis-dataset-name">
                                {item.filename || 'Dataset'}
                              </span>
                              <span className="file-badge">
                                {(item.filename || 'CSV').split('.').pop()?.toUpperCase()}
                              </span>
                            </div>
                            <p className="analysis-last-question">
                              "{item.last_question || 'General analytical inquiry'}"
                            </p>
                          </div>
                        </div>

                        <div className="analysis-card-right">
                          <span className="analysis-time-badge">
                            {item.timestamp ? new Date(item.timestamp).toLocaleString(undefined, {
                              month: 'short',
                              day: 'numeric',
                              hour: '2-digit',
                              minute: '2-digit'
                            }) : 'Recent'}
                          </span>
                          <button
                            type="button"
                            className="restore-session-btn"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRestoreConversation(item);
                            }}
                          >
                            <span>Resume</span>
                            <ArrowRight size={13} />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="history-empty-card">
                  <History size={32} className="history-icon" />
                  <h3>No prior analytical sessions</h3>
                  <p>
                    Start a new analysis by uploading a dataset and asking questions.
                    Conversational turns, key metrics and chart artifacts will be archived here.
                  </p>
                  <button
                    className="choose-dataset-btn"
                    onClick={() => {
                      setWorkspaceMode('landing');
                      setActiveTab('new-analysis');
                    }}
                  >
                    Start First Analysis
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Settings View */}
          {activeTab === 'settings' && (
            <div className="workspace-inner-container secondary-view">
              <div className="view-header">
                <div>
                  <span className="section-eyebrow">SYSTEM PREFERENCES</span>
                  <h2 className="view-title">Workspace Settings</h2>
                </div>
              </div>

              <div className="settings-grid">
                <div className="settings-panel">
                  <div className="panel-title-row">
                    <Cpu size={16} />
                    <h3>AI Reasoning Engine</h3>
                  </div>
                  <p className="panel-desc">Configure the LLM analyst and execution safety boundary.</p>

                  <div className="setting-control-item">
                    <label>Active Model Provider</label>
                    <div className="setting-input-mock">Claude 3.5 Sonnet / OpenAI GPT-4o (Configured via .env)</div>
                  </div>

                  <div className="setting-control-item">
                    <label>Code Execution Policy</label>
                    <div className="setting-input-mock">AST-Inspected Pandas Sandbox (Restricted)</div>
                  </div>
                </div>

                <div className="settings-panel">
                  <div className="panel-title-row">
                    <Sliders size={16} />
                    <h3>Display & Interface</h3>
                  </div>
                  <p className="panel-desc">Visual tuning and theme configuration.</p>

                  <div className="setting-control-item">
                    <label>Theme</label>
                    <div className="setting-input-mock">Dark Luxury Futuristic (Obsidian / Slate)</div>
                  </div>

                  <div className="setting-control-item">
                    <label>RGB AI Atmosphere</label>
                    <div className="setting-input-mock">Active (Blue → Violet → Cyan subtle aura)</div>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
