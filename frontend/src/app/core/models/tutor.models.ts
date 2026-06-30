// ================================================================
// Shared TypeScript models — mirror the FastAPI Pydantic schemas.
// Single source of truth for all frontend ↔ backend data contracts.
// ================================================================

export interface TutorRequest {
  message: string;
  session_id?: string;
  topic?: string;
  subtopic?: string;
  active_decorators?: string[];
}

export interface TutorResponse {
  session_id: string;
  message: string;
  intent: string | null;
  evaluation_result: EvaluationResult | null;
  mastery_level: number | null;
  knowledge_items: KnowledgeItem[] | null;
}

export interface EvaluationResult {
  score: number;
  mastery_delta: number;
  passed: boolean;
  strengths: string[];
  gaps: string[];
  follow_up_question: string;
  detailed_feedback: string;
}

export interface KnowledgeItem {
  summary: string;
  raw: string[];
}

// SSE stream event shapes
export type StreamEventType = 'chunk' | 'node_complete' | 'done' | 'error';

export interface StreamChunk {
  type: 'chunk';
  content: string;
}

export interface NodeCompleteEvent {
  type: 'node_complete';
  node: 'planner' | 'evaluator' | 'knowledge_feed';
  data: Record<string, unknown>;
}

export interface DoneEvent {
  type: 'done';
}

export interface ErrorEvent {
  type: 'error';
  message: string;
}

export type StreamEvent = StreamChunk | NodeCompleteEvent | DoneEvent | ErrorEvent;

// ── Chat UI models ─────────────────────────────────────────────────────────

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  isStreaming?: boolean;
  metadata?: {
    intent?: string;
    evaluation?: EvaluationResult;
    mastery_level?: number;
  };
}

// ── Progress / Settings ────────────────────────────────────────────────────

export interface Topic {
  id: string;
  name: string;
  subtopics: string[];
}

export interface ConfigSummary {
  llm: {
    task_providers: Record<string, string>;
    available_providers: string[];
    fallback_chain: string[];
  };
  graph: {
    checkpointer: string;
    max_iterations: number;
  };
  tutor: {
    topics: string[];
    active_decorators: string[];
  };
  integrations: {
    enabled: string[];
    active: Array<{ name: string; ready: boolean }>;
  };
  auth_mode: string;
  environment: string;
}

export interface UserProgress {
  topic_id: string;
  mastery_level: number;
  last_practiced_at: string;
}
