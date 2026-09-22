import { AuditResult, CreateAuditRequest, AuditComparison, DeveloperFixPrompt } from '../types/audit';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1';

export async function checkBackendHealth(): Promise<{ status: string; service: string; version: string }> {
  const response = await fetch(`${API_BASE_URL}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }
  return response.json();
}

export async function createAudit(request: CreateAuditRequest): Promise<AuditResult> {
  const response = await fetch(`${API_BASE_URL}/audits`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to trigger audit' }));
    throw new Error(errorData.detail || `Audit request failed (${response.status})`);
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
