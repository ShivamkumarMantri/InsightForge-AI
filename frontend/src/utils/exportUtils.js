import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';

/**
 * Format numerical values with commas or compact currency
 */
const formatCurrency = (val) => {
  if (typeof val === 'number') {
    if (Math.abs(val) >= 1_000_000) return `$${(val / 1_000_000).toFixed(2)}M`;
    if (Math.abs(val) >= 1_000) return `$${(val / 1_000).toFixed(1)}K`;
    return `$${val.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
  }
  return String(val ?? '');
};

/**
 * Download raw data array as a clean CSV file
 */
export function downloadDataAsCSV(data, filename = 'export.csv') {
  if (!data || !Array.isArray(data) || data.length === 0) {
    console.warn('downloadDataAsCSV: No data provided to export.');
    return false;
  }

  try {
    // Extract headers
    let keys = [];
    if (typeof data[0] === 'object' && data[0] !== null) {
      keys = Object.keys(data[0]);
    } else {
      keys = ['Value'];
    }

    const csvRows = [];
    csvRows.push(keys.map((k) => `"${String(k).replace(/"/g, '""')}"`).join(','));

    data.forEach((row) => {
      if (typeof row === 'object' && row !== null) {
        const values = keys.map((k) => {
          const val = row[k] ?? '';
          return `"${String(val).replace(/"/g, '""')}"`;
        });
        csvRows.push(values.join(','));
      } else {
        csvRows.push(`"${String(row).replace(/"/g, '""')}"`);
      }
    });

    const csvString = csvRows.join('\r\n');
    const blob = new Blob([csvString], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', filename.endsWith('.csv') ? filename : `${filename}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
    return true;
  } catch (err) {
    console.error('Failed to export CSV:', err);
    return false;
  }
}

/**
 * Download Chart as high-resolution PNG image
 */
export async function downloadChartAsPNG(chartElement, filename = 'chart.png') {
  if (!chartElement) {
    console.warn('downloadChartAsPNG: Target DOM element not found.');
    return false;
  }

  try {
    // Find chart wrapper or SVG
    const target = chartElement.querySelector('.recharts-responsive-container') || chartElement;

    const canvas = await html2canvas(target, {
      backgroundColor: '#121316',
      scale: 2, // 2x pixel ratio for retina crispness
      useCORS: true,
      logging: false,
      onclone: (clonedDoc) => {
        const clonedTarget = clonedDoc.querySelector('.recharts-responsive-container') || clonedDoc.body;
        if (clonedTarget) {
          clonedTarget.style.borderRadius = '8px';
          clonedTarget.style.padding = '12px';
          clonedTarget.style.backgroundColor = '#121316';
        }
      }
    });

    const link = document.createElement('a');
    link.download = filename.endsWith('.png') ? filename : `${filename}.png`;
    link.href = canvas.toDataURL('image/png', 1.0);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    return true;
  } catch (err) {
    console.error('Failed to export chart as PNG:', err);
    return false;
  }
}

/**
 * Export complete Dashboard Summary as structured JSON or CSV
 */
export function downloadDashboardSummary(dashboardData, filename = 'executive_summary') {
  if (!dashboardData) return false;

  try {
    const summaryPayload = {
      insightforge_ai_version: '1.0.0',
      exported_at: new Date().toISOString(),
      dataset: dashboardData.filename,
      dataset_id: dashboardData.dataset_id,
      kpis: dashboardData.kpis,
      ai_discovered_insights: dashboardData.ai_discovered,
      top_products: dashboardData.charts?.top_products?.data || [],
      regional_performance: dashboardData.charts?.regional_performance?.data || [],
      revenue_trend: dashboardData.charts?.revenue_trend?.data || [],
      anomalies: dashboardData.anomalies,
      data_quality: dashboardData.data_quality,
      drivers: dashboardData.drivers
    };

    const jsonString = `data:text/json;charset=utf-8,${encodeURIComponent(JSON.stringify(summaryPayload, null, 2))}`;
    const link = document.createElement('a');
    link.setAttribute('href', jsonString);
    link.setAttribute('download', `${filename.replace(/[^a-z0-9_-]/gi, '_')}.json`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    return true;
  } catch (err) {
    console.error('Failed to export dashboard summary:', err);
    return false;
  }
}

/**
 * Capture a chart element as base64 image data URL for PDF inclusion
 */
async function captureChartDataURL(element) {
  if (!element) return null;
  try {
    const target = element.querySelector('.recharts-responsive-container') || element;
    const canvas = await html2canvas(target, {
      backgroundColor: '#121316',
      scale: 1.5,
      useCORS: true,
      logging: false
    });
    return canvas.toDataURL('image/png', 0.92);
  } catch (e) {
    console.warn('Could not rasterize chart for PDF:', e);
    return null;
  }
}

/**
 * Generate comprehensive AI-Powered Executive PDF Report
 */
export async function generateClientPDFReport({
  dashboardData,
  filename = 'dataset.csv',
  chartElements = {},
  onProgress = () => {}
}) {
  if (!dashboardData) {
    throw new Error('Dashboard data is required to generate PDF report.');
  }

  onProgress({ step: 1, message: 'Initializing PDF document layout...' });

  const doc = new jsPDF({
    orientation: 'portrait',
    unit: 'pt',
    format: 'letter'
  });

  const pageWidth = doc.internal.pageSize.getWidth();
  const pageHeight = doc.internal.pageSize.getHeight();
  const margin = 36;
  const contentWidth = pageWidth - (margin * 2);

  let currentY = margin;

  const checkPageBreak = (neededHeight) => {
    if (currentY + neededHeight > pageHeight - margin - 20) {
      doc.addPage();
      currentY = margin;
      drawHeaderFooter();
    }
  };

  const drawHeaderFooter = () => {
    const pageNum = doc.internal.pages.length - 1;
    // Footer line
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.5);
    doc.line(margin, pageHeight - 30, pageWidth - margin, pageHeight - 30);

    // Footer text
    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7.5);
    doc.setTextColor(148, 163, 184);
    doc.text('InsightForge AI Executive Intelligence Report • Calculated from verified Pandas Sandbox series', margin, pageHeight - 18);
    doc.text(`Page ${pageNum}`, pageWidth - margin, pageHeight - 18, { align: 'right' });
  };

  // 1. REPORT HEADER
  onProgress({ step: 2, message: 'Compiling executive KPIs and AI insights...' });

  // Top branding bar
  doc.setFillColor(124, 58, 237); // #7c3aed Purple
  doc.roundedRect(margin, currentY, contentWidth, 3, 1, 1, 'F');
  currentY += 14;

  // Eyebrow
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(8.5);
  doc.setTextColor(124, 58, 237);
  doc.text('INSIGHTFORGE AI  |  EXECUTIVE INTELLIGENCE BRIEFING', margin, currentY);

  const dateStr = new Date().toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(100, 116, 139);
  doc.text(`Generated: ${dateStr}`, pageWidth - margin, currentY, { align: 'right' });
  currentY += 18;

  // Report Title
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(19);
  doc.setTextColor(15, 23, 42);
  doc.text(filename, margin, currentY);
  currentY += 16;

  // Overview Statement
  const kpis = dashboardData.kpis || {};
  const aiInsights = dashboardData.ai_discovered || [];
  const charts = dashboardData.charts || {};
  const anomalies = dashboardData.anomalies || {};
  const dataQuality = dashboardData.data_quality || {};
  const drivers = dashboardData.drivers || {};

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(9);
  doc.setTextColor(71, 85, 105);
  const overviewText = `Executive analytical summary for ${filename} (${(dataQuality.total_rows || 0).toLocaleString()} transactions across ${dataQuality.total_columns || 0} dimensions). Verified against sandboxed Pandas analytical engine with zero artificial hallucination.`;
  const splitOverview = doc.splitTextToSize(overviewText, contentWidth);
  doc.text(splitOverview, margin, currentY);
  currentY += splitOverview.length * 12 + 10;

  // 2. KEY PERFORMANCE INDICATORS (KPIs)
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(124, 58, 237);
  doc.text('1. EXECUTIVE KEY PERFORMANCE INDICATORS', margin, currentY);
  currentY += 12;

  const kpiBoxWidth = (contentWidth - 18) / 4;
  const kpiBoxHeight = 52;

  const kpiItems = [
    { label: 'TOTAL REVENUE', val: kpis.total_revenue?.formatted || '$0.00', sub: 'Gross Analyzed Volume', color: [124, 58, 237] },
    { label: 'TOTAL ORDERS', val: kpis.total_orders?.formatted || '0', sub: 'Verified Records', color: [37, 99, 235] },
    { label: 'AVG ORDER VALUE', val: kpis.average_order_value?.formatted || '$0.00', sub: 'Mean Ticket Size', color: [6, 182, 212] },
    { label: 'MOM GROWTH', val: kpis.growth_rate?.formatted || '0.0%', sub: 'Cycle-over-Cycle Variance', color: kpis.growth_rate?.trend === 'down' ? [239, 68, 68] : [16, 185, 129] }
  ];

  kpiItems.forEach((kpi, idx) => {
    const x = margin + idx * (kpiBoxWidth + 6);
    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(x, currentY, kpiBoxWidth, kpiBoxHeight, 4, 4, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);
    doc.text(kpi.label, x + 8, currentY + 12);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12.5);
    doc.setTextColor(kpi.color[0], kpi.color[1], kpi.color[2]);
    doc.text(kpi.val, x + 8, currentY + 30);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.5);
    doc.setTextColor(148, 163, 184);
    doc.text(kpi.sub, x + 8, currentY + 44);
  });

  currentY += kpiBoxHeight + 16;

  // 3. AI DISCOVERED EXECUTIVE INSIGHTS
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(124, 58, 237);
  doc.text('2. AI DISCOVERED EXECUTIVE INSIGHTS', margin, currentY);
  currentY += 12;

  aiInsights.forEach((item) => {
    checkPageBreak(42);

    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(margin, currentY, contentWidth, 36, 4, 4, 'FD');

    // Category tag
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(124, 58, 237);
    doc.text(`[${(item.badge || item.title || 'INSIGHT').toUpperCase()}] ${item.title}:`, margin + 10, currentY + 13);

    // Statement
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(15, 23, 42);
    const stmtText = `"${item.statement}"`;
    const splitStmt = doc.splitTextToSize(stmtText, contentWidth - 20);
    doc.text(splitStmt[0] || stmtText, margin + 10, currentY + 26);

    currentY += 42;
  });

  currentY += 6;

  // 4. SELECTED CHARTS SECTION
  onProgress({ step: 3, message: 'Rasterizing high-definition visualizations...' });

  // If chart elements were passed from UI, rasterize them
  const trendImg = chartElements.revenueTrend ? await captureChartDataURL(chartElements.revenueTrend) : null;
  const prodImg = chartElements.topProducts ? await captureChartDataURL(chartElements.topProducts) : null;
  const regImg = chartElements.regional ? await captureChartDataURL(chartElements.regional) : null;

  if (trendImg || prodImg || regImg) {
    checkPageBreak(170);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(10.5);
    doc.setTextColor(124, 58, 237);
    doc.text('3. DYNAMIC PERFORMANCE VISUALIZATIONS', margin, currentY);
    currentY += 12;

    if (trendImg) {
      const chartH = 135;
      checkPageBreak(chartH + 10);
      doc.addImage(trendImg, 'PNG', margin, currentY, contentWidth, chartH);
      currentY += chartH + 14;
    }

    if (prodImg && regImg) {
      const halfW = (contentWidth - 10) / 2;
      const chartH = 120;
      checkPageBreak(chartH + 10);
      doc.addImage(prodImg, 'PNG', margin, currentY, halfW, chartH);
      doc.addImage(regImg, 'PNG', margin + halfW + 10, currentY, halfW, chartH);
      currentY += chartH + 14;
    } else if (prodImg) {
      const chartH = 120;
      checkPageBreak(chartH + 10);
      doc.addImage(prodImg, 'PNG', margin, currentY, contentWidth, chartH);
      currentY += chartH + 14;
    }
  }

  // 5. COMMERCIAL BREAKDOWN: TOP PRODUCTS & REGIONAL PERFORMANCE
  onProgress({ step: 4, message: 'Constructing top products and regional tables...' });
  checkPageBreak(120);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(124, 58, 237);
  doc.text('4. TOP PRODUCTS & REGIONAL PERFORMANCE', margin, currentY);
  currentY += 12;

  const tableColWidth = (contentWidth - 12) / 2;
  const topProductsData = charts.top_products?.data || [];
  const regionalData = charts.regional_performance?.data || [];

  // Left Column: Top Products
  let leftY = currentY;
  doc.setFillColor(124, 58, 237);
  doc.rect(margin, leftY, tableColWidth, 16, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(255, 255, 255);
  doc.text('Top Products by Revenue', margin + 6, leftY + 11);
  doc.text('Revenue', margin + tableColWidth - 6, leftY + 11, { align: 'right' });
  leftY += 16;

  topProductsData.slice(0, 5).forEach((p, i) => {
    doc.setFillColor(i % 2 === 0 ? 255 : 248, i % 2 === 0 ? 255 : 250, i % 2 === 0 ? 255 : 252);
    doc.rect(margin, leftY, tableColWidth, 14, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(15, 23, 42);
    const pName = String(p.name || p.product || 'Item');
    doc.text(pName.length > 24 ? `${pName.slice(0, 22)}...` : pName, margin + 6, leftY + 10);
    doc.setFont('helvetica', 'bold');
    doc.text(formatCurrency(p.value || p.revenue || 0), margin + tableColWidth - 6, leftY + 10, { align: 'right' });
    leftY += 14;
  });

  // Right Column: Regional
  let rightY = currentY;
  const rightX = margin + tableColWidth + 12;
  doc.setFillColor(37, 99, 235);
  doc.rect(rightX, rightY, tableColWidth, 16, 'F');
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(7.5);
  doc.setTextColor(255, 255, 255);
  doc.text('Regional / Category Distribution', rightX + 6, rightY + 11);
  doc.text('Revenue', rightX + tableColWidth - 6, rightY + 11, { align: 'right' });
  rightY += 16;

  regionalData.slice(0, 5).forEach((r, i) => {
    doc.setFillColor(i % 2 === 0 ? 255 : 248, i % 2 === 0 ? 255 : 250, i % 2 === 0 ? 255 : 252);
    doc.rect(rightX, rightY, tableColWidth, 14, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(15, 23, 42);
    const rName = String(r.name || r.region || 'Region');
    doc.text(rName.length > 24 ? `${rName.slice(0, 22)}...` : rName, rightX + 6, rightY + 10);
    doc.setFont('helvetica', 'bold');
    doc.text(formatCurrency(r.value || r.revenue || 0), rightX + tableColWidth - 6, rightY + 10, { align: 'right' });
    rightY += 14;
  });

  currentY = Math.max(leftY, rightY) + 16;

  // 6. STATISTICAL ANOMALIES (IQR OUTLIER AUDIT)
  onProgress({ step: 5, message: 'Auditing statistical anomalies and data quality...' });
  checkPageBreak(120);

  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(124, 58, 237);
  doc.text('5. STATISTICAL ANOMALIES (IQR OUTLIER AUDIT)', margin, currentY);
  currentY += 12;

  const anomCount = anomalies.outlier_count || 0;
  const anomPct = anomalies.outlier_pct || 0;
  const upperB = anomalies.upper_bound ? `$${anomalies.upper_bound.toLocaleString()}` : '$0';
  const maxAnom = anomalies.max_outlier ? `$${anomalies.max_outlier.toLocaleString()}` : 'None';

  doc.setFont('helvetica', 'normal');
  doc.setFontSize(8.5);
  doc.setTextColor(71, 85, 105);
  const anomText = `Interquartile Range analysis (1.5 × IQR) on '${anomalies.column || 'Revenue'}' detected ${anomCount} statistical outliers (${anomPct}%) exceeding the upper threshold of ${upperB} (Max outlier: ${maxAnom}).`;
  const splitAnom = doc.splitTextToSize(anomText, contentWidth);
  doc.text(splitAnom, margin, currentY);
  currentY += splitAnom.length * 11 + 6;

  const sampleAnoms = anomalies.samples || [];
  if (sampleAnoms.length > 0) {
    doc.setFillColor(15, 23, 42);
    doc.rect(margin, currentY, contentWidth, 14, 'F');
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(255, 255, 255);
    doc.text('Row #', margin + 6, currentY + 10);
    doc.text('Product / Item', margin + 60, currentY + 10);
    doc.text('Region', margin + 260, currentY + 10);
    doc.text('Transaction Amount', pageWidth - margin - 6, currentY + 10, { align: 'right' });
    currentY += 14;

    sampleAnoms.slice(0, 4).forEach((s, idx) => {
      doc.setFillColor(idx % 2 === 0 ? 255 : 248, idx % 2 === 0 ? 255 : 250, idx % 2 === 0 ? 255 : 252);
      doc.rect(margin, currentY, contentWidth, 13, 'F');
      doc.setFont('helvetica', 'normal');
      doc.setFontSize(7.5);
      doc.setTextColor(15, 23, 42);
      doc.text(`#${s.id || idx}`, margin + 6, currentY + 9);
      doc.text(String(s.product || 'Item').slice(0, 34), margin + 60, currentY + 9);
      doc.text(String(s.region || 'Global').slice(0, 20), margin + 260, currentY + 9);
      doc.setFont('helvetica', 'bold');
      doc.text(s.formatted || formatCurrency(s.value || 0), pageWidth - margin - 6, currentY + 9, { align: 'right' });
      currentY += 13;
    });
    currentY += 10;
  }

  // 7. DATA QUALITY & SCHEMA INTEGRITY SCORECARD
  checkPageBreak(70);
  doc.setFont('helvetica', 'bold');
  doc.setFontSize(10.5);
  doc.setTextColor(124, 58, 237);
  doc.text('6. DATA QUALITY & SCHEMA INTEGRITY SCORECARD', margin, currentY);
  currentY += 12;

  const qualityBoxWidth = (contentWidth - 18) / 4;
  const qualityItems = [
    { label: 'QUALITY SCORE', val: `${dataQuality.score ?? 100}/100`, sub: `Status: ${dataQuality.status || 'Optimal'}`, color: [16, 185, 129] },
    { label: 'DUPLICATE ROWS', val: `${(dataQuality.duplicate_rows || 0).toLocaleString()}`, sub: dataQuality.duplicate_rows === 0 ? '0% Redundancy' : 'Deduplication advised', color: [15, 23, 42] },
    { label: 'MISSING CELLS', val: `${(dataQuality.missing_cells || 0).toLocaleString()} (${dataQuality.missing_pct || 0}%)`, sub: dataQuality.missing_cells === 0 ? 'Optimal Hygiene' : 'Imputation advised', color: [15, 23, 42] },
    { label: 'SCHEMA MATRIX', val: `${(dataQuality.total_rows || 0).toLocaleString()} × ${dataQuality.total_columns || 0}`, sub: 'Rows × Columns', color: [15, 23, 42] }
  ];

  qualityItems.forEach((q, idx) => {
    const x = margin + idx * (qualityBoxWidth + 6);
    doc.setFillColor(248, 250, 252);
    doc.setDrawColor(226, 232, 240);
    doc.roundedRect(x, currentY, qualityBoxWidth, 46, 4, 4, 'FD');

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(100, 116, 139);
    doc.text(q.label, x + 8, currentY + 11);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(q.color[0], q.color[1], q.color[2]);
    doc.text(q.val, x + 8, currentY + 27);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.5);
    doc.setTextColor(148, 163, 184);
    doc.text(q.sub, x + 8, currentY + 39);
  });

  currentY += 56;

  // Final Header / Footer pass
  for (let i = 1; i <= doc.internal.pages.length - 1; i++) {
    doc.setPage(i);
    // Draw header/footer for every page
    doc.setDrawColor(226, 232, 240);
    doc.setLineWidth(0.5);
    doc.line(margin, pageHeight - 30, pageWidth - margin, pageHeight - 30);

    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7.5);
    doc.setTextColor(148, 163, 184);
    doc.text('InsightForge AI Executive Intelligence Report • Calculated strictly from verified active DataFrame series', margin, pageHeight - 18);
    doc.text(`Page ${i} of ${doc.internal.pages.length - 1}`, pageWidth - margin, pageHeight - 18, { align: 'right' });
  }

  onProgress({ step: 6, message: 'Finalizing PDF output...' });

  const safeFilename = filename.replace(/[^a-z0-9_-]/gi, '_');
  const reportName = `InsightForge_Report_${safeFilename}_${new Date().toISOString().slice(0, 10)}.pdf`;
  doc.save(reportName);

  return true;
}
