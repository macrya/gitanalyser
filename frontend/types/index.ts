export interface User {
  id: number;
  github_id: number;
  username: string;
  email?: string;
  avatar_url?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Repository {
  id: number;
  github_id: number;
  user_id: number;
  name: string;
  full_name: string;
  description?: string;
  url: string;
  default_branch: string;
  language?: string;
  is_private: boolean;
  stars: number;
  forks: number;
  last_analyzed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TechnicalDebtItem {
  id: number;
  file_path: string;
  line_number?: number;
  debt_type: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  title: string;
  description?: string;
  code_snippet?: string;
  complexity_score?: number;
  estimated_effort_hours?: number;
}

export interface CodeSuggestion {
  id: number;
  file_path: string;
  line_start?: number;
  line_end?: number;
  suggestion_type: string;
  title: string;
  description?: string;
  original_code?: string;
  suggested_code?: string;
  priority: number;
  confidence: number;
  impact?: string;
  applied: boolean;
}

export interface Analysis {
  id: number;
  repository_id: number;
  commit_sha: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  total_lines: number;
  total_files: number;
  average_complexity: number;
  maintainability_index: number;
  code_coverage: number;
  technical_debt_ratio: number;
  total_debt_items: number;
  critical_issues: number;
  high_issues: number;
  medium_issues: number;
  low_issues: number;
  metrics: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

export interface AnalysisDetail extends Analysis {
  debt_items: TechnicalDebtItem[];
  suggestions: CodeSuggestion[];
}

export interface PullRequest {
  id: number;
  repository_id: number;
  analysis_id?: number;
  github_pr_number?: number;
  github_pr_url?: string;
  title: string;
  description?: string;
  branch_name: string;
  status: string;
  files_changed: number;
  suggestions_applied: number;
  created_at: string;
  merged_at?: string;
  closed_at?: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
}
