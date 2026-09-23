import { AuditResult, CreateAuditRequest, AuditComparison, DeveloperFixPrompt } from '../types/audit';

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
