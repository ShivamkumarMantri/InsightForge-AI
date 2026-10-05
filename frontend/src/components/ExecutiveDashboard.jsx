import React, { useState, useEffect, useRef } from 'react';
import VisualizationRenderer from './VisualizationRenderer';
import ExportReportModal from './ExportReportModal';
import { apiFetch } from '../utils/api';
import {
  Sparkles,
  TrendingUp,
  TrendingDown,
  DollarSign,
  ShoppingCart,
  CreditCard,
  Activity,
  Award,
  Zap,
  AlertTriangle,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  Layers,
  ChevronRight,
  Filter,
  BarChart2,
  PieChart as PieChartIcon,
  HelpCircle,
  ArrowUpRight,
  Info,
  Download,
  FileText
} from 'lucide-react';

/**
 * ExecutiveDashboard Component
 * Flagship Executive Intelligence Dashboard for InsightForge AI:
 * 1. KPI Cards (Total Revenue, Total Orders, Average Order Value, Growth %)
 * 2. Charts (Revenue Trend, Top 5 Products, Regional Performance via VisualizationRenderer)
 * 3. Panels (AI Discovered Insights, Anomalies with IQR analysis, Data Quality Monitor)
 * 4. AI Connection: "Ask InsightForge" triggers conversational analyst with context preserved.
 */
export default function ExecutiveDashboard({
  datasetId,
  filename = 'dataset.csv',
  onAskAI = () => {},
  onSwitchToProfiling = () => {},
  onSwitchToChat = () => {}
}) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedInsight, setSelectedInsight] = useState(null);
  const [isExportModalOpen, setIsExportModalOpen] = useState(false);

  const revenueTrendRef = useRef(null);
  const topProductsRef = useRef(null);
  const regionalRef = useRef(null);

  const fetchDashboard = async () => {
    if (!datasetId) return;
    setLoading(true);
    setError(null);

    try {
      const res = await apiFetch(`/api/dataset/${datasetId}/dashboard`);
      const data = await res.json();
      setDashboardData(data);
      if (data.ai_discovered && data.ai_discovered.length > 0) {
        setSelectedInsight(data.ai_discovered[0]);
      }
      setLoading(false);
    } catch (err) {
      console.error('Executive dashboard loading error:', err);
      setError(err.message || 'Unable to compute auto insights.');
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboard();
  }, [datasetId]);

  const getInsightIcon = (type) => {
    switch (type) {
      case 'trend':
        return <TrendingUp size={16} className="insight-type-icon trend" />;
      case 'performer':
        return <Award size={16} className="insight-type-icon performer" />;
      case 'driver':
        return <Zap size={16} className="insight-type-icon driver" />;
      case 'anomaly':
        return <AlertTriangle size={16} className="insight-type-icon anomaly" />;
      case 'quality':
      default:
        return <ShieldCheck size={16} className="insight-type-icon quality" />;
    }
  };

  const getInsightPrompt = (insight) => {
    if (!insight) return 'Give me an executive summary of this dataset.';
    switch (insight.type) {
      case 'trend':
        return `Explain the key revenue trend: "${insight.statement}". What drove the peaks and troughs?`;
      case 'performer':
        return `Why is "${insight.statement.split(' is ')[0] || 'the top product'}" performing so well, and what are its growth drivers?`;
      case 'driver':
        return `Analyze the regional performance driver: "${insight.statement}". How can we optimize this?`;
      case 'anomaly':
        return `Investigate the statistical anomalies: "${insight.statement}". Which transactions or products are responsible?`;
      case 'quality':
        return `Provide a breakdown of data quality: "${insight.statement}". What actions are recommended?`;
      default:
        return `Explain this insight: "${insight.statement}"`;
    }
  };

  if (loading) {
    return (
      <div className="exec-dashboard-container">
        {/* Skeleton Header */}
        <div className="exec-header-skeleton skeleton-pulse">
          <div className="skeleton-bar short"></div>
          <div className="skeleton-bar tall"></div>
        </div>

        {/* Skeleton KPIs */}
        <div className="exec-kpis-grid">
          {[1, 2, 3, 4].map((n) => (
            <div key={n} className="kpi-card skeleton-pulse">
              <div className="skeleton-bar short"></div>
              <div className="skeleton-bar tall"></div>
              <div className="skeleton-bar medium"></div>
            </div>
          ))}
        </div>

        {/* Skeleton Panels */}
        <div className="exec-skeleton-grid">
          <div className="exec-card skeleton-pulse tall-mock"></div>
          <div className="exec-card skeleton-pulse tall-mock"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="exec-dashboard-container">
        <div className="intelligence-error-card rgb-glow-box">
          <AlertCircle size={32} className="error-icon" />
          <h3>Autonomous Analysis Error</h3>
          <p>{error}</p>
          <button className="choose-dataset-btn" onClick={fetchDashboard}>
            <RefreshCw size={14} />
            <span>Retry Analysis</span>
          </button>
        </div>
      </div>
    );
  }

  const { kpis, charts, ai_discovered = [], anomalies, data_quality, drivers } = dashboardData || {};

  return (
    <div className="exec-dashboard-container" role="region" aria-label="Executive Intelligence Dashboard">
      {/* Top Executive Header Bar */}
      <div className="exec-dashboard-header">
        <div className="exec-header-left">
          <div className="section-eyebrow-row">
            <span className="section-eyebrow">EXECUTIVE INTELLIGENCE</span>
            <span className="section-eyebrow-divider">/</span>
            <span className="section-eyebrow-sub">Autonomous Auto Insights</span>
          </div>
          <div className="exec-title-row">
            <h1 className="exec-dashboard-title">{filename}</h1>
            <div className="exec-meta-badge">
              <span className="live-dot"></span>
              <span>Pandas Verified</span>
            </div>
          </div>
          <p className="exec-header-subtext">
            Synthesized quantitative performance metrics, Recharts distribution trajectories, and IQR outlier detection.
          </p>
        </div>

        <div className="exec-header-actions">
          {/* Export Report Button */}
          <button
            type="button"
            className="exec-export-btn rgb-glow-box"
            onClick={() => setIsExportModalOpen(true)}
            title="Export AI-Powered PDF Report and executive data"
            id="exec-export-report-btn"
          >
            <FileText size={15} className="btn-icon" />
            <span>Export Report</span>
          </button>

          {/* Requirement 3: Keep the existing "Ask InsightForge" button */}
          <button
            type="button"
            className="ask-insightforge-btn rgb-glow-box"
            onClick={() => onAskAI('Give me a strategic executive summary of this dataset.')}
            title="Ask InsightForge AI conversational questions about this dataset"
            id="exec-ask-insightforge-btn"
          >
            <Sparkles size={16} className="btn-sparkle rgb-sparkle" />
            <span>Ask InsightForge</span>
            <ArrowRight size={14} className="btn-arrow" />
          </button>

          <button
            type="button"
            className="exec-sub-action-btn"
            onClick={fetchDashboard}
            title="Recompute statistical insights"
          >
            <RefreshCw size={14} />
            <span>Recalculate</span>
          </button>
        </div>
      </div>

      {/* 1. EXECUTIVE KPI CARDS */}
      <section className="exec-section" aria-label="Executive KPIs">
        <div className="exec-section-header">
          <span className="section-label-glow">EXECUTIVE PERFORMANCE METRICS</span>
          <span className="section-caption">Core organizational indicators computed dynamically by Pandas</span>
        </div>

        <div className="exec-kpis-grid">
          {/* KPI 1: Total Revenue */}
          <div className="kpi-card rgb-glow-box">
            <div className="kpi-card-top">
              <span className="kpi-label">TOTAL REVENUE</span>
              <div className="kpi-icon-frame revenue">
                <DollarSign size={16} />
              </div>
            </div>
            <div className="kpi-main-val">{kpis?.total_revenue?.formatted || '$0.00'}</div>
            <div className="kpi-footer">
              <span className="kpi-subtext">Gross cumulative analyzed volume</span>
            </div>
          </div>

          {/* KPI 2: Total Orders */}
          <div className="kpi-card rgb-glow-box">
            <div className="kpi-card-top">
              <span className="kpi-label">TOTAL ORDERS</span>
              <div className="kpi-icon-frame orders">
                <ShoppingCart size={16} />
              </div>
            </div>
            <div className="kpi-main-val">{kpis?.total_orders?.formatted || '0'}</div>
            <div className="kpi-footer">
              <span className="kpi-subtext">Total verified records / transactions</span>
            </div>
          </div>

          {/* KPI 3: Average Order Value */}
          <div className="kpi-card rgb-glow-box">
            <div className="kpi-card-top">
              <span className="kpi-label">AVERAGE ORDER VALUE</span>
              <div className="kpi-icon-frame aov">
                <CreditCard size={16} />
              </div>
            </div>
            <div className="kpi-main-val">{kpis?.average_order_value?.formatted || '$0.00'}</div>
            <div className="kpi-footer">
              <span className="kpi-subtext">Mean transaction ticket size</span>
            </div>
          </div>

          {/* KPI 4: Growth % */}
          <div className="kpi-card rgb-glow-box">
            <div className="kpi-card-top">
              <span className="kpi-label">GROWTH RATE</span>
              <div className={`kpi-icon-frame ${kpis?.growth_rate?.trend === 'down' ? 'growth-down' : 'growth-up'}`}>
                {kpis?.growth_rate?.trend === 'down' ? (
                  <TrendingDown size={16} />
                ) : (
                  <TrendingUp size={16} />
                )}
              </div>
            </div>
            <div className="kpi-main-val-group">
              <span className={`kpi-main-val ${kpis?.growth_rate?.trend === 'down' ? 'val-down' : 'val-up'}`}>
                {kpis?.growth_rate?.formatted || '0.0%'}
              </span>
              <span className={`kpi-trend-pill ${kpis?.growth_rate?.trend === 'down' ? 'pill-down' : 'pill-up'}`}>
                {kpis?.growth_rate?.trend === 'down' ? 'Decline' : 'Growth'}
              </span>
            </div>
            <div className="kpi-footer">
              <span className="kpi-subtext">Month-over-month cycle variance</span>
            </div>
          </div>
        </div>
      </section>

      {/* 2. PANEL: AI DISCOVERED INSIGHTS */}
      <section className="exec-section" aria-label="AI Discovered Insights">
        <div className="exec-section-header with-badge">
          <div className="header-title-cluster">
            <div className="ai-discovered-badge rgb-glow-box">
              <Sparkles size={13} className="rgb-sparkle" />
              <span>AI DISCOVERED</span>
            </div>
            <span className="section-caption">5 key executive findings synthesized strictly from Pandas calculations</span>
          </div>
          <span className="ai-no-hallucination-tag">
            <ShieldCheck size={12} />
            <span>Zero Hallucination · Mathematical Truth</span>
          </span>
        </div>

        <div className="ai-discovered-grid">
          {ai_discovered.map((item, idx) => (
            <div
              key={item.id || idx}
              className={`insight-card rgb-glow-box ${selectedInsight?.id === item.id ? 'is-selected' : ''}`}
              onClick={() => setSelectedInsight(item)}
            >
              <div className="insight-card-header">
                <div className="insight-title-group">
                  <div className="insight-icon-box">
                    {getInsightIcon(item.type)}
                  </div>
                  <div className="insight-titles">
                    <span className="insight-type-label">{item.title}</span>
                    <span className="insight-category-sub">{item.category || item.badge}</span>
                  </div>
                </div>
                <span className="insight-badge-pill">{item.badge}</span>
              </div>

              <div className="insight-statement">
                "{item.statement}"
              </div>

              {item.detail && (
                <div className="insight-detail-text">
                  {item.detail}
                </div>
              )}

              <div className="insight-action-footer">
                <button
                  type="button"
                  className="insight-ask-ai-link"
                  onClick={(e) => {
                    e.stopPropagation();
                    onAskAI(getInsightPrompt(item));
                  }}
                  title="Ask Conversational AI about this finding"
                >
                  <Sparkles size={12} className="rgb-sparkle" />
                  <span>Ask AI about this</span>
                  <ArrowRight size={12} />
                </button>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* 3. CHARTS SECTION (Revenue Trend, Top 5 Products, Regional Performance) */}
      <section className="exec-section" aria-label="Executive Charts">
        <div className="exec-section-header">
          <span className="section-label-glow">DYNAMIC EXECUTIVE VISUALIZATIONS</span>
          <span className="section-caption">Automated Recharts rendering from active DataFrame series</span>
        </div>

        {/* Feature Chart: Revenue Trend (Full Width) */}
        {charts?.revenue_trend && (
          <div className="exec-featured-chart-block" ref={revenueTrendRef}>
            <VisualizationRenderer
              visualization={charts.revenue_trend.visualization}
              data={charts.revenue_trend.data}
              className="exec-chart-surface featured"
            />
          </div>
        )}

        {/* 2-Column Grid: Top 5 Products & Regional Performance */}
        <div className="exec-charts-two-col">
          {charts?.top_products && (
            <div className="exec-chart-col" ref={topProductsRef}>
              <VisualizationRenderer
                visualization={charts.top_products.visualization}
                data={charts.top_products.data}
                className="exec-chart-surface"
              />
            </div>
          )}

          {charts?.regional_performance && (
            <div className="exec-chart-col" ref={regionalRef}>
              <VisualizationRenderer
                visualization={charts.regional_performance.visualization}
                data={charts.regional_performance.data}
                className="exec-chart-surface"
              />
            </div>
          )}
        </div>
      </section>

      {/* 4. PANELS: ANOMALIES & DATA QUALITY */}
      <div className="exec-panels-two-col">
        {/* Panel A: Statistical Anomalies (IQR) */}
        <section className="exec-panel-card rgb-glow-box" aria-label="Statistical Anomalies Panel">
          <div className="panel-header-row">
            <div className="panel-title-group">
              <div className="panel-icon-wrap warning">
                <AlertTriangle size={16} />
              </div>
              <div>
                <h3 className="panel-main-title">Statistical Anomalies</h3>
                <span className="panel-sub-label">IQR Outlier Detection (1.5 × Interquartile Range)</span>
              </div>
            </div>

            <div className="panel-meta-tag">
              <span>Target: <strong>{anomalies?.column || 'Revenue'}</strong></span>
            </div>
          </div>

          {/* Statistical IQR Metrics */}
          <div className="anomaly-stats-strip">
            <div className="anomaly-stat-pill">
              <span className="pill-metric-label">IQR Spread</span>
              <span className="pill-metric-val">{anomalies?.iqr?.toLocaleString() || '0'}</span>
            </div>
            <div className="anomaly-stat-pill">
              <span className="pill-metric-label">Upper Threshold</span>
              <span className="pill-metric-val">${anomalies?.upper_bound?.toLocaleString() || '0'}</span>
            </div>
            <div className="anomaly-stat-pill highlight">
              <span className="pill-metric-label">Outliers Found</span>
              <span className="pill-metric-val text-warning">
                {anomalies?.outlier_count || 0} ({anomalies?.outlier_pct || 0}%)
              </span>
            </div>
            <div className="anomaly-stat-pill">
              <span className="pill-metric-label">Max Anomaly</span>
              <span className="pill-metric-val">${anomalies?.max_outlier?.toLocaleString() || '0'}</span>
            </div>
          </div>

          {/* Outlier Sample Records */}
          <div className="anomaly-samples-block">
            <span className="block-label">Sample Outlier Records:</span>
            {anomalies?.samples && anomalies.samples.length > 0 ? (
              <div className="anomaly-table-wrap">
                <table className="anomaly-mini-table">
                  <thead>
                    <tr>
                      <th>Row</th>
                      <th>Product</th>
                      <th>Region</th>
                      <th className="text-right">Transaction Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {anomalies.samples.map((s, idx) => (
                      <tr key={s.id || idx}>
                        <td className="row-id">#{s.id}</td>
                        <td className="product-cell">{s.product}</td>
                        <td className="region-cell">{s.region}</td>
                        <td className="text-right value-cell">{s.formatted || `$${s.value}`}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="clean-anomaly-notice">
                <CheckCircle2 size={15} className="clean-icon" />
                <span>Zero statistical outliers detected within the 1.5 IQR bounds.</span>
              </div>
            )}
          </div>

          <div className="panel-footer-action">
            <button
              type="button"
              className="panel-action-btn"
              onClick={() => onAskAI(`Investigate the ${anomalies?.outlier_count || 0} statistical outliers detected above the upper bound of $${anomalies?.upper_bound?.toLocaleString()}. Which specific items or regions generated them?`)}
            >
              <Sparkles size={13} className="rgb-sparkle" />
              <span>Ask AI to investigate anomalies</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </section>

        {/* Panel B: Data Quality Monitor */}
        <section className="exec-panel-card rgb-glow-box" aria-label="Data Quality Panel">
          <div className="panel-header-row">
            <div className="panel-title-group">
              <div className="panel-icon-wrap quality">
                <ShieldCheck size={16} />
              </div>
              <div>
                <h3 className="panel-main-title">Data Quality</h3>
                <span className="panel-sub-label">Automated Schema Hygiene & Integrity Audit</span>
              </div>
            </div>

            <div className={`quality-status-badge ${data_quality?.score >= 95 ? 'optimal' : (data_quality?.score >= 80 ? 'healthy' : 'warning')}`}>
              <span className="status-dot"></span>
              <span>{data_quality?.status || 'Verified'}</span>
            </div>
          </div>

          {/* Quality Score & Hygiene Breakdown */}
          <div className="quality-score-hero">
            <div className="quality-number-wrap">
              <span className="quality-huge-num">{data_quality?.score ?? 100}</span>
              <span className="quality-denom">/100</span>
            </div>
            <div className="quality-score-desc">
              <span className="quality-verdict-title">
                {data_quality?.score >= 95 ? 'Optimal Schema Integrity' : 'Requires Attention'}
              </span>
              <p className="quality-verdict-p">
                {data_quality?.score >= 95
                  ? 'Dataset complies fully with analytical standards. Zero data-loss risks detected.'
                  : 'Noticeable null cells or duplicate entries found. Consider cleaning before deployment.'}
              </p>
            </div>
          </div>

          {/* Metrics Matrix */}
          <div className="quality-metrics-grid">
            <div className="quality-metric-box">
              <span className="qm-label">Duplicate Rows</span>
              <span className={`qm-val ${data_quality?.duplicate_rows === 0 ? 'text-clean' : 'text-warning'}`}>
                {data_quality?.duplicate_rows?.toLocaleString() || 0}
              </span>
              <span className="qm-sub">{data_quality?.duplicate_rows === 0 ? '0% redundancy' : 'Deduplication advised'}</span>
            </div>

            <div className="quality-metric-box">
              <span className="qm-label">Missing Cells</span>
              <span className={`qm-val ${data_quality?.missing_cells === 0 ? 'text-clean' : 'text-warning'}`}>
                {data_quality?.missing_cells?.toLocaleString() || 0}
              </span>
              <span className="qm-sub">{data_quality?.missing_pct || 0}% null density</span>
            </div>

            <div className="quality-metric-box">
              <span className="qm-label">Total Records</span>
              <span className="qm-val">{data_quality?.total_rows?.toLocaleString() || 0}</span>
              <span className="qm-sub">100% ingested</span>
            </div>

            <div className="quality-metric-box">
              <span className="qm-label">Columns</span>
              <span className="qm-val">{data_quality?.total_columns || 0}</span>
              <span className="qm-sub">Parsed schema</span>
            </div>
          </div>

          <div className="panel-footer-action">
            <button
              type="button"
              className="panel-action-btn secondary"
              onClick={onSwitchToProfiling}
            >
              <Layers size={13} />
              <span>Inspect column data types & distribution</span>
              <ArrowRight size={13} />
            </button>
          </div>
        </section>
      </div>

      {/* Bottom Sticky Floating AI Connection Bar */}
      <div className="exec-floating-ai-bar rgb-glow-box">
        <div className="floating-left">
          <div className="floating-sparkle-frame">
            <Sparkles size={16} className="rgb-sparkle" />
          </div>
          <div className="floating-text-block">
            <span className="floating-title">Ready for deeper conversational intelligence?</span>
            <span className="floating-sub">Ask any strategic question with memory and Pandas execution intact.</span>
          </div>
        </div>

        <div className="floating-right">
          <button
            type="button"
            className="floating-ask-btn"
            onClick={() => onAskAI('')}
          >
            <span>Ask InsightForge AI</span>
            <ArrowRight size={14} />
          </button>
        </div>
      </div>

      {/* Flagship Executive Export Modal */}
      <ExportReportModal
        isOpen={isExportModalOpen}
        onClose={() => setIsExportModalOpen(false)}
        dashboardData={dashboardData}
        filename={filename}
        datasetId={datasetId}
        chartElements={{
          revenueTrend: revenueTrendRef.current,
          topProducts: topProductsRef.current,
          regional: regionalRef.current
        }}
      />
    </div>
  );
}
