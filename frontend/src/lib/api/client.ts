import {
  User,
  TokenResponse,
  Memory,
  MemoryDetail,
  MemoryListResponse,
  CreateMemoryInput,
  UpdateMemoryInput,
  Tag,
  IngestionJob,
  IngestionJobListResponse,
  SearchRequest,
  SearchResponse,
  SearchHistoryResponse,
  AskRequest,
  AskResponse,
  ConversationItem,
  ConversationDetail,
  SourceAttributionItem,
  GraphResponse,
  GraphEdgeItem,
  CreateEdgeInput,
  ClustersResponse,
  MemoryConnectionsResponse,
  SearchResultItem,
  DashboardStatsResponse,
  TimelineResponse,
  KnowledgeGapsResponse,
  AISettingsResponse,
  PrivacySettingsResponse,
  ApiError
} from '@/types';

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const TOKEN_KEY = 'smritix_token';

export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setStoredToken(token: string | null): void {
  if (typeof window === 'undefined') return;
  if (token) {
    localStorage.setItem(TOKEN_KEY, token);
  } else {
    localStorage.removeItem(TOKEN_KEY);
  }
}

interface FetchOptions extends RequestInit {
  params?: Record<string, string | number | boolean | undefined | null>;
}

export async function apiFetch<T>(path: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers, ...restOptions } = options;

  let url = `${BASE_URL}/api/v1${path}`;

  if (params) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        searchParams.append(key, String(val));
      }
    });
    const qs = searchParams.toString();
    if (qs) {
      url += `?${qs}`;
    }
  }

  const token = getStoredToken();
  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (token) {
    defaultHeaders['Authorization'] = `Bearer ${token}`;
  }

  const response = await fetch(url, {
    credentials: 'include',
    ...restOptions,
    headers: {
      ...defaultHeaders,
      ...headers,
    },
  });

  if (!response.ok) {
    let errorData: ApiError;
    try {
      errorData = await response.json();
    } catch {
      errorData = {
        message: `HTTP error ${response.status}`,
        code: 'NETWORK_ERROR',
      };
    }
    const message = errorData.error?.message || errorData.message || 'Request failed';
    throw new Error(message);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

// Auth API
export const authApi = {
  async register(data: { email: string; password: string; display_name?: string }): Promise<TokenResponse> {
    const res = await apiFetch<TokenResponse>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  async login(data: { email: string; password: string }): Promise<TokenResponse> {
    const res = await apiFetch<TokenResponse>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },

  async logout(): Promise<void> {
    try {
      await apiFetch('/auth/logout', { method: 'POST' });
    } finally {
      setStoredToken(null);
    }
  },

  async getMe(): Promise<User> {
    return apiFetch<User>('/auth/me');
  },

  async refresh(): Promise<TokenResponse> {
    const res = await apiFetch<TokenResponse>('/auth/refresh', { method: 'POST' });
    if (res.access_token) {
      setStoredToken(res.access_token);
    }
    return res;
  },
};

// Memories API
export const memoriesApi = {
  async list(params?: {
    query?: string;
    tag?: string;
    memory_type?: string;
    is_archived?: boolean;
    limit?: number;
    offset?: number;
  }): Promise<MemoryListResponse> {
    return apiFetch<MemoryListResponse>('/memories/', {
      params: params as Record<string, string | number | boolean | undefined>,
    });
  },

  async get(id: string): Promise<MemoryDetail> {
    return apiFetch<MemoryDetail>(`/memories/${id}`);
  },

  async create(data: CreateMemoryInput): Promise<Memory> {
    return apiFetch<Memory>('/memories/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: UpdateMemoryInput): Promise<Memory> {
    return apiFetch<Memory>(`/memories/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async delete(id: string): Promise<void> {
    await apiFetch(`/memories/${id}`, {
      method: 'DELETE',
    });
  },

  async archive(id: string): Promise<Memory> {
    return apiFetch<Memory>(`/memories/${id}/archive`, {
      method: 'POST',
    });
  },

  async restore(id: string): Promise<Memory> {
    return apiFetch<Memory>(`/memories/${id}/restore`, {
      method: 'POST',
    });
  },

  async getConnections(id: string, depth: number = 1): Promise<MemoryConnectionsResponse> {
    const res = await apiFetch<{ data: MemoryConnectionsResponse }>(`/memories/${id}/connections`, {
      params: { depth },
    });
    return res.data;
  },

  async getSimilar(id: string, limit: number = 5): Promise<SearchResultItem[]> {
    const res = await apiFetch<{ data: SearchResultItem[] }>(`/memories/${id}/similar`, {
      params: { limit },
    });
    return res.data;
  },
};

// Tags API
export const tagsApi = {
  async list(): Promise<Tag[]> {
    return apiFetch<Tag[]>('/tags/');
  },

  async create(data: { name: string; color?: string | null }): Promise<Tag> {
    return apiFetch<Tag>('/tags/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async update(id: string, data: { name?: string; color?: string | null }): Promise<Tag> {
    return apiFetch<Tag>(`/tags/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    });
  },

  async delete(id: string): Promise<void> {
    await apiFetch(`/tags/${id}`, {
      method: 'DELETE',
    });
  },
};

// Ingest API
export const ingestApi = {
  async uploadDocument(file: File, tags?: string[]): Promise<IngestionJob> {
    const formData = new FormData();
    formData.append('file', file);
    if (tags && tags.length > 0) {
      formData.append('tags', tags.join(','));
    }

    const token = getStoredToken();
    const headers: Record<string, string> = {};
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${BASE_URL}/api/v1/ingest/document`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
      headers,
    });

    if (!response.ok) {
      let errorMsg = `Upload failed (${response.status})`;
      try {
        const errorData = await response.json();
        errorMsg = errorData.detail || errorData.message || errorMsg;
      } catch {}
      throw new Error(errorMsg);
    }

    return response.json();
  },

  async listJobs(): Promise<IngestionJobListResponse> {
    return apiFetch<IngestionJobListResponse>('/ingest/jobs');
  },

  async getJob(id: string): Promise<IngestionJob> {
    return apiFetch<IngestionJob>(`/ingest/jobs/${id}`);
  },
};

// Search API
export const searchApi = {
  async semanticSearch(data: SearchRequest): Promise<SearchResponse> {
    return apiFetch<SearchResponse>('/search/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async hybridSearch(data: SearchRequest): Promise<SearchResponse> {
    return apiFetch<SearchResponse>('/search/hybrid', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  async getHistory(limit: number = 20): Promise<SearchHistoryResponse> {
    return apiFetch<SearchHistoryResponse>('/search/history', {
      params: { limit },
    });
  },
};

// Ask (RAG) API
export const askApi = {
  async ask(data: AskRequest): Promise<AskResponse> {
    const res = await apiFetch<{ data: AskResponse }>('/ask/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  },

  async getConversations(): Promise<ConversationItem[]> {
    const res = await apiFetch<{ data: ConversationItem[] }>('/ask/conversations');
    return res.data;
  },

  async getConversation(id: string): Promise<ConversationDetail> {
    const res = await apiFetch<{ data: ConversationDetail }>(`/ask/conversations/${id}`);
    return res.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await apiFetch<{ data: { deleted: boolean } }>(`/ask/conversations/${id}`, {
      method: 'DELETE',
    });
  },

  askStream(
    data: AskRequest,
    handlers: {
      onMetadata?: (meta: { conversation_id: string; sources: SourceAttributionItem[] }) => void;
      onToken?: (token: string) => void;
      onDone?: (done: { conversation_id: string; sources?: SourceAttributionItem[] }) => void;
      onError?: (err: Error) => void;
    }
  ): () => void {
    const controller = new AbortController();
    const token = getStoredToken();
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    (async () => {
      try {
        const response = await fetch(`${BASE_URL}/api/v1/ask/stream`, {
          method: 'POST',
          headers,
          body: JSON.stringify(data),
          signal: controller.signal,
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error(`Streaming failed with status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) {
          throw new Error('No readable stream available in response');
        }

        const decoder = new TextDecoder();
        let buffer = '';

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const parts = buffer.split('\n\n');
          buffer = parts.pop() || '';

          for (const part of parts) {
            const trimmed = part.trim();
            if (!trimmed || !trimmed.startsWith('data: ')) continue;
            try {
              const payload = JSON.parse(trimmed.slice(6));
              if (payload.type === 'metadata' && handlers.onMetadata) {
                handlers.onMetadata(payload);
              } else if (payload.type === 'token' && handlers.onToken) {
                handlers.onToken(payload.token);
              } else if (payload.type === 'done' && handlers.onDone) {
                handlers.onDone(payload);
              } else if (payload.type === 'error' && handlers.onError) {
                handlers.onError(new Error(payload.error));
              }
            } catch (err) {
              console.error('Failed to parse SSE JSON chunk:', err);
            }
          }
        }
      } catch (err: any) {
        if (err.name !== 'AbortError' && handlers.onError) {
          handlers.onError(err);
        }
      }
    })();

    return () => controller.abort();
  },
};

// Knowledge Graph API
export const graphApi = {
  async getGraph(params?: {
    tag?: string;
    memory_type?: string;
    limit?: number;
  }): Promise<GraphResponse> {
    const res = await apiFetch<{ data: GraphResponse }>('/graph/', {
      params: params as Record<string, string | number | boolean | undefined>,
    });
    return res.data;
  },

  async getNodeConnections(memoryId: string, depth: number = 1): Promise<MemoryConnectionsResponse> {
    const res = await apiFetch<{ data: MemoryConnectionsResponse }>('/graph/connections', {
      params: { memory_id: memoryId, depth },
    });
    return res.data;
  },

  async getClusters(): Promise<ClustersResponse> {
    const res = await apiFetch<{ data: ClustersResponse }>('/graph/clusters');
    return res.data;
  },

  async createEdge(data: CreateEdgeInput): Promise<GraphEdgeItem> {
    const res = await apiFetch<{ data: GraphEdgeItem }>('/graph/edges', {
      method: 'POST',
      body: JSON.stringify(data),
    });
    return res.data;
  },

  async deleteEdge(edgeId: string): Promise<void> {
    await apiFetch<{ data: { deleted: boolean } }>(`/graph/edges/${edgeId}`, {
      method: 'DELETE',
    });
  },
};

// Dashboard API
export const dashboardApi = {
  async getStats(): Promise<DashboardStatsResponse> {
    const res = await apiFetch<{ data: DashboardStatsResponse }>('/dashboard/stats');
    return res.data;
  },

  async getTimeline(limit: number = 50): Promise<TimelineResponse> {
    const res = await apiFetch<{ data: TimelineResponse }>('/dashboard/timeline', {
      params: { limit },
    });
    return res.data;
  },

  async getKnowledgeGaps(): Promise<KnowledgeGapsResponse> {
    const res = await apiFetch<{ data: KnowledgeGapsResponse }>('/dashboard/knowledge-gaps');
    return res.data;
  },
};

// Settings API
export const settingsApi = {
  async getAISettings(): Promise<AISettingsResponse> {
    const res = await apiFetch<{ data: AISettingsResponse }>('/settings/ai');
    return res.data;
  },

  async getPrivacySettings(): Promise<PrivacySettingsResponse> {
    const res = await apiFetch<{ data: PrivacySettingsResponse }>('/settings/privacy');
    return res.data;
  },

  async getUserSettings(): Promise<Record<string, any>> {
    const res = await apiFetch<{ data: Record<string, any> }>('/settings');
    return res.data;
  },
};
