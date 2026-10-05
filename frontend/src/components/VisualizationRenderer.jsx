import React, { useState, useRef } from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend
} from 'recharts';
import {
  BarChart2,
  LineChart as LineChartIcon,
  PieChart as PieChartIcon,
  Maximize2,
  Minimize2,
  Download,
  Image as ImageIcon,
  AlertCircle,
  TrendingUp,
  Activity,
  Layers,
  Sparkles,
  FileSpreadsheet
} from 'lucide-react';
import { downloadChartAsPNG, downloadDataAsCSV } from '../utils/exportUtils';

// Curated luxury futuristic color palette
const LUXURY_COLORS = [
  '#8b5cf6', // Violet
  '#3b82f6', // Blue
  '#06b6d4', // Cyan
  '#10b981', // Emerald
  '#f59e0b', // Amber
  '#ec4899', // Pink
  '#6366f1', // Indigo
  '#14b8a6'  // Teal
];

const formatVal = (val) => {
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1_000_000) {
      return `$${(val / 1_000_000).toFixed(2)}M`;
    }
    if (Math.abs(val) >= 1_000) {
      return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
    }
    return val.toLocaleString(undefined, { maximumFractionDigits: 2 });
  }
  return val;
};

// Luxury Custom Tooltip for Recharts
const CustomLuxuryTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const item = payload[0];
    const rawVal = item.value;
    const nameLabel = label || item.payload?.name || item.name || '';

    return (
      <div className="luxury-chart-tooltip">
        <div className="tooltip-header">
          <span className="tooltip-dot" style={{ backgroundColor: item.color || '#8b5cf6' }}></span>
          <span className="tooltip-label">{nameLabel}</span>
        </div>
        <div className="tooltip-value-row">
          <span className="tooltip-val-key">{item.dataKey || 'Value'}:</span>
          <span className="tooltip-val-num">
            {typeof rawVal === 'number' ? rawVal.toLocaleString(undefined, { maximumFractionDigits: 2 }) : rawVal}
          </span>
        </div>
      </div>
    );
  }
  return null;
};

/**
 * VisualizationRenderer Component
 * Dynamic charting engine that maps Gemini visualization specifications to interactive Recharts.
 * Supports: Bar, Line, Area, Pie/Donut, Scatter, Histogram.
 */
export default function VisualizationRenderer({
  visualization,
  data = [],
  className = ''
}) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const containerRef = useRef(null);

  const vis = visualization || {};
  const chartType = (vis.type || 'bar').toLowerCase();
  const chartTitle = vis.title || `${vis.y || 'Metric'} by ${vis.x || 'Dimension'}`;
  const chartData = (data && data.length > 0) ? data : (vis.data || []);
  const xKey = vis.x || 'name';
  const yKey = vis.y || 'value';

  // Download chart data as clean CSV
  const handleDownloadCSV = (e) => {
    e?.stopPropagation();
    if (!chartData || chartData.length === 0) return;
    const safeTitle = chartTitle.replace(/[^a-z0-9_-]/gi, '_').toLowerCase();
    downloadDataAsCSV(chartData, `InsightForge_${safeTitle}.csv`);
  };

  // Download chart as high-resolution PNG
  const handleDownloadPNG = async (e) => {
    e?.stopPropagation();
    if (!containerRef.current) return;
    const safeTitle = chartTitle.replace(/[^a-z0-9_-]/gi, '_').toLowerCase();
    await downloadChartAsPNG(containerRef.current, `InsightForge_${safeTitle}.png`);
  };

  const getChartIcon = () => {
    switch (chartType) {
      case 'line':
        return <LineChartIcon size={14} className="chart-type-icon" />;
      case 'area':
        return <Activity size={14} className="chart-type-icon" />;
      case 'pie':
      case 'donut':
        return <PieChartIcon size={14} className="chart-type-icon" />;
      case 'scatter':
        return <Sparkles size={14} className="chart-type-icon" />;
      case 'histogram':
      case 'bar':
      default:
        return <BarChart2 size={14} className="chart-type-icon" />;
    }
  };

  // Render the specific Recharts chart element
  const renderChartBody = (height = 320) => {
    if (!chartData || chartData.length === 0) {
      return (
        <div className="chart-empty-state">
          <AlertCircle size={24} className="empty-chart-icon" />
          <p>No quantitative data points available for this visualization specification.</p>
        </div>
      );
    }

    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={chartData} margin={{ top: 15, right: 20, left: 10, bottom: 25 }}>
              <defs>
                <linearGradient id="lineGlow" x1="0" y1="0" x2="1" y2="0">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="50%" stopColor="#3b82f6" />
                  <stop offset="100%" stopColor="#06b6d4" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e212b" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                dy={8}
              />
              <YAxis
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                tickFormatter={formatVal}
              />
              <Tooltip content={<CustomLuxuryTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="url(#lineGlow)"
                strokeWidth={2.5}
                dot={{ fill: '#8b5cf6', stroke: '#121316', strokeWidth: 2, r: 4 }}
                activeDot={{ r: 6, fill: '#06b6d4', stroke: '#ffffff', strokeWidth: 2 }}
                animationDuration={600}
              />
            </LineChart>
          </ResponsiveContainer>
        );

      case 'area':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <AreaChart data={chartData} margin={{ top: 15, right: 20, left: 10, bottom: 25 }}>
              <defs>
                <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.45} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e212b" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                dy={8}
              />
              <YAxis
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                tickFormatter={formatVal}
              />
              <Tooltip content={<CustomLuxuryTooltip />} />
              <Area
                type="monotone"
                dataKey="value"
                stroke="#8b5cf6"
                strokeWidth={2}
                fillOpacity={1}
                fill="url(#areaGradient)"
                animationDuration={600}
              />
            </AreaChart>
          </ResponsiveContainer>
        );

      case 'pie':
      case 'donut':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
              <Tooltip content={<CustomLuxuryTooltip />} />
              <Legend
                verticalAlign="bottom"
                height={36}
                formatter={(val) => <span className="pie-legend-label">{val}</span>}
              />
              <Pie
                data={chartData}
                dataKey="value"
                nameKey="name"
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={98}
                paddingAngle={4}
                animationDuration={600}
              >
                {chartData.map((_, index) => (
                  <Cell
                    key={`cell-${index}`}
                    fill={LUXURY_COLORS[index % LUXURY_COLORS.length]}
                    stroke="#121316"
                    strokeWidth={2}
                  />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        );

      case 'scatter':
        return (
          <ResponsiveContainer width="100%" height={height}>
            <ScatterChart margin={{ top: 15, right: 20, left: 10, bottom: 25 }}>
              <CartesianGrid stroke="#1e212b" strokeDasharray="3 3" />
              <XAxis
                dataKey="x"
                name={vis.x || 'X'}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                tickFormatter={formatVal}
                dy={8}
              />
              <YAxis
                dataKey="y"
                name={vis.y || 'Y'}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                tickFormatter={formatVal}
              />
              <Tooltip content={<CustomLuxuryTooltip />} />
              <Scatter
                name={chartTitle}
                data={chartData}
                fill="#8b5cf6"
                stroke="#38bdf8"
                strokeWidth={1}
                animationDuration={600}
              />
            </ScatterChart>
          </ResponsiveContainer>
        );

      case 'histogram':
      case 'bar':
      default:
        return (
          <ResponsiveContainer width="100%" height={height}>
            <BarChart
              data={chartData}
              margin={{ top: 15, right: 20, left: 10, bottom: 25 }}
              barSize={chartData.length > 8 ? 24 : 36}
            >
              <defs>
                <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#8b5cf6" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
              <CartesianGrid stroke="#1e212b" strokeDasharray="3 3" vertical={false} />
              <XAxis
                dataKey={xKey}
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: chartData.length > 8 ? 10 : 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                dy={chartData.length > 6 ? 6 : 8}
                interval={0}
                angle={chartData.length > 6 ? -18 : 0}
                textAnchor={chartData.length > 6 ? 'end' : 'middle'}
                height={chartData.length > 6 ? 45 : 30}
              />
              <YAxis
                stroke="#475569"
                tick={{ fill: '#94a3b8', fontSize: 11 }}
                tickLine={false}
                axisLine={{ stroke: '#2e3342' }}
                tickFormatter={formatVal}
              />
              <Tooltip content={<CustomLuxuryTooltip />} cursor={{ fill: 'rgba(255, 255, 255, 0.03)' }} />
              <Bar
                dataKey="value"
                fill="url(#barGradient)"
                radius={[4, 4, 0, 0]}
                animationDuration={600}
              >
                {chartData.map((_, index) => (
                  <Cell
                    key={`bar-cell-${index}`}
                    fill={index === 0 ? 'url(#barGradient)' : 'rgba(139, 92, 246, 0.75)'}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  return (
    <>
      <div
        ref={containerRef}
        className={`luxury-chart-container rgb-glow-box ${className}`}
        role="region"
        aria-label={chartTitle}
      >
        {/* Header Controls */}
        <div className="chart-header-row">
          <div className="chart-title-group">
            <span className="chart-type-tag">
              {getChartIcon()}
              <span>{chartType.toUpperCase()}</span>
            </span>
            <h4 className="chart-main-title">{chartTitle}</h4>
          </div>

          <div className="chart-actions-group">
            <button
              type="button"
              className="chart-action-btn"
              onClick={handleDownloadPNG}
              title="Download chart as high-resolution PNG"
              aria-label="Download chart as PNG"
            >
              <ImageIcon size={13} />
              <span>PNG</span>
            </button>

            <button
              type="button"
              className="chart-action-btn"
              onClick={handleDownloadCSV}
              title="Download raw chart data as CSV"
              aria-label="Download chart data"
            >
              <Download size={13} />
              <span>CSV</span>
            </button>

            <button
              type="button"
              className="chart-action-btn icon-only"
              onClick={() => setIsFullscreen(true)}
              title="View chart fullscreen"
              aria-label="Expand chart fullscreen"
            >
              <Maximize2 size={13} />
            </button>
          </div>
        </div>

        {/* Dynamic Interactive Chart */}
        <div className="chart-render-wrapper">
          {renderChartBody(300)}
        </div>

        {/* Subtle Footer Spec Bar */}
        <div className="chart-meta-footer">
          <span className="meta-spec-text">
            X: <strong>{xKey}</strong> · Y: <strong>{yKey}</strong>
          </span>
          <span className="meta-points-count">{chartData.length} records visualized</span>
        </div>
      </div>

      {/* Fullscreen Overlay Modal */}
      {isFullscreen && (
        <div className="chart-fullscreen-modal" role="dialog" aria-modal="true">
          <div className="fullscreen-backdrop" onClick={() => setIsFullscreen(false)}></div>
          <div className="fullscreen-content-card rgb-glow-box">
            <div className="fullscreen-header">
              <div className="chart-title-group">
                <span className="chart-type-tag">
                  {getChartIcon()}
                  <span>{chartType.toUpperCase()}</span>
                </span>
                <h3 className="fullscreen-title">{chartTitle}</h3>
              </div>

              <div className="fullscreen-actions">
                <button
                  type="button"
                  className="chart-action-btn"
                  onClick={handleDownloadPNG}
                  title="Download PNG"
                >
                  <ImageIcon size={14} />
                  <span>Export PNG</span>
                </button>
                <button
                  type="button"
                  className="chart-action-btn"
                  onClick={handleDownloadCSV}
                  title="Download CSV"
                >
                  <Download size={14} />
                  <span>Export CSV</span>
                </button>
                <button
                  type="button"
                  className="fullscreen-close-btn"
                  onClick={() => setIsFullscreen(false)}
                  title="Close fullscreen"
                  aria-label="Close fullscreen"
                >
                  <Minimize2 size={15} />
                </button>
              </div>
            </div>

            <div className="fullscreen-chart-body">
              {renderChartBody(500)}
            </div>
          </div>
        </div>
      )}
    </>
  );
}
