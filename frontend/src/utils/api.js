/**
 * InsightForge AI - Centralized API Service Configuration
 * 
 * Supports:
 * - VITE_API_URL environment variable for deployed FastAPI backend on Render.
 * - Automatic trimming of trailing slashes and redundant /api prefixes.
 * - Development fallback to local Vite proxy (/api).
 * - Clear, production-ready error formatting for network and backend failures.
 */

// Read VITE_API_URL from environment
const rawEnvUrl = (import.meta.env.VITE_API_URL || '').trim();

// Clean trailing slashes
let normalizedBase = rawEnvUrl.replace(/\/+$/, '');

// If user supplied e.g. "https://api.render.com/api", remove trailing "/api"
// so that endpoints like "/api/upload" do not become "/api/api/upload"
if (normalizedBase.endsWith('/api')) {
  normalizedBase = normalizedBase.slice(0, -4);
}

export const API_BASE_URL = normalizedBase;

/**
 * Returns the fully resolved URL for a given API endpoint.
 * Example:
 *   getApiUrl('/api/sample') -> "https://insightforge-api.onrender.com/api/sample"
 *   (or "/api/sample" if VITE_API_URL is not set)
 */
export function getApiUrl(endpoint) {
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  if (API_BASE_URL) {
    return `${API_BASE_URL}${cleanEndpoint}`;
  }
  return cleanEndpoint;
}

/**
 * Enhanced fetch wrapper with robust error handling for Render / Vercel deployments.
 */
export async function apiFetch(endpoint, options = {}) {
  const targetUrl = getApiUrl(endpoint);

  let response;
  try {
    response = await fetch(targetUrl, options);
  } catch (netErr) {
    console.error(`Backend network failure requesting [${targetUrl}]:`, netErr);

    // Differentiate between missing VITE_API_URL and server wake-up/cold start
    if (!API_BASE_URL && typeof window !== 'undefined' && !['localhost', '127.0.0.1'].includes(window.location.hostname)) {
      throw new Error(
        'Backend connection failed: VITE_API_URL environment variable is missing in Vercel. ' +
        'Please add VITE_API_URL pointing to your deployed Render backend in your Vercel project settings.'
      );
    }

    throw new Error(
      'Cannot connect to analysis backend. If using Render free tier, the instance may be spinning up from sleep ' +
      '(takes ~30-60 seconds). Please verify your connection or retry in a moment.'
    );
  }

  if (!response.ok) {
    let userMsg = `Backend request failed (HTTP ${response.status})`;

    try {
      const contentType = response.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const errorJson = await response.json();
        if (errorJson?.error?.message) {
          userMsg = errorJson.error.message;
        } else if (errorJson?.detail) {
          userMsg = typeof errorJson.detail === 'string'
            ? errorJson.detail.split('\n')[0]
            : JSON.stringify(errorJson.detail);
        } else if (errorJson?.message) {
          userMsg = errorJson.message;
        }
      } else {
        // Non-JSON response (e.g. Vercel 404 HTML, 502 Bad Gateway)
        if (response.status === 404) {
          userMsg = `API route '${endpoint}' not found on server (404). Check backend deployment status and VITE_API_URL.`;
        } else if (response.status === 502 || response.status === 503) {
          userMsg = `Backend server is starting up or temporarily unavailable (${response.status}). Please retry in 30 seconds.`;
        } else if (response.status === 413) {
          userMsg = 'File size exceeds maximum permitted limit (25 MB).';
        }
      }
    } catch (_) {
      // Retain default status message
    }

    const error = new Error(userMsg);
    error.status = response.status;
    throw error;
  }

  return response;
}
