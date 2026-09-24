import { AuditResult, CreateAuditRequest, AuditComparison, DeveloperFixPrompt, IssueAnalysisResponse, RetestAuditResponse } from '../types/audit';

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const API_BASE_URL = RAW_BASE.endsWith('/api/v1') ? RAW_BASE : `${RAW_BASE}/api/v1`;
const SERVER_ROOT = RAW_BASE.replace(/\/api\/v1$/, '');

export async function checkBackendHealth(): Promise<{ status: string; service: string; version: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new Error(`Health check failed with status ${response.status}`);
    }
    return await response.json();
  } catch (err: any) {
    throw new Error(err.message || 'Backend service is unavailable.');
  }
}

export async function createAudit(request: CreateAuditRequest): Promise<AuditResult> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/audits`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: request.url,
        viewports: request.viewports || ['desktop', 'mobile'],
        baseline_audit_id: request.baseline_audit_id,
      }),
    });
  } catch (netErr: any) {
    throw new Error(
      `Cannot connect to backend API at ${API_BASE_URL}. Ensure FastAPI backend is running.`
    );
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Audit request failed (${response.status})` }));
    const errorMsg = errorData.detail || errorData.error_message || `Audit request failed with status ${response.status}`;
    throw new Error(errorMsg);
  }

  return response.json();
}

export async function getAudit(auditId: string): Promise<AuditResult> {
  const response = await fetch(`${API_BASE_URL}/audits/${auditId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch audit ${auditId} (${response.status})`);
  }
  return response.json();
}

export async function retestAudit(auditId: string): Promise<RetestAuditResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/audits/${auditId}/retest`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (netErr: any) {
    throw new Error(`Cannot connect to backend API at ${API_BASE_URL}. Ensure FastAPI backend is running.`);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Retest failed (${response.status})` }));
    const errorMsg = typeof errorData.detail === 'string' ? errorData.detail : (errorData.detail?.message || errorData.error_message || `Retest failed with status ${response.status}`);
    throw new Error(errorMsg);
  }

  return response.json();
}

export async function compareAudits(baselineAuditId: string, newAuditId: string): Promise<AuditComparison> {
  const response = await fetch(`${API_BASE_URL}/audits/compare`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      baseline_audit_id: baselineAuditId,
      new_audit_id: newAuditId,
    }),
  });

  if (!response.ok) {
    throw new Error(`Failed to compare audits (${response.status})`);
  }

  return response.json();
}

export async function getFixPrompt(auditId: string): Promise<DeveloperFixPrompt> {
  const response = await fetch(`${API_BASE_URL}/audits/${auditId}/fix-prompt`);
  if (!response.ok) {
    throw new Error(`Failed to fetch fix prompt for audit ${auditId}`);
  }
  return response.json();
}

export async function analyzeIssue(auditId: string, issueId: string): Promise<IssueAnalysisResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/audits/${auditId}/issues/${issueId}/analyze`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
    });
  } catch (netErr: any) {
    throw new Error('Could not connect to the AI analysis service.');
  }

  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.json();
    } catch {
      // ignore json parse error
    }

    const detail = errorData?.detail;
    const errorCode = typeof detail === 'object' && detail !== null ? detail.error : (errorData?.error || null);

    if (response.status === 503) {
      if (errorCode === 'AI_NOT_CONFIGURED') {
        throw new Error('AI analysis is not configured. Add LLM_API_KEY to the backend environment.');
      } else if (errorCode === 'AI_PROVIDER_ERROR') {
        throw new Error('AI analysis is temporarily unavailable. Please try again.');
      } else {
        const msg = typeof detail === 'string' ? detail : (detail?.message || errorData?.message || 'AI analysis service unavailable.');
        throw new Error(msg);
      }
    }

    if (response.status === 404) {
      const msg = typeof detail === 'string' ? detail : (detail?.message || `Audit '${auditId}' or issue '${issueId}' could not be found.`);
      throw new Error(msg);
    }

    const msg = typeof detail === 'string' ? detail : (detail?.message || errorData?.error_message || `AI analysis failed (${response.status})`);
    throw new Error(msg);
  }

  return response.json();
}

export function getArtifactUrl(auditId: string, artifactPathOrId?: string): string {
  if (!artifactPathOrId) return '';
  if (artifactPathOrId.startsWith('http://') || artifactPathOrId.startsWith('https://')) {
    return artifactPathOrId;
  }
  if (artifactPathOrId.startsWith('/')) {
    return `${SERVER_ROOT}${artifactPathOrId}`;
  }
  return `${API_BASE_URL}/audits/${auditId}/artifacts/${artifactPathOrId}`;
}


