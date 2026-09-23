export type IssueSeverity = 'critical' | 'high' | 'medium' | 'low' | 'info';

export type IssueCategory =
  | 'layout'
  | 'responsive'
  | 'console_error'
  | 'console'
  | 'network_failure'
  | 'broken_resource'
  | 'seo'
  | 'accessibility'
  | 'performance'
  | 'interaction';

export interface Issue {
  issue_id: string;
  category: IssueCategory;
  severity: IssueSeverity;
  title: string;
  description: string;
  selector?: string;
  viewport?: string;
  evidence_references?: string[];
  root_cause_analysis?: string;
  recommended_fix?: string;
}

export interface BrowserViewport {
  name: string;
  width: number;
  height: number;
  device_scale_factor: number;
}

export interface ConsoleLogEntry {
  timestamp: string;
  level: string;
  text: string;
  location?: string;
}

export interface NetworkFailure {
  timestamp: string;
  url: string;
  method: string;
  status_code?: number;
  error_text: string;
}

export interface ResponsiveMetrics {
  viewport_width: number;
  viewport_height: number;
  document_scroll_width: number;
  document_client_width: number;
  horizontal_overflow: number;
}

export interface PageMetadata {
  initial_url: string;
  final_url: string;
  title: string;
  http_status?: number;
  page_load_success: boolean;
  error_message?: string;
}

export interface ViewportAuditResult {
  viewport: BrowserViewport;
  page: PageMetadata;
  screenshot_artifact_id?: string;
  screenshot_url?: string;
  console_errors: ConsoleLogEntry[];
  console_logs?: ConsoleLogEntry[];
  network_failures: NetworkFailure[];
  responsive: ResponsiveMetrics;
}

export interface LayoutIssue {
  viewport: BrowserViewport;
  selector: string;
  issue_type: string;
  description: string;
}

export interface AccessibilityIssue {
  rule_id: string;
  impact: string;
  selector: string;
  description: string;
}

export interface BrowserEvidence {
  url: string;
  timestamp: string;
  desktop?: ViewportAuditResult;
  mobile?: ViewportAuditResult;
  viewports_tested: BrowserViewport[];
  screenshot_paths: string[];
  console_errors: ConsoleLogEntry[];
  network_failures: NetworkFailure[];
  layout_issues: LayoutIssue[];
  accessibility_issues: AccessibilityIssue[];
}

export interface AuditSummaryStats {
  total_issues: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  info_count: number;
  console_error_count: number;
  network_failure_count: number;
  layout_issue_count: number;
  accessibility_issue_count: number;
}

export type AuditStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface AuditResult {
  audit_id: string;
  target_url?: string;
  url: string;
  status: AuditStatus;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  desktop?: ViewportAuditResult;
  mobile?: ViewportAuditResult;
  evidence?: BrowserEvidence;
  issues: Issue[];
  findings?: Issue[];
  stats: AuditSummaryStats;
  error_message?: string;
}

export interface CreateAuditRequest {
  url: string;
  viewports?: string[];
  baseline_audit_id?: string;
}

export interface AuditComparison {
  baseline_audit_id: string;
  new_audit_id: string;
  created_at: string;
  fixed_issues: Issue[];
  remaining_issues: Issue[];
  new_issues: Issue[];
  regressions: Issue[];
}

export interface DeveloperFixPrompt {
  audit_id: string;
  target_issues: Issue[];
  fix_prompt: string;
  suggested_files: string[];
}
