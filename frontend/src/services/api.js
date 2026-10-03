/**
 * API Service for Agentic SOV Cleansing & Intelligence System
 * Supports environment variables, custom URL override via localStorage,
 * and smart detection of private cloud hostnames.
 */

export function getCustomBackendUrl() {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('sov_backend_url') || '';
  }
  return '';
}

export function setCustomBackendUrl(url) {
  if (typeof window !== 'undefined') {
    if (!url || !url.trim()) {
      localStorage.removeItem('sov_backend_url');
    } else {
      let clean = url.trim().replace(/\/$/, '');
      if (!clean.startsWith('http://') && !clean.startsWith('https://')) {
        clean = `https://${clean}`;
      }
      localStorage.setItem('sov_backend_url', clean);
    }
  }
}

export function getApiBase() {
  // 1. Check user-configured override in localStorage
  const custom = getCustomBackendUrl();
  if (custom) return custom;

  // 2. Check build-time VITE_API_URL
  const rawApiUrl = (import.meta.env.VITE_API_URL || '').trim().replace(/\/$/, '');
  if (!rawApiUrl) return '';

  // Check if rawApiUrl is a Render private network host (e.g. "sov-cleansing-backend")
  // Public domains must contain a dot (e.g. .onrender.com) or localhost/127.0.0.1
  const hostOnly = rawApiUrl.replace(/^https?:\/\//, '').split(':')[0];
  if (!hostOnly.includes('.') && hostOnly !== 'localhost' && hostOnly !== '127.0.0.1') {
    // This is an internal private hostname inaccessible to client browsers
    return '';
  }

  return rawApiUrl.startsWith('http://') || rawApiUrl.startsWith('https://')
    ? rawApiUrl
    : `https://${rawApiUrl}`;
}

export function getBaseUrl() {
  const base = getApiBase();
  return base ? `${base}/api` : '/api';
}

export const API_BASE = getApiBase();

/**
 * Health check to verify if the backend is reachable
 */
export async function checkBackendHealth(targetBaseUrl) {
  const base = targetBaseUrl !== undefined ? targetBaseUrl.replace(/\/$/, '') : getApiBase();
  const url = base ? `${base}/health` : '/health';
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(6000) });
    if (!res.ok) return { online: false, status: res.status };
    const data = await res.json();
    return { online: true, data };
  } catch (err) {
    return { online: false, error: err.message };
  }
}

async function request(endpoint, options = {}) {
  const baseUrl = getBaseUrl();
  const fullUrl = `${baseUrl}${endpoint}`;

  try {
    const res = await fetch(fullUrl, options);
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({ detail: `Request failed with status ${res.status}` }));
      throw new Error(errorData.detail || `Server returned error ${res.status}`);
    }
    return await res.json();
  } catch (err) {
    if (err.message && (err.message.includes('Failed to fetch') || err.name === 'TypeError')) {
      const targetHint = baseUrl.startsWith('http') ? baseUrl : `${window.location.origin}${baseUrl}`;
      throw new Error(
        `Unable to reach backend at "${targetHint}".\n` +
        `If the backend is waking up on Render (free tier spins down after idle), please wait ~30 seconds and try again, or verify your Backend API URL.`
      );
    }
    throw err;
  }
}

export async function uploadSOVFile(file) {
  const formData = new FormData();
  formData.append('file', file);
  return request('/upload', {
    method: 'POST',
    body: formData,
  });
}

export async function loadSampleSOV(sampleFilename) {
  return request(`/samples/load/${sampleFilename}`, {
    method: 'POST',
  });
}

export async function fetchSampleList() {
  return request('/samples');
}

export async function overrideSheetSelection(sessionId, sheetName, headerRow) {
  return request(`/session/${sessionId}/select-sheet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sheet_name: sheetName, header_row: headerRow }),
  });
}

export async function updateMappingOverrides(sessionId, mappings) {
  return request(`/session/${sessionId}/mapping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mappings }),
  });
}

export async function submitReReasoning(sessionId, recId, feedback) {
  return request(`/session/${sessionId}/re-reason`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rec_id: recId, feedback }),
  });
}

export async function executeTransformation(
  sessionId,
  decisions,
  mappingOverrides,
  approvedBy = "Human Reviewer (Underwriting Ops)"
) {
  return request(`/session/${sessionId}/transform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recommendation_decisions: decisions,
      column_mapping_overrides: mappingOverrides,
      approved_by: approvedBy,
    }),
  });
}
