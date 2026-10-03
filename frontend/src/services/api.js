const BASE_URL = '/api';

export async function uploadSOVFile(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Upload failed' }));
    throw new Error(errorData.detail || 'Failed to upload and process SOV file');
  }

  return res.json();
}

export async function loadSampleSOV(sampleFilename) {
  const res = await fetch(`${BASE_URL}/samples/load/${sampleFilename}`, {
    method: 'POST',
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Failed to load sample' }));
    throw new Error(errorData.detail || 'Failed to load test sample');
  }

  return res.json();
}

export async function fetchSampleList() {
  const res = await fetch(`${BASE_URL}/samples`);
  if (!res.ok) throw new Error('Failed to fetch samples');
  return res.json();
}

export async function overrideSheetSelection(sessionId, sheetName, headerRow) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/select-sheet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sheet_name: sheetName, header_row: headerRow }),
  });

  if (!res.ok) throw new Error('Failed to update sheet selection');
  return res.json();
}

export async function updateMappingOverrides(sessionId, mappings) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/mapping`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ mappings }),
  });

  if (!res.ok) throw new Error('Failed to update column mappings');
  return res.json();
}

export async function submitReReasoning(sessionId, recId, feedback) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/re-reason`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ rec_id: recId, feedback }),
  });

  if (!res.ok) throw new Error('Failed to re-reason recommendation');
  return res.json();
}

export async function executeTransformation(
  sessionId,
  decisions,
  mappingOverrides,
  approvedBy = "Human Reviewer (Underwriting Ops)"
) {
  const res = await fetch(`${BASE_URL}/session/${sessionId}/transform`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      recommendation_decisions: decisions,
      column_mapping_overrides: mappingOverrides,
      approved_by: approvedBy,
    }),
  });

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({ detail: 'Transformation failed' }));
    throw new Error(errorData.detail || 'Failed to execute transformations');
  }

  return res.json();
}
