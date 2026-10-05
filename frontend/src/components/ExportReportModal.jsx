import React, { useState } from 'react';
import {
  FileText,
  Download,
  FileSpreadsheet,
  Layers,
  Sparkles,
  CheckCircle2,
  AlertCircle,
  X,
  Loader2,
  TrendingUp,
  Award,
  ShieldCheck,
  Zap,
  ArrowRight
} from 'lucide-react';
import {
  generateClientPDFReport,
  downloadDashboardSummary,
  downloadDataAsCSV
} from '../utils/exportUtils';

/**
 * ExportReportModal Component
 * Flagship executive export suite:
 * - AI-Powered PDF Report Generation (with embedded charts, KPIs, AI insights, IQR anomalies)
 * - Dashboard Summary Export (JSON & Executive Briefing)
 * - Granular CSV Export (Products, Regions, Trends, Anomalies)
 * - Real-time generation progress feedback
 */
export default function ExportReportModal({
  isOpen,
  onClose,
  dashboardData,
  filename = 'dataset.csv',
  datasetId,
  chartElements = {}
}) {
  const [selectedFormat, setSelectedFormat] = useState('pdf'); // 'pdf' | 'summary_json' | 'csv_all'
  const [isGenerating, setIsGenerating] = useState(false);
  const [progressStatus, setProgressStatus] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  if (!isOpen) return null;

  const handleExportPDF = async () => {
    setIsGenerating(true);
    setProgressStatus({ step: 1, message: 'Initiating AI-Powered PDF compilation...' });
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      // Attempt rich client-side PDF generation with embedded Recharts
      await generateClientPDFReport({
        dashboardData,
        filename,
        chartElements,
        onProgress: (prog) => setProgressStatus(prog)
      });

      setSuccessMessage('AI Executive PDF Report downloaded successfully!');
      setTimeout(() => {
        setIsGenerating(false);
        setProgressStatus(null);
      }, 1200);
    } catch (err) {
      console.warn('Client PDF generation error, falling back to server PDF endpoint:', err);
      // Fallback to backend ReportLab endpoint
      try {
        let pdfUrl = `/api/dataset/${datasetId}/export/pdf`;
        const res = await fetch(pdfUrl);
        if (!res.ok) {
          throw new Error('Server PDF compilation failed.');
        }
        const blob = await res.blob();
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `InsightForge_Report_${filename.replace(/[^a-z0-9_-]/gi, '_')}.pdf`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        setSuccessMessage('Executive PDF Report downloaded successfully!');
      } catch (serverErr) {
        console.error('All PDF generation paths failed:', serverErr);
        setErrorMessage('Failed to generate PDF report. Please try again.');
      } finally {
        setIsGenerating(false);
        setProgressStatus(null);
      }
    }
  };

  const handleExportSummary = () => {
    try {
      downloadDashboardSummary(dashboardData, `InsightForge_Summary_${filename}`);
      setSuccessMessage('Dashboard Executive Summary exported as JSON!');
    } catch (err) {
      setErrorMessage('Failed to export dashboard summary.');
    }
  };

  const handleExportTableCSV = (tableType) => {
    try {
      let dataToExport = [];
      let name = tableType;

      if (tableType === 'top_products') {
        dataToExport = dashboardData?.charts?.top_products?.data || [];
        name = 'top_products';
      } else if (tableType === 'regional') {
        dataToExport = dashboardData?.charts?.regional_performance?.data || [];
        name = 'regional_performance';
      } else if (tableType === 'trend') {
        dataToExport = dashboardData?.charts?.revenue_trend?.data || [];
        name = 'revenue_trend';
      } else if (tableType === 'anomalies') {
        dataToExport = dashboardData?.anomalies?.samples || [];
        name = 'iqr_anomalies';
      }

      if (dataToExport.length === 0) {
        setErrorMessage(`No data available for ${tableType}.`);
        return;
      }

      downloadDataAsCSV(dataToExport, `InsightForge_${filename.replace(/[^a-z0-9_-]/gi, '_')}_${name}.csv`);
      setSuccessMessage(`${name.replace(/_/g, ' ').toUpperCase()} downloaded as CSV!`);
    } catch (err) {
      setErrorMessage('Failed to export CSV table.');
    }
  };

  return (
    <div className="export-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div className="export-modal-card rgb-glow-box" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div className="export-modal-header">
          <div className="export-header-left">
            <div className="export-sparkle-frame">
              <Sparkles size={18} className="rgb-sparkle" />
            </div>
            <div>
              <h3 className="export-modal-title">Export Executive Report & Data</h3>
              <p className="export-modal-subtitle">
                Verified mathematical findings for <strong>{filename}</strong>
              </p>
            </div>
          </div>

          <button
            type="button"
            className="export-close-btn"
            onClick={onClose}
            aria-label="Close export dialog"
          >
            <X size={16} />
          </button>
        </div>

        {/* Modal Body */}
        <div className="export-modal-body">
          {/* Main Option 1: AI-Powered PDF Report */}
          <div
            className={`export-option-card ${selectedFormat === 'pdf' ? 'is-selected' : ''}`}
            onClick={() => setSelectedFormat('pdf')}
          >
            <div className="export-option-radio">
              <span className={`radio-circle ${selectedFormat === 'pdf' ? 'checked' : ''}`}></span>
            </div>
            <div className="export-option-icon-box pdf">
              <FileText size={22} />
            </div>
            <div className="export-option-content">
              <div className="export-option-title-row">
                <h4 className="export-option-title">AI-Powered Executive PDF Report</h4>
                <span className="export-badge-recommended">Recommended</span>
              </div>
              <p className="export-option-desc">
                Comprehensive multi-page publication including executive KPIs, 5 AI discovered findings, high-definition charts, IQR anomaly audit, and data quality scorecard.
              </p>
              <div className="export-pdf-features-pills">
                <span>✓ Dataset Overview</span>
                <span>✓ Key KPIs</span>
                <span>✓ Top Products</span>
                <span>✓ Regional Performance</span>
                <span>✓ Important Trends</span>
                <span>✓ AI Insights</span>
                <span>✓ IQR Anomalies</span>
                <span>✓ Quality Score</span>
                <span>✓ Selected Charts</span>
              </div>
            </div>
          </div>

          {/* Main Option 2: Dashboard Executive Summary (JSON) */}
          <div
            className={`export-option-card ${selectedFormat === 'summary_json' ? 'is-selected' : ''}`}
            onClick={() => setSelectedFormat('summary_json')}
          >
            <div className="export-option-radio">
              <span className={`radio-circle ${selectedFormat === 'summary_json' ? 'checked' : ''}`}></span>
            </div>
            <div className="export-option-icon-box json">
              <Layers size={22} />
            </div>
            <div className="export-option-content">
              <div className="export-option-title-row">
                <h4 className="export-option-title">Executive Dashboard Summary (JSON)</h4>
                <span className="export-badge-format">Structured JSON</span>
              </div>
              <p className="export-option-desc">
                Complete machine-readable JSON payload of all calculated metrics, driver concentrations, and synthesized insights for pipeline automation or enterprise archiving.
              </p>
            </div>
          </div>

          {/* Main Option 3: Granular Table CSVs */}
          <div
            className={`export-option-card ${selectedFormat === 'csv_all' ? 'is-selected' : ''}`}
            onClick={() => setSelectedFormat('csv_all')}
          >
            <div className="export-option-radio">
              <span className={`radio-circle ${selectedFormat === 'csv_all' ? 'checked' : ''}`}></span>
            </div>
            <div className="export-option-icon-box csv">
              <FileSpreadsheet size={22} />
            </div>
            <div className="export-option-content">
              <div className="export-option-title-row">
                <h4 className="export-option-title">Analytical Breakdown Data (CSV Tables)</h4>
                <span className="export-badge-format">RFC 4180 CSV</span>
              </div>
              <p className="export-option-desc">
                Export specific dimensional series directly into CSV format for Microsoft Excel, Google Sheets, or custom SQL processing.
              </p>

              {selectedFormat === 'csv_all' && (
                <div className="csv-quick-links-grid" onClick={(e) => e.stopPropagation()}>
                  <button
                    type="button"
                    className="csv-download-chip"
                    onClick={() => handleExportTableCSV('top_products')}
                  >
                    <Download size={11} />
                    <span>Top Products CSV</span>
                  </button>
                  <button
                    type="button"
                    className="csv-download-chip"
                    onClick={() => handleExportTableCSV('regional')}
                  >
                    <Download size={11} />
                    <span>Regional Performance CSV</span>
                  </button>
                  <button
                    type="button"
                    className="csv-download-chip"
                    onClick={() => handleExportTableCSV('trend')}
                  >
                    <Download size={11} />
                    <span>Temporal Trends CSV</span>
                  </button>
                  <button
                    type="button"
                    className="csv-download-chip"
                    onClick={() => handleExportTableCSV('anomalies')}
                  >
                    <Download size={11} />
                    <span>IQR Outliers CSV</span>
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Feedback States */}
          {isGenerating && progressStatus && (
            <div className="export-progress-banner">
              <Loader2 size={16} className="animate-spin text-purple-400" />
              <span>{progressStatus.message}</span>
            </div>
          )}

          {successMessage && (
            <div className="export-success-banner">
              <CheckCircle2 size={16} className="text-emerald-400" />
              <span>{successMessage}</span>
            </div>
          )}

          {errorMessage && (
            <div className="export-error-banner">
              <AlertCircle size={16} className="text-rose-400" />
              <span>{errorMessage}</span>
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="export-modal-footer">
          <div className="export-footer-disclaimer">
            <ShieldCheck size={13} className="text-emerald-400" />
            <span>Real calculated metrics only · Zero hallucination</span>
          </div>

          <div className="export-footer-actions">
            <button
              type="button"
              className="export-cancel-btn"
              onClick={onClose}
              disabled={isGenerating}
            >
              Close
            </button>

            {selectedFormat === 'pdf' && (
              <button
                type="button"
                className="export-primary-btn rgb-glow-box"
                onClick={handleExportPDF}
                disabled={isGenerating}
                id="modal-generate-pdf-btn"
              >
                {isGenerating ? (
                  <>
                    <Loader2 size={15} className="animate-spin" />
                    <span>Generating PDF...</span>
                  </>
                ) : (
                  <>
                    <FileText size={15} />
                    <span>Generate AI PDF Report</span>
                  </>
                )}
              </button>
            )}

            {selectedFormat === 'summary_json' && (
              <button
                type="button"
                className="export-primary-btn rgb-glow-box"
                onClick={handleExportSummary}
              >
                <Download size={15} />
                <span>Download Summary (JSON)</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
