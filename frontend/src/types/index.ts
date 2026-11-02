export type Tag = {
  id: string;
  name: string;
  color?: string | null;
};

export type MemoryChunk = {
  id: string;
  chunk_index: number;
  content: string;
  token_count?: number | null;
};

export type MemorySource = {
  id: string;
  source_type: string;
  source_uri: string;
  source_title?: string | null;
};

export type Memory = {
  id: string;
  title: string | null;
  content: string;
  summary?: string | null;
  memory_type: string;
  source_type: string;
  tags: string[];
  is_archived: boolean;
  created_at: string;
  updated_at: string;
};

export type MemoryDetail = Memory & {
  chunks: MemoryChunk[];
  sources: MemorySource[];
  connections_count: number;
};

export type MemoryListResponse = {
  items: Memory[];
  total: number;
  limit: number;
  offset: number;
};

export type CreateMemoryInput = {
  title?: string;
  content: string;
  memory_type?: string;
  source_type?: string;
  source_uri?: string;
  tags?: string[];
  project_ids?: string[];
};

export type UpdateMemoryInput = {
  title?: string;
  content?: string;
  summary?: string;
  memory_type?: string;
  tags?: string[];
};

export type Project = {
  id: string;
  name: string;
  description: string;
  createdAt: string;
  updatedAt: string;
};

export type Message = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  createdAt: string;
};

export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
};

export type SearchRequest = {
  query: string;
  limit?: number;
  memory_type?: string;
  tag?: string;
  min_score?: number;
};

export type SearchResultItem = {
  memory_id: string;
  title?: string | null;
  snippet: string;
  memory_type: string;
  score: number;
  tags: string[];
  chunk_index?: number | null;
  created_at: string;
};

export type SearchResponse = {
  query: string;
  search_type: string;
  results: SearchResultItem[];
  total: number;
};

export type SearchHistoryItem = {
  id: string;
  query: string;
  search_type: string;
  results_count?: number | null;
  created_at: string;
};

export type SearchHistoryResponse = {
  items: SearchHistoryItem[];
  total: number;
};

export type SearchResult = SearchResultItem;

export type SourceAttributionItem = {
  index: number;
  memory_id: string;
  title?: string | null;
  snippet: string;
  relevance_score: number;
  memory_type: string;
  is_cited?: boolean;
};

export type AskRequest = {
  query: string;
  conversation_id?: string | null;
  limit?: number;
};

export type AskResponse = {
  conversation_id: string;
  answer: string;
  sources: SourceAttributionItem[];
};

export type ConversationItem = {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  message_count: number;
};

export type ConversationMessage = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  sources?: SourceAttributionItem[];
  created_at: string;
};

export type ConversationDetail = {
  id: string;
  title?: string | null;
  created_at: string;
  updated_at: string;
  messages: ConversationMessage[];
};

export type AskStreamEvent =
  | { type: 'metadata'; conversation_id: string; sources: SourceAttributionItem[] }
  | { type: 'token'; token: string }
  | { type: 'error'; error: string }
  | { type: 'done'; conversation_id: string; sources?: SourceAttributionItem[] };

export type User = {
  id: string;
  email: string;
  display_name?: string | null;
  created_at?: string;
};

export type TokenResponse = {
  access_token: string;
  token_type: string;
  user?: User | null;
};

export type IngestionJob = {
  id: string;
  source_type: string;
  source_uri: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  error_message?: string | null;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
};

export type IngestionJobListResponse = {
  items: IngestionJob[];
  total: number;
};

export type ApiError = {
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  message?: string;
  code?: string;
};

export type GraphNodeItem = {
  id: string;
  title: string;
  snippet: string;
  memory_type: string;
  tags: string[];
  connection_count: number;
  created_at: string;
};

export type GraphEdgeItem = {
  id: string;
  source: string;
  target: string;
  relation_type: string;
  confidence: number;
  created_by: string;
  metadata?: any;
  created_at: string;
};

export type GraphResponse = {
  nodes: GraphNodeItem[];
  edges: GraphEdgeItem[];
  total_nodes: number;
  total_edges: number;
};

export type CreateEdgeInput = {
  source_memory_id: string;
  target_memory_id: string;
  relation_type?: string;
  confidence?: number;
  metadata?: any;
};

export type ClusterItem = {
  id: string;
  name: string;
  node_ids: string[];
  size: number;
  tags: string[];
  description?: string | null;
};

export type ClustersResponse = {
  clusters: ClusterItem[];
  total_clusters: number;
};

export type MemoryConnectionsResponse = {
  memory_id: string;
  nodes: GraphNodeItem[];
  edges: GraphEdgeItem[];
  total_connections: number;
};

export type TypeBreakdownItem = {
  memory_type: string;
  count: number;
  percentage: number;
  color: string;
};

export type ActivityDayItem = {
  date: string;
  day_name: string;
  count: number;
};

export type TopTagItem = {
  name: string;
  count: number;
};

export type DashboardStatsResponse = {
  total_memories: number;
  new_this_week: number;
  total_edges: number;
  total_conversations: number;
  total_chunks: number;
  types: TypeBreakdownItem[];
  activity: ActivityDayItem[];
  top_tags: TopTagItem[];
};

export type TimelineMemoryItem = {
  id: string;
  title: string;
  snippet: string;
  memory_type: string;
  tags: string[];
  created_at: string;
};

export type TimelineDayGroup = {
  date: string;
  formatted_date: string;
  memories: TimelineMemoryItem[];
};

export type TimelineResponse = {
  groups: TimelineDayGroup[];
  total: number;
};

export type KnowledgeGapItem = {
  memory_id: string;
  title: string;
  memory_type: string;
  reason: string;
};

export type KnowledgeGapsResponse = {
  gaps: KnowledgeGapItem[];
  orphaned_count: number;
  untagged_count: number;
  health_score: number;
};

export type AISettingsResponse = {
  ollama_available: boolean;
  ollama_url: string;
  llm_provider: string;
  embedding_provider: string;
  embedding_dimensions: number;
  local_only: boolean;
  privacy_first: boolean;
  default_model: string;
};

export type PrivacySettingsResponse = {
  local_first: boolean;
  telemetry_enabled: boolean;
  cloud_sync_enabled: boolean;
  zero_cost_local_mode: boolean;
  encryption_at_rest: boolean;
};
