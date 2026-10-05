import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileSpreadsheet,
  Check,
  X,
  Sparkles,
  ArrowRight,
  ArrowUpRight,
  AlertTriangle,
  Loader2,
  RefreshCw
} from 'lucide-react';

/**
 * DatasetUploader Component
 * Fully functional upload component with:
 * - Drag & drop and file picker support (.csv, .xlsx, .xls, max 25MB)
 * - FastAPI /api/upload integration
 * - Animated RGB atmosphere styling
 * - Smooth transition to success state:
 *     ✓ Dataset uploaded
 *     filename.csv
 *     1,000 rows · 9 columns
 *     Analyze Dataset →
 * - Clean, user-friendly error handling (no raw stack traces)
 */
export default function DatasetUploader({
  onUploadSuccess = () => {},
  onAnalyze = () => {}
}) {
  const [isDragOver, setIsDragOver] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState(null);
  const [uploadedDataset, setUploadedDataset] = useState(null);
  const fileInputRef = useRef(null);

  const MAX_FILE_SIZE = 25 * 1024 * 1024; // 25 MB
  const ALLOWED_EXTENSIONS = ['.csv', '.xlsx', '.xls'];

  const handleDragEnter = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDragOver) setIsDragOver(true);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  };

  const handleFileInputChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFileSelected(e.target.files[0]);
    }
  };

  const validateFile = (file) => {
    const filename = file.name || '';
    const ext = filename.slice(filename.lastIndexOf('.')).toLowerCase();

    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      return 'Unsupported file format. InsightForge supports CSV, XLSX, and XLS datasets.';
    }

    if (file.size === 0) {
      return 'The selected file is empty (0 bytes).';
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'File size exceeds the 25 MB limit. Please select a smaller dataset.';
    }

    return null;
  };

  const handleFileSelected = async (file) => {
    setUploadError(null);

    // Client-side validation
    const clientError = validateFile(file);
    if (clientError) {
      setUploadError(clientError);
      return;
    }

    // Initiate upload to FastAPI backend
    setIsUploading(true);

    try {
      const formData = new FormData();
      formData.append('file', file);

      // Support proxy (/api/upload) with fallback to http://127.0.0.1:8000/api/upload
      let response;
      try {
        response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
      } catch (proxyErr) {
        // Fallback directly to localhost:8000 if proxy routing is unavailable
        response = await fetch('http://127.0.0.1:8000/api/upload', {
          method: 'POST',
          body: formData,
        });
      }

      if (!response.ok) {
        let errorMsg = 'Failed to process dataset on the server.';
        try {
          const errData = await response.json();
          if (errData && errData.error && errData.error.message) {
            errorMsg = errData.error.message;
          } else if (errData && errData.detail) {
            // Clean up message, avoid raw stack traces
            errorMsg = typeof errData.detail === 'string'
              ? errData.detail.split('\n')[0]
              : JSON.stringify(errData.detail);
          }
        } catch (_) {
          if (response.status === 413) {
            errorMsg = 'File size exceeds the maximum limit of 25 MB.';
          } else if (response.status === 422) {
            errorMsg = 'Unable to parse dataset. The file appears to be corrupted or invalid.';
          } else if (response.status === 500) {
            errorMsg = 'Internal analysis engine error. Please try again.';
          }
        }
        throw new Error(errorMsg);
      }

      const result = await response.json();

      // Successful upload
      setUploadedDataset(result);
      onUploadSuccess(result);
    } catch (err) {
      console.error('Dataset upload error:', err);
      let userFriendlyMsg = err.message || 'An unexpected error occurred during upload.';
      if (userFriendlyMsg.includes('Failed to fetch') || userFriendlyMsg.includes('NetworkError')) {
        userFriendlyMsg = 'Cannot connect to analysis backend. Please ensure the API server is running on port 8000.';
      }
      setUploadError(userFriendlyMsg);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    }
  };

  const handleReset = (e) => {
    if (e) e.stopPropagation();
    setUploadedDataset(null);
    setUploadError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleLoadSample = async (e) => {
    if (e) e.stopPropagation();
    setUploadError(null);
    setIsUploading(true);
    try {
      let response;
      try {
        response = await fetch('/api/sample');
      } catch (_) {
        response = await fetch('http://127.0.0.1:8000/api/sample');
      }
      if (!response.ok) {
        throw new Error('Failed to load sample dataset from backend.');
      }
      const result = await response.json();
      setUploadedDataset(result);
      onUploadSuccess(result);
    } catch (err) {
      setUploadError(err.message || 'Error loading sample dataset.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleAnalyzeClick = (e) => {
    if (e) e.stopPropagation();
    if (uploadedDataset) {
      onAnalyze(uploadedDataset);
    }
  };

  return (
    <section className="uploader-container" aria-label="Dataset Uploader">
      {/* Hidden native input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".csv, .xlsx, .xls"
        className="hidden-file-input"
        onChange={handleFileInputChange}
        aria-label="Upload dataset file"
      />

      {/* Clean Error Notification */}
      {uploadError && (
        <div className="upload-error-banner" role="alert">
          <div className="error-icon-box">
            <AlertTriangle size={16} />
          </div>
          <div className="error-text-content">
            <span className="error-title">Upload Failed</span>
            <span className="error-message">{uploadError}</span>
          </div>
          <button
            type="button"
            className="error-dismiss-btn"
            onClick={() => setUploadError(null)}
            aria-label="Dismiss error"
          >
            <X size={15} />
          </button>
        </div>
      )}

      {/* Main Upload Zone */}
      <div
        className={`upload-zone rgb-glow-box ${isDragOver ? 'is-drag-over' : ''} ${uploadedDataset ? 'is-success-state' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={() => !uploadedDataset && !isUploading && fileInputRef.current?.click()}
        role="region"
        aria-label="Drag and drop dataset upload area"
      >
        {/* Subtle AI Visual Indicator with animated RGB aura */}
        <div className="upload-ai-badge">
          <span className="ai-indicator-ring rgb-pulse"></span>
          <span className="ai-indicator-core">
            <Sparkles size={11} className="ai-spark-icon" />
          </span>
          <span className="ai-indicator-text">Neural Dataset Parser</span>
        </div>

        {/* STATE 1: Uploading Loader */}
        {isUploading && (
          <div className="upload-content-loading" aria-live="polite">
            <div className="upload-loader-ring">
              <Loader2 size={32} className="spin-loader" />
            </div>
            <h3 className="upload-primary-text">Parsing dataset with Pandas...</h3>
            <p className="upload-subtext">Validating schema and data matrices</p>
          </div>
        )}

        {/* STATE 2: Success State (Exact required layout) */}
        {!isUploading && uploadedDataset && (
          <div className="upload-content-success">
            {/* Required text: ✓ Dataset uploaded */}
            <div className="success-badge-row">
              <span className="success-check-icon">
                <Check size={14} />
              </span>
              <span className="success-badge-label">Dataset uploaded</span>
            </div>

            {/* Required text: filename.csv */}
            <div className="success-filename-row">
              <FileSpreadsheet size={20} className="success-file-icon" />
              <h3 className="success-filename">{uploadedDataset.filename}</h3>
            </div>

            {/* Required text: 1,000 rows · 9 columns */}
            <p className="success-meta-text">
              {Number(uploadedDataset.rows).toLocaleString()} rows · {Number(uploadedDataset.columns).toLocaleString()} columns
            </p>

            {/* Required button: "Analyze Dataset →" */}
            <div className="success-actions-row">
              <button
                type="button"
                className="analyze-dataset-btn"
                onClick={handleAnalyzeClick}
              >
                <span>Analyze Dataset</span>
                <ArrowRight size={15} className="btn-arrow" />
              </button>

              <button
                type="button"
                className="upload-replace-btn"
                onClick={handleReset}
                title="Upload a different dataset"
              >
                <RefreshCw size={13} />
                <span>Change file</span>
              </button>
            </div>
          </div>
        )}

        {/* STATE 3: Idle Upload Prompt */}
        {!isUploading && !uploadedDataset && (
          <div className="upload-content-idle">
            <div className="upload-icon-frame">
              <UploadCloud size={28} className="upload-icon-main" />
            </div>

            <h3 className="upload-primary-text">Drop your dataset here</h3>
            <p className="upload-subtext">CSV, XLSX or XLS · up to 25 MB</p>

            <div className="upload-buttons-group">
              <button
                type="button"
                className="choose-dataset-btn"
                onClick={(e) => {
                  e.stopPropagation();
                  fileInputRef.current?.click();
                }}
              >
                <span>Choose dataset</span>
                <ArrowUpRight size={14} className="btn-arrow" />
              </button>

              <button
                type="button"
                className="sample-dataset-btn"
                onClick={handleLoadSample}
                title="Quick test with bundled sample_data/sales.csv"
              >
                <Sparkles size={12} className="rgb-sparkle" />
                <span>Try sample sales.csv</span>
              </button>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
