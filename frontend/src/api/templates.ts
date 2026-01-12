import { apiClient } from '@/lib/api-client';
import type {
  EmailSignature,
  EmailSignatureCreate,
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplateListItem,
  TemplateFolder,
  TemplateFolderCreate,
  TemplateVersion,
  Snippet,
  SnippetCreate,
  TemplatePreviewRequest,
  TemplatePreviewResponse,
  TemplateValidationRequest,
  TemplateValidationResponse,
  TemplateVariables,
} from '@/types/template';

const BASE_PATH = '/campaigns';

// Signatures API
export const signaturesApi = {
  list: async (): Promise<EmailSignature[]> => {
    const response = await apiClient.get<EmailSignature[]>(`${BASE_PATH}/signatures/`);
    return response.data;
  },

  get: async (id: string): Promise<EmailSignature> => {
    const response = await apiClient.get<EmailSignature>(`${BASE_PATH}/signatures/${id}/`);
    return response.data;
  },

  create: async (data: EmailSignatureCreate): Promise<EmailSignature> => {
    const response = await apiClient.post<EmailSignature>(`${BASE_PATH}/signatures/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<EmailSignatureCreate>): Promise<EmailSignature> => {
    const response = await apiClient.patch<EmailSignature>(`${BASE_PATH}/signatures/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/signatures/${id}/`);
  },

  setDefault: async (id: string): Promise<EmailSignature> => {
    const response = await apiClient.post<EmailSignature>(`${BASE_PATH}/signatures/${id}/set_default/`);
    return response.data;
  },
};

// Templates API
export const templatesApi = {
  list: async (params?: {
    category?: string;
    folder?: string;
    search?: string;
  }): Promise<EmailTemplateListItem[]> => {
    const response = await apiClient.get<EmailTemplateListItem[]>(`${BASE_PATH}/templates/`, { params });
    return response.data;
  },

  get: async (id: string): Promise<EmailTemplate> => {
    const response = await apiClient.get<EmailTemplate>(`${BASE_PATH}/templates/${id}/`);
    return response.data;
  },

  create: async (data: EmailTemplateCreate): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(`${BASE_PATH}/templates/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<EmailTemplateCreate>): Promise<EmailTemplate> => {
    const response = await apiClient.patch<EmailTemplate>(`${BASE_PATH}/templates/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/templates/${id}/`);
  },

  preview: async (data: TemplatePreviewRequest): Promise<TemplatePreviewResponse> => {
    const response = await apiClient.post<TemplatePreviewResponse>(`${BASE_PATH}/templates/preview/`, data);
    return response.data;
  },

  validate: async (data: TemplateValidationRequest): Promise<TemplateValidationResponse> => {
    const response = await apiClient.post<TemplateValidationResponse>(`${BASE_PATH}/templates/validate/`, data);
    return response.data;
  },

  getVariables: async (): Promise<TemplateVariables> => {
    const response = await apiClient.get<TemplateVariables>(`${BASE_PATH}/templates/variables/`);
    return response.data;
  },

  duplicate: async (id: string, name: string): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(`${BASE_PATH}/templates/${id}/duplicate/`, { name });
    return response.data;
  },

  getVersions: async (id: string): Promise<TemplateVersion[]> => {
    const response = await apiClient.get<TemplateVersion[]>(`${BASE_PATH}/templates/${id}/versions/`);
    return response.data;
  },

  saveVersion: async (id: string, changeNotes?: string): Promise<TemplateVersion> => {
    const response = await apiClient.post<TemplateVersion>(`${BASE_PATH}/templates/${id}/save_version/`, {
      change_notes: changeNotes,
    });
    return response.data;
  },

  restoreVersion: async (id: string, versionId: string): Promise<EmailTemplate> => {
    const response = await apiClient.post<EmailTemplate>(`${BASE_PATH}/templates/${id}/restore_version/`, {
      version_id: versionId,
    });
    return response.data;
  },
};

// Folders API
export const foldersApi = {
  list: async (parent?: string | 'root'): Promise<TemplateFolder[]> => {
    const response = await apiClient.get<TemplateFolder[]>(`${BASE_PATH}/folders/`, {
      params: parent ? { parent } : undefined,
    });
    return response.data;
  },

  get: async (id: string): Promise<TemplateFolder> => {
    const response = await apiClient.get<TemplateFolder>(`${BASE_PATH}/folders/${id}/`);
    return response.data;
  },

  create: async (data: TemplateFolderCreate): Promise<TemplateFolder> => {
    const response = await apiClient.post<TemplateFolder>(`${BASE_PATH}/folders/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<TemplateFolderCreate>): Promise<TemplateFolder> => {
    const response = await apiClient.patch<TemplateFolder>(`${BASE_PATH}/folders/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/folders/${id}/`);
  },

  getTemplates: async (id: string): Promise<EmailTemplateListItem[]> => {
    const response = await apiClient.get<EmailTemplateListItem[]>(`${BASE_PATH}/folders/${id}/templates/`);
    return response.data;
  },

  addTemplates: async (id: string, templateIds: string[]): Promise<{ added_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/folders/${id}/add_templates/`, {
      template_ids: templateIds,
    });
    return response.data;
  },

  removeTemplates: async (id: string, templateIds: string[]): Promise<{ removed_count: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/folders/${id}/remove_templates/`, {
      template_ids: templateIds,
    });
    return response.data;
  },
};

// Snippets API
export const snippetsApi = {
  list: async (params?: { category?: string; search?: string }): Promise<Snippet[]> => {
    const response = await apiClient.get<Snippet[]>(`${BASE_PATH}/snippets/`, { params });
    return response.data;
  },

  get: async (id: string): Promise<Snippet> => {
    const response = await apiClient.get<Snippet>(`${BASE_PATH}/snippets/${id}/`);
    return response.data;
  },

  create: async (data: SnippetCreate): Promise<Snippet> => {
    const response = await apiClient.post<Snippet>(`${BASE_PATH}/snippets/`, data);
    return response.data;
  },

  update: async (id: string, data: Partial<SnippetCreate>): Promise<Snippet> => {
    const response = await apiClient.patch<Snippet>(`${BASE_PATH}/snippets/${id}/`, data);
    return response.data;
  },

  delete: async (id: string): Promise<void> => {
    await apiClient.delete(`${BASE_PATH}/snippets/${id}/`);
  },

  getCategories: async (): Promise<string[]> => {
    const response = await apiClient.get<string[]>(`${BASE_PATH}/snippets/categories/`);
    return response.data;
  },

  use: async (id: string): Promise<{ times_used: number }> => {
    const response = await apiClient.post(`${BASE_PATH}/snippets/${id}/use/`);
    return response.data;
  },
};
