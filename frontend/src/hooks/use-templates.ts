import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  signaturesApi,
  templatesApi,
  foldersApi,
  snippetsApi,
} from '@/api/templates';
import type {
  EmailSignatureCreate,
  EmailTemplateCreate,
  TemplateFolderCreate,
  SnippetCreate,
  TemplatePreviewRequest,
  TemplateValidationRequest,
} from '@/types/template';

// Query keys
export const signatureKeys = {
  all: ['signatures'] as const,
  lists: () => [...signatureKeys.all, 'list'] as const,
  detail: (id: string) => [...signatureKeys.all, 'detail', id] as const,
};

export const templateKeys = {
  all: ['templates'] as const,
  lists: () => [...templateKeys.all, 'list'] as const,
  list: (filters: { category?: string; folder?: string; search?: string }) =>
    [...templateKeys.lists(), filters] as const,
  details: () => [...templateKeys.all, 'detail'] as const,
  detail: (id: string) => [...templateKeys.details(), id] as const,
  versions: (id: string) => [...templateKeys.detail(id), 'versions'] as const,
  variables: () => [...templateKeys.all, 'variables'] as const,
};

export const folderKeys = {
  all: ['folders'] as const,
  lists: () => [...folderKeys.all, 'list'] as const,
  list: (parent?: string) => [...folderKeys.lists(), parent] as const,
  detail: (id: string) => [...folderKeys.all, 'detail', id] as const,
  templates: (id: string) => [...folderKeys.detail(id), 'templates'] as const,
};

export const snippetKeys = {
  all: ['snippets'] as const,
  lists: () => [...snippetKeys.all, 'list'] as const,
  list: (filters: { category?: string; search?: string }) =>
    [...snippetKeys.lists(), filters] as const,
  detail: (id: string) => [...snippetKeys.all, 'detail', id] as const,
  categories: () => [...snippetKeys.all, 'categories'] as const,
};

// Signature hooks
export function useSignatures() {
  return useQuery({
    queryKey: signatureKeys.lists(),
    queryFn: () => signaturesApi.list(),
  });
}

export function useSignature(id: string) {
  return useQuery({
    queryKey: signatureKeys.detail(id),
    queryFn: () => signaturesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateSignature() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmailSignatureCreate) => signaturesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: signatureKeys.lists() });
    },
  });
}

export function useUpdateSignature() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EmailSignatureCreate> }) =>
      signaturesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: signatureKeys.lists() });
      queryClient.invalidateQueries({ queryKey: signatureKeys.detail(id) });
    },
  });
}

export function useDeleteSignature() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => signaturesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: signatureKeys.lists() });
    },
  });
}

export function useSetDefaultSignature() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => signaturesApi.setDefault(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: signatureKeys.lists() });
    },
  });
}

// Template hooks
export function useTemplates(filters?: { category?: string; folder?: string; search?: string }) {
  return useQuery({
    queryKey: templateKeys.list(filters || {}),
    queryFn: () => templatesApi.list(filters),
  });
}

export function useTemplate(id: string) {
  return useQuery({
    queryKey: templateKeys.detail(id),
    queryFn: () => templatesApi.get(id),
    enabled: !!id,
  });
}

export function useCreateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: EmailTemplateCreate) => templatesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

export function useUpdateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<EmailTemplateCreate> }) =>
      templatesApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(id) });
    },
  });
}

export function useDeleteTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => templatesApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

export function usePreviewTemplate() {
  return useMutation({
    mutationFn: (data: TemplatePreviewRequest) => templatesApi.preview(data),
  });
}

export function useValidateTemplate() {
  return useMutation({
    mutationFn: (data: TemplateValidationRequest) => templatesApi.validate(data),
  });
}

export function useTemplateVariables() {
  return useQuery({
    queryKey: templateKeys.variables(),
    queryFn: () => templatesApi.getVariables(),
  });
}

export function useDuplicateTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => templatesApi.duplicate(id, name),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

export function useTemplateVersions(id: string) {
  return useQuery({
    queryKey: templateKeys.versions(id),
    queryFn: () => templatesApi.getVersions(id),
    enabled: !!id,
  });
}

export function useSaveTemplateVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, changeNotes }: { id: string; changeNotes?: string }) =>
      templatesApi.saveVersion(id, changeNotes),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.versions(id) });
    },
  });
}

export function useRestoreTemplateVersion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, versionId }: { id: string; versionId: string }) =>
      templatesApi.restoreVersion(id, versionId),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: templateKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

// Folder hooks
export function useFolders(parent?: string | 'root') {
  return useQuery({
    queryKey: folderKeys.list(parent),
    queryFn: () => foldersApi.list(parent),
  });
}

export function useFolder(id: string) {
  return useQuery({
    queryKey: folderKeys.detail(id),
    queryFn: () => foldersApi.get(id),
    enabled: !!id,
  });
}

export function useCreateFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: TemplateFolderCreate) => foldersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: folderKeys.lists() });
    },
  });
}

export function useUpdateFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<TemplateFolderCreate> }) =>
      foldersApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: folderKeys.lists() });
      queryClient.invalidateQueries({ queryKey: folderKeys.detail(id) });
    },
  });
}

export function useDeleteFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => foldersApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: folderKeys.lists() });
    },
  });
}

export function useFolderTemplates(id: string) {
  return useQuery({
    queryKey: folderKeys.templates(id),
    queryFn: () => foldersApi.getTemplates(id),
    enabled: !!id,
  });
}

export function useAddTemplatesToFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, templateIds }: { id: string; templateIds: string[] }) =>
      foldersApi.addTemplates(id, templateIds),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: folderKeys.templates(id) });
      queryClient.invalidateQueries({ queryKey: folderKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

export function useRemoveTemplatesFromFolder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, templateIds }: { id: string; templateIds: string[] }) =>
      foldersApi.removeTemplates(id, templateIds),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: folderKeys.templates(id) });
      queryClient.invalidateQueries({ queryKey: folderKeys.detail(id) });
      queryClient.invalidateQueries({ queryKey: templateKeys.lists() });
    },
  });
}

// Snippet hooks
export function useSnippets(filters?: { category?: string; search?: string }) {
  return useQuery({
    queryKey: snippetKeys.list(filters || {}),
    queryFn: () => snippetsApi.list(filters),
  });
}

export function useSnippet(id: string) {
  return useQuery({
    queryKey: snippetKeys.detail(id),
    queryFn: () => snippetsApi.get(id),
    enabled: !!id,
  });
}

export function useCreateSnippet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SnippetCreate) => snippetsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: snippetKeys.lists() });
    },
  });
}

export function useUpdateSnippet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<SnippetCreate> }) =>
      snippetsApi.update(id, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: snippetKeys.lists() });
      queryClient.invalidateQueries({ queryKey: snippetKeys.detail(id) });
    },
  });
}

export function useDeleteSnippet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => snippetsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: snippetKeys.lists() });
    },
  });
}

export function useSnippetCategories() {
  return useQuery({
    queryKey: snippetKeys.categories(),
    queryFn: () => snippetsApi.getCategories(),
  });
}

export function useUseSnippet() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => snippetsApi.use(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: snippetKeys.lists() });
    },
  });
}
