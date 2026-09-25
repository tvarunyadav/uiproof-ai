import {
  AuditResult,
  CreateAuditRequest,
  AuditComparison,
  DeveloperFixPrompt,
  IssueAnalysisResponse,
  RetestAuditResponse,
  Project,
  CreateProjectRequest,
  AuditSummaryItem,
} from '../types/audit';

import {
  User,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  LogoutResponse,
} from '../types/auth';

const RAW_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000').replace(/\/+$/, '');
const API_BASE_URL = RAW_BASE.endsWith('/api/v1') ? RAW_BASE : `${RAW_BASE}/api/v1`;
const SERVER_ROOT = RAW_BASE.replace(/\/api\/v1$/, '');

export class ApiError extends Error {
  status: number;
  detail?: any;

  constructor(message: string, status: number, detail?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }
}

export async function fetchWithAuth(endpoint: string, options: RequestInit = {}): Promise<Response> {
  const token = localStorage.getItem('uiproof_token');
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });
  } catch (netErr: any) {
    throw new ApiError('Unable to connect to the UIProof backend.', 0);
  }

  if (response.status === 401) {
    let errorDetail = 'Your session has expired. Please log in again.';
    try {
      const errJson = await response.clone().json();
      if (typeof errJson.detail === 'string') {
        errorDetail = errJson.detail;
      }
    } catch {
      // fallback message
    }
    throw new ApiError(errorDetail, 401);
  }

  return response;
}

export async function checkBackendHealth(): Promise<{ status: string; service: string; version: string }> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    if (!response.ok) {
      throw new ApiError(`Health check failed with status ${response.status}`, response.status);
    }
    return await response.json();
  } catch (err: any) {
    throw new ApiError(err.message || 'Backend service is unavailable.', 0);
  }
}

// Authentication Endpoints
export async function registerUser(request: RegisterRequest): Promise<User> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: request.email.trim().toLowerCase(),
        password: request.password,
      }),
    });
  } catch (netErr: any) {
    throw new ApiError('Unable to connect to the UIProof backend.', 0);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Registration failed.' }));
    if (response.status === 409) {
      throw new ApiError('A user with this email address already exists.', 409);
    }
    const msg = typeof errorData.detail === 'string' ? errorData.detail : 'Registration failed.';
    throw new ApiError(msg, response.status, errorData.detail);
  }

  return response.json();
}

export async function loginUser(request: LoginRequest): Promise<TokenResponse> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        email: request.email.trim().toLowerCase(),
        password: request.password,
      }),
    });
  } catch (netErr: any) {
    throw new ApiError('Unable to connect to the UIProof backend.', 0);
  }

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Login failed.' }));
    if (response.status === 401) {
      throw new ApiError('Invalid email or password.', 401);
    }
    const msg = typeof errorData.detail === 'string' ? errorData.detail : 'Authentication failed.';
    throw new ApiError(msg, response.status, errorData.detail);
  }

  return response.json();
}

export async function getMeProfile(): Promise<User> {
  const response = await fetchWithAuth('/auth/me');
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: 'Failed to fetch user profile.' }));
    throw new ApiError(errorData.detail || 'Failed to fetch user profile.', response.status);
  }
  return response.json();
}

export async function logoutUser(): Promise<LogoutResponse> {
  try {
    const response = await fetchWithAuth('/auth/logout', {
      method: 'POST',
    });
    if (response.ok) {
      return await response.json();
    }
  } catch {
    // Ignore network or token expiration failures on logout
  }
  return { message: 'Logged out successfully.' };
}

// Protected Project Endpoints
export async function listProjects(): Promise<Project[]> {
  const response = await fetchWithAuth('/projects');
  if (!response.ok) {
    throw new ApiError(`Failed to fetch projects (${response.status})`, response.status);
  }
  return response.json();
}

export async function createProject(request: CreateProjectRequest): Promise<Project> {
  const response = await fetchWithAuth('/projects', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Failed to create project (${response.status})` }));
    throw new ApiError(errorData.detail || `Failed to create project with status ${response.status}`, response.status);
  }

  return response.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const response = await fetchWithAuth(`/projects/${projectId}`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch project ${projectId} (${response.status})`, response.status);
  }
  return response.json();
}

export async function listProjectAudits(projectId: string): Promise<AuditSummaryItem[]> {
  const response = await fetchWithAuth(`/projects/${projectId}/audits`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch audits for project ${projectId} (${response.status})`, response.status);
  }
  return response.json();
}

// Protected Audit Endpoints
export async function listAudits(): Promise<AuditSummaryItem[]> {
  const response = await fetchWithAuth('/audits');
  if (!response.ok) {
    throw new ApiError(`Failed to fetch global audit history (${response.status})`, response.status);
  }
  return response.json();
}

export async function createAudit(request: CreateAuditRequest): Promise<AuditResult> {
  const response = await fetchWithAuth('/audits', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url: request.url,
      viewports: request.viewports || ['desktop', 'mobile'],
      baseline_audit_id: request.baseline_audit_id,
      project_id: request.project_id,
    }),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Audit request failed (${response.status})` }));
    const errorMsg = errorData.detail || errorData.error_message || `Audit request failed with status ${response.status}`;
    throw new ApiError(errorMsg, response.status);
  }

  return response.json();
}

export async function getAudit(auditId: string): Promise<AuditResult> {
  const response = await fetchWithAuth(`/audits/${auditId}`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch audit ${auditId} (${response.status})`, response.status);
  }
  return response.json();
}

export async function retestAudit(auditId: string): Promise<RetestAuditResponse> {
  const response = await fetchWithAuth(`/audits/${auditId}/retest`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ detail: `Retest failed (${response.status})` }));
    const errorMsg = typeof errorData.detail === 'string' ? errorData.detail : (errorData.detail?.message || errorData.error_message || `Retest failed with status ${response.status}`);
    throw new ApiError(errorMsg, response.status);
  }

  return response.json();
}

export async function compareAudits(baselineAuditId: string, newAuditId: string): Promise<AuditComparison> {
  const response = await fetchWithAuth('/audits/compare', {
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
    throw new ApiError(`Failed to compare audits (${response.status})`, response.status);
  }

  return response.json();
}

export async function getFixPrompt(auditId: string): Promise<DeveloperFixPrompt> {
  const response = await fetchWithAuth(`/audits/${auditId}/fix-prompt`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch fix prompt for audit ${auditId}`, response.status);
  }
  return response.json();
}

export async function analyzeIssue(auditId: string, issueId: string): Promise<IssueAnalysisResponse> {
  const response = await fetchWithAuth(`/audits/${auditId}/issues/${issueId}/analyze`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    let errorData: any = null;
    try {
      errorData = await response.clone().json();
    } catch {
      // ignore json parse error
    }

    const detail = errorData?.detail;
    const errorCode = typeof detail === 'object' && detail !== null ? detail.error : (errorData?.error || null);

    if (response.status === 503) {
      if (errorCode === 'AI_NOT_CONFIGURED') {
        throw new ApiError('AI analysis is not configured. Add LLM_API_KEY to the backend environment.', 503);
      } else if (errorCode === 'AI_PROVIDER_ERROR') {
        throw new ApiError('AI analysis is temporarily unavailable. Please try again.', 503);
      } else {
        const msg = typeof detail === 'string' ? detail : (detail?.message || errorData?.message || 'AI analysis service unavailable.');
        throw new ApiError(msg, 503);
      }
    }

    if (response.status === 404) {
      const msg = typeof detail === 'string' ? detail : (detail?.message || `Audit '${auditId}' or issue '${issueId}' could not be found.`);
      throw new ApiError(msg, 404);
    }

    const msg = typeof detail === 'string' ? detail : (detail?.message || errorData?.error_message || `AI analysis failed (${response.status})`);
    throw new ApiError(msg, response.status);
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
