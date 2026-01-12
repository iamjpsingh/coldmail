export type TemplateCategory =
  | 'outreach'
  | 'followup'
  | 'nurture'
  | 'promotional'
  | 'transactional'
  | 'other';

export interface EmailSignature {
  id: string;
  name: string;
  content_html: string;
  content_text: string;
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmailSignatureCreate {
  name: string;
  content_html: string;
  content_text?: string;
  is_default?: boolean;
}

export interface EmailTemplate {
  id: string;
  name: string;
  subject: string;
  content_html: string;
  content_text: string;
  category: TemplateCategory;
  description: string;
  signature: EmailSignature | null;
  signature_id: string | null;
  include_signature: boolean;
  variables: string[];
  has_spintax: boolean;
  times_used: number;
  last_used_at: string | null;
  is_shared: boolean;
  created_by: string | null;
  created_by_name: string;
  folder_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface EmailTemplateCreate {
  name: string;
  subject: string;
  content_html: string;
  content_text?: string;
  category?: TemplateCategory;
  description?: string;
  signature_id?: string | null;
  include_signature?: boolean;
  is_shared?: boolean;
  folder_ids?: string[];
}

export interface EmailTemplateListItem {
  id: string;
  name: string;
  subject: string;
  category: TemplateCategory;
  has_spintax: boolean;
  times_used: number;
  is_shared: boolean;
  created_at: string;
  updated_at: string;
}

export interface TemplateFolder {
  id: string;
  name: string;
  parent: string | null;
  color: string;
  template_count: number;
  children_count: number;
  created_at: string;
  updated_at: string;
}

export interface TemplateFolderCreate {
  name: string;
  parent?: string | null;
  color?: string;
}

export interface TemplateVersion {
  id: string;
  version_number: number;
  subject: string;
  content_html: string;
  content_text: string;
  change_notes: string;
  created_by: string | null;
  created_by_name: string;
  created_at: string;
}

export interface Snippet {
  id: string;
  name: string;
  shortcode: string;
  content_html: string;
  content_text: string;
  description: string;
  category: string;
  times_used: number;
  created_at: string;
  updated_at: string;
}

export interface SnippetCreate {
  name: string;
  shortcode: string;
  content_html: string;
  content_text?: string;
  description?: string;
  category?: string;
}

export interface TemplatePreviewRequest {
  subject: string;
  content_html: string;
  content_text?: string;
  sample_contact?: Record<string, unknown>;
}

export interface TemplatePreviewResponse {
  subject: string;
  content_html: string;
  content_text: string;
  variables_used: string[];
  missing_variables: string[];
  spintax_variations: number;
}

export interface TemplateValidationRequest {
  subject: string;
  content_html: string;
  content_text?: string;
}

export interface TemplateValidationResponse {
  is_valid: boolean;
  variables: string[];
  known_variables: string[];
  custom_variables: string[];
  has_spintax: boolean;
  spintax_count: number;
  spintax_variations: number;
  warnings: string[];
}

export interface TemplateVariables {
  contact: Record<string, string>;
  sender: Record<string, string>;
  campaign: Record<string, string>;
  date: Record<string, string>;
}
