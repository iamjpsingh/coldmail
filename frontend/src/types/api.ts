// Common API response types

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface APIError {
  detail?: string;
  message?: string;
  errors?: Record<string, string[]>;
}

export interface SuccessResponse {
  status: string;
  message?: string;
}
