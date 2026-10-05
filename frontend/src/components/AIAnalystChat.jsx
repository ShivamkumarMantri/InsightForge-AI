import React, { useState, useEffect, useRef } from 'react';
import VisualizationRenderer from './VisualizationRenderer';
import {
  Sparkles,
  Send,
  Loader2,
  Calculator,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  AlertCircle,
  TrendingUp,
  BarChart2,
  RotateCcw,
  Plus,
  HelpCircle,
  MessageSquare,
  Clock,
  ArrowRight,
  Download,
  FileSpreadsheet
} from 'lucide-react';
import { downloadDataAsCSV } from '../utils/exportUtils';

/**
 * AIAnalystChat Component (Step 6: Conversational AI Analyst)
 * Features:
 * - Conversational memory per dataset session (conversation_id tracking)
 * - User messages (right-aligned) & AI messages (left-aligned)
 * - Rich AI response: Answer, Key Metric, Dynamic Chart, Why it matters, Collapsible calculation steps
 * - Subtle futuristic thinking indicator: ● Understanding  ● Analyzing  ● Preparing insight
 * - Dynamic follow-up suggestion chips generated per response
 * - "New Analysis" action to clear the active conversation
 * - Integration with Local Storage & Recent Analyses history
 */
export default function AIAnalystChat({
  datasetId,
  filename = 'dataset.csv',
  initialQuery = '',
  initialConversationId = null,
  onNewAnalysis = () => {},
  onConversationUpdated = () => {}
}) {
  const [conversationId, setConversationId] = useState(initialConversationId);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState(initialQuery);
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingStep, setThinkingStep] = useState(0);
  const [error, setError] = useState(null);
  const [expandedCalcs, setExpandedCalcs] = useState({});

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const thinkingSteps = [
    { label: 'Understanding', desc: 'Resolving conversational context & entities' },
    { label: 'Analyzing', desc: 'Executing sandboxed Pandas operations' },
    { label: 'Preparing insight', desc: 'Formulating executive findings & chart visualization' }
  ];

  const defaultSuggestedPrompts = [
    'Which region generated the highest revenue?',
    'Show monthly revenue.',
    'Give me the top 5 products.',
    'What is the average quantity sold?'
  ];

  // Scroll to bottom smoothly when messages or thinking state updates
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isThinking]);

  // Cycle thinking state smoothly while waiting for response
  useEffect(() => {
    let interval;
    if (isThinking) {
      interval = setInterval(() => {
        setThinkingStep((prev) => (prev + 1) % thinkingSteps.length);
      }, 850);
    } else {
      setThinkingStep(0);
    }
    return () => clearInterval(interval);
  }, [isThinking]);

  // Load conversation if initialConversationId provided
  useEffect(() => {
    if (initialConversationId) {
      setConversationId(initialConversationId);
      loadConversationHistory(initialConversationId);
    }
  }, [initialConversationId]);

  const lastProcessedQueryRef = useRef(null);

  // Handle initialQuery if passed or triggered from Executive Dashboard
  useEffect(() => {
    if (initialQuery && initialQuery !== lastProcessedQueryRef.current && !isThinking) {
      lastProcessedQueryRef.current = initialQuery;
      setInputMessage('');
      handleSendMessage(initialQuery);
    }
  }, [initialQuery]);

  const loadConversationHistory = async (convId) => {
    try {
      let res;
      try {
        res = await fetch(`/api/chat/${convId}`);
      } catch (_) {
        res = await fetch(`http://127.0.0.1:8000/api/chat/${convId}`);
      }
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          const formatted = data.messages.map((m) => ({
            id: m.id || String(Math.random()),
            role: m.role,
            text: m.text,
            timestamp: m.timestamp,
            analysisResult: m.analysis || null,
            suggestions: m.analysis?.suggestions || []
          }));
          setMessages(formatted);
        }
      }
    } catch (err) {
      console.warn('Could not load prior conversation from server:', err);
    }
  };

  const saveRecentAnalysisLocally = (convId, lastQuestion) => {
    try {
      const stored = JSON.parse(localStorage.getItem('insightforge_recent_analyses') || '[]');
      const filtered = stored.filter((item) => item.conversation_id !== convId);
      const updated = [
        {
          conversation_id: convId,
          dataset_id: datasetId,
          filename: filename,
          last_question: lastQuestion,
          timestamp: new Date().toISOString()
        },
        ...filtered
      ].slice(0, 10);
      localStorage.setItem('insightforge_recent_analyses', JSON.stringify(updated));
      onConversationUpdated(updated);
    } catch (e) {
      console.warn('Failed to store recent analysis in localStorage:', e);
    }
  };

  const handleSendMessage = async (textToSend) => {
    const q = (textToSend || inputMessage || '').trim();
    if (!q || !datasetId || isThinking) return;

    setError(null);
    setInputMessage('');

    // Append user message immediately
    const userMsgId = `user-${Date.now()}`;
    const userMsg = {
      id: userMsgId,
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    setIsThinking(true);

    try {
      const payload = {
        dataset_id: datasetId,
        message: q
      };
      if (conversationId) {
        payload.conversation_id = conversationId;
      }

      let response;
      try {
        response = await fetch('/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      } catch (_) {
        response = await fetch('http://127.0.0.1:8000/api/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(payload)
        });
      }

      if (!response.ok) {
        const errJson = await response.json().catch(() => ({}));
        throw new Error(errJson.error?.message || errJson.detail || 'Analysis query execution failed.');
      }

      const result = await response.json();

      // Update active conversation ID
      if (result.conversation_id) {
        setConversationId(result.conversation_id);
        saveRecentAnalysisLocally(result.conversation_id, q);
      }

      // Append assistant message
      const aiMsgId = `ai-${Date.now()}`;
      const aiMsg = {
        id: aiMsgId,
        role: 'assistant',
        text: result.answer,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        analysisResult: result,
        suggestions: result.suggestions || []
      };

      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.message || 'Unable to process conversational query. Please try again.');
    } finally {
      setIsThinking(false);
      // Refocus input
      if (textareaRef.current) {
        textareaRef.current.focus();
      }
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputMessage);
    }
  };

  const handleResetConversation = () => {
    setMessages([]);
    setConversationId(null);
    setError(null);
    setInputMessage('');
    onNewAnalysis();
  };

  const toggleCalcExpanded = (msgId) => {
    setExpandedCalcs((prev) => ({
      ...prev,
      [msgId]: !prev[msgId]
    }));
  };

  return (
    <section className="ai-analyst-conversational-section" aria-label="Conversational AI Analyst">
      {/* Analyst Header Bar */}
      <div className="analyst-chat-header">
        <div className="header-left-meta">
          <div className="ai-avatar-badge">
            <Sparkles size={14} className="rgb-sparkle" />
          </div>
          <div className="analyst-info">
            <div className="analyst-name-row">
              <span className="analyst-name">InsightForge Analyst</span>
              <span className="analyst-status-pill">
                <span className="online-indicator"></span>
                <span>Active Session</span>
              </span>
            </div>
            <span className="analyst-subinfo">
              Dataset: <strong>{filename}</strong> {conversationId && `· ID: ${conversationId.slice(0, 8)}`}
            </span>
          </div>
        </div>

        <div className="header-actions">
          <button
            type="button"
            className="new-analysis-action-btn"
            onClick={handleResetConversation}
            title="Clear conversation and begin a fresh analysis"
          >
            <RotateCcw size={13} />
            <span>New Analysis</span>
          </button>
        </div>
      </div>

      {/* Messages Scroll Area */}
      <div className="chat-messages-container" role="log" aria-live="polite">
        {messages.length === 0 && !isThinking && (
          <div className="chat-welcome-state">
            <div className="welcome-icon-wrap rgb-glow-box">
              <MessageSquare size={24} className="rgb-sparkle" />
            </div>
            <h3 className="welcome-heading">Conversational AI Data Analyst</h3>
            <p className="welcome-subtext">
              Ask questions naturally. InsightForge remembers context across follow-ups, resolves pronouns
              (<em>"it"</em>, <em>"that region"</em>, <em>"compare it with South"</em>), and computes verifiable statistics.
            </p>

            <div className="welcome-suggestions-strip">
              <span className="welcome-prompt-label">Quick Start Questions:</span>
              <div className="welcome-chips-row">
                {defaultSuggestedPrompts.map((p) => (
                  <button
                    key={p}
                    type="button"
                    className="quick-question-chip"
                    onClick={() => handleSendMessage(p)}
                  >
                    <span>{p}</span>
                    <ArrowRight size={12} className="chip-arrow" />
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Message Thread */}
        {messages.map((msg) => (
          <div
            key={msg.id}
            className={`chat-message-row ${msg.role === 'user' ? 'user-aligned' : 'ai-aligned'}`}
          >
            {msg.role === 'user' ? (
              /* User Bubble (Right Aligned) */
              <div className="user-message-bubble">
                <p className="user-text-content">{msg.text}</p>
                <span className="message-timestamp">{msg.timestamp}</span>
              </div>
            ) : (
              /* AI Response Card (Left Aligned) */
              <div className="ai-response-card rgb-glow-box">
                {/* Response Card Header */}
                <div className="ai-card-top-bar">
                  <div className="ai-card-tag-pill">
                    <Sparkles size={12} className="rgb-sparkle" />
                    <span>INSIGHT</span>
                  </div>
                  {msg.analysisResult?.context_used && (
                    <span className="context-retained-badge" title="Context remembered from prior questions">
                      ● Context Retained
                    </span>
                  )}
                  <span className="message-timestamp ai-time">{msg.timestamp}</span>
                </div>

                {/* 1. Primary Answer */}
                <h3 className="ai-answer-statement">{msg.text}</h3>

                {/* 2. Key Metric Display */}
                {msg.analysisResult?.key_metric && msg.analysisResult.key_metric !== '-' && (
                  <div className="ai-metric-highlight-box">
                    <span className="metric-glow-number">{msg.analysisResult.key_metric}</span>
                    {msg.analysisResult.insight && (
                      <p className="metric-insight-narrative">{msg.analysisResult.insight}</p>
                    )}
                  </div>
                )}

                {/* 3. Interactive Chart Engine */}
                {msg.analysisResult?.visualization &&
                  msg.analysisResult.visualization.type &&
                  msg.analysisResult.visualization.type !== 'none' && (
                    <div className="ai-chart-surface">
                      <VisualizationRenderer
                        visualization={msg.analysisResult.visualization}
                        data={msg.analysisResult.data}
                      />
                    </div>
                  )}

                {/* Download Analysis Result as CSV */}
                {((msg.analysisResult?.data && msg.analysisResult.data.length > 0) ||
                  (msg.analysisResult?.visualization?.data && msg.analysisResult.visualization.data.length > 0)) && (
                  <div className="ai-message-export-bar">
                    <button
                      type="button"
                      className="ai-download-csv-btn"
                      onClick={() => {
                        const exportData = (msg.analysisResult.data && msg.analysisResult.data.length > 0)
                          ? msg.analysisResult.data
                          : msg.analysisResult.visualization.data;
                        const safeQ = (msg.analysisResult.question || 'analysis')
                          .slice(0, 30)
                          .replace(/[^a-z0-9_-]/gi, '_')
                          .toLowerCase();
                        downloadDataAsCSV(
                          exportData,
                          `InsightForge_${filename.replace(/[^a-z0-9_-]/gi, '_')}_${safeQ}.csv`
                        );
                      }}
                      title="Download query analysis table as CSV"
                      aria-label="Download analysis result as CSV"
                    >
                      <Download size={12} className="btn-icon" />
                      <span>
                        Download Analysis Result (CSV)
                      </span>
                    </button>
                  </div>
                )}

                {/* 4. Why this matters */}
                {msg.analysisResult?.why_it_matters && (
                  <div className="ai-why-matters-box">
                    <div className="why-title-line">
                      <Lightbulb size={14} className="why-icon" />
                      <span>Why this matters</span>
                    </div>
                    <p className="why-text-body">{msg.analysisResult.why_it_matters}</p>
                  </div>
                )}

                {/* 5. Collapsible "How this was calculated" */}
                {msg.analysisResult?.calculation_steps && msg.analysisResult.calculation_steps.length > 0 && (
                  <div className="ai-calculation-collapsible">
                    <button
                      type="button"
                      className="calc-toggle-header"
                      onClick={() => toggleCalcExpanded(msg.id)}
                      aria-expanded={Boolean(expandedCalcs[msg.id])}
                    >
                      <div className="calc-toggle-title">
                        <Calculator size={13} className="calc-icon" />
                        <span>How this was calculated</span>
                      </div>
                      {expandedCalcs[msg.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    </button>

                    {expandedCalcs[msg.id] && (
                      <div className="calc-expanded-body">
                        <ol className="calc-steps-ordered-list">
                          {msg.analysisResult.calculation_steps.map((step, idx) => (
                            <li key={idx} className="calc-step-row">
                              <span className="step-badge">{idx + 1}</span>
                              <span className="step-statement">{step.replace(/^\d+\.\s*/, '')}</span>
                            </li>
                          ))}
                        </ol>

                        {msg.analysisResult.plan && (
                          <div className="safe-plan-code-badge">
                            <code>
                              Operation: {msg.analysisResult.plan.operation} (
                              {msg.analysisResult.plan.group_by
                                ? `group_by='${msg.analysisResult.plan.group_by}'`
                                : ''}
                              {msg.analysisResult.plan.target_column
                                ? `, target='${msg.analysisResult.plan.target_column}'`
                                : ''}
                              {msg.analysisResult.plan.filter
                                ? `, filter=${JSON.stringify(msg.analysisResult.plan.filter)}`
                                : ''}
                              )
                            </code>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* 6. Contextual Follow-Up Suggestions (Step 6) */}
                {msg.suggestions && msg.suggestions.length > 0 && (
                  <div className="follow-up-suggestions-block">
                    <span className="suggestions-eyebrow">Suggested Follow-ups:</span>
                    <div className="suggestion-chips-grid">
                      {msg.suggestions.map((suggestion, sIdx) => (
                        <button
                          key={sIdx}
                          type="button"
                          className="follow-up-chip-btn"
                          onClick={() => handleSendMessage(suggestion)}
                          disabled={isThinking}
                        >
                          <Sparkles size={11} className="suggestion-chip-sparkle" />
                          <span>{suggestion}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}

        {/* Step 5: Subtle Futuristic AI Thinking State */}
        {isThinking && (
          <div className="chat-message-row ai-aligned">
            <div className="thinking-futuristic-card rgb-glow-box" aria-live="assertive">
              <div className="thinking-dots-row">
                {thinkingSteps.map((step, idx) => (
                  <div
                    key={idx}
                    className={`thinking-step-pill ${thinkingStep === idx ? 'step-active' : ''} ${
                      thinkingStep > idx ? 'step-completed' : ''
                    }`}
                  >
                    <span className="futuristic-dot">●</span>
                    <span className="step-label-text">{step.label}</span>
                  </div>
                ))}
              </div>
              <div className="thinking-detail-text">
                <span>{thinkingSteps[thinkingStep]?.desc}</span>
              </div>
            </div>
          </div>
        )}

        {/* Error Banner */}
        {error && (
          <div className="chat-error-banner" role="alert">
            <AlertCircle size={15} />
            <span>{error}</span>
            <button type="button" className="error-dismiss" onClick={() => setError(null)}>
              ✕
            </button>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Bottom Sticky Input Bar */}
      <div className="chat-bottom-input-container">
        <div className="chat-input-bar rgb-glow-box">
          <div className="input-sparkle-lead">
            <Sparkles size={16} className="rgb-sparkle" />
          </div>

          <textarea
            ref={textareaRef}
            rows={1}
            className="chat-textarea-input"
            placeholder="Ask InsightForge anything about your data... (Enter to send, Shift + Enter for new line)"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isThinking}
            aria-label="Ask InsightForge anything about your data"
          />

          <button
            type="button"
            className={`chat-submit-btn ${inputMessage.trim() && !isThinking ? 'btn-ready' : ''}`}
            onClick={() => handleSendMessage(inputMessage)}
            disabled={!inputMessage.trim() || isThinking}
            aria-label="Send message to AI Analyst"
          >
            {isThinking ? (
              <Loader2 size={16} className="spin-loader" />
            ) : (
              <>
                <span>Send</span>
                <Send size={13} className="send-glyph" />
              </>
            )}
          </button>
        </div>

        <div className="input-footer-hint">
          <span>InsightForge Conversational Memory Active · Enter to send · Shift + Enter for new line</span>
        </div>
      </div>
    </section>
  );
}
