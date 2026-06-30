---
title: "Personal AI Tutor Agent — Project Specification & Implementation Guide"
author: "raj100456"
date: "2026-06-30"
geometry: "margin=1in"
fontsize: 11pt
toc: true
toc-depth: 3
colorlinks: true
---

# Personal AI Tutor Agent
## Complete Architecture & Implementation Specification

**Repository:** https://github.com/raj100456/ai-tutor-agent  
**License:** Apache 2.0  
**Version:** 1.0.0  
**Date:** June 2026

---

# 1. Executive Summary

The Personal AI Tutor Agent is a production-grade, self-healing tutoring system designed for senior software engineers preparing for FAANG and staff-level technical interviews. It combines a **LangGraph state-machine orchestrator**, a **multi-provider LLM factory**, and a **plugin-based integration bus** into a single, highly configurable system where all behaviour is controlled from one configuration file.

## 1.1 Core Design Philosophy

| Principle | Mechanism |
|---|---|
| Single config point | `config.yaml` drives every behaviour |
| Zero-code provider switching | Factory + registry pattern for LLM providers |
| Plugin-based integrations | `@IntegrationRegistry.register()` decorator |
| Graph-native orchestration | LangGraph `StateGraph` with Postgres checkpointing |
| Runtime behaviour modifiers | Higher-order function decorators on the LLM |
| Streaming-first | SSE from `astream_events()` to Angular `Observable` |

## 1.2 Technology Stack

| Layer | Technology | Version |
|---|---|---|
| Backend runtime | Python | 3.12 |
| Package manager | UV (Astral) | 0.5+ |
| Web framework | FastAPI | 0.115 |
| AI orchestration | LangGraph | 0.2 |
| LangChain core | langchain-core | 0.3 |
| Local LLM | llama-cpp-python | 0.3.2 |
| Database/auth | Supabase (PostgreSQL) | 2.0 |
| Frontend framework | Angular | 18 |
| UI components | Angular Material | 18 |
| Auth | Clerk (configurable) | — |
| Deployment (FE) | Vercel | — |
| Deployment (BE) | Railway | — |

---

# 2. Requirements

## 2.1 Functional Requirements

### FR-1: Personalized Learning
- Generate adaptive learning roadmaps per topic (system design, DSA, behavioral, coding patterns)
- Track per-topic mastery levels (0–100) updated after every practice session
- Support milestone-based progression with prerequisite enforcement

### FR-2: Real-Time Chat
- Stream responses token by token via Server-Sent Events
- Maintain conversation context across sessions (Supabase checkpointing)
- Classify user intent and route to specialized nodes (planner, evaluator, feed, chat)

### FR-3: Practice & Evaluation
- Generate and score MCQ, open-ended, coding, and system design practice items
- Provide structured feedback: score, strengths, gaps, follow-up questions
- Update mastery level after each evaluation

### FR-4: Multi-Channel Notifications
- Send daily study reminders via configured channels
- Channels: Discord webhook, Slack webhook, Email (SendGrid), Firebase Push
- Cron-based scheduling via Supabase Edge Functions or Vercel Cron

### FR-5: Knowledge Feed
- Fetch daily technical content from Hacker News, GitHub Trending, and RSS feeds
- Filter by user topic keywords
- Summarize with LLM before surfacing to user

### FR-6: MCP Integration
- Load any MCP (Model Context Protocol) server as LangChain tools
- Built-in: web-search (Brave), GitHub, local filesystem

## 2.2 Non-Functional Requirements

| Requirement | Target |
|---|---|
| Chat response latency (p95) | < 2 seconds (first token) |
| Session persistence | Resumable across restarts |
| Provider failover | < 500ms switchover |
| Infrastructure cost | < $100/month |
| Extensibility | New provider/integration in < 30 min |
| Offline capable | Local llama.cpp inference, no cloud needed |

---

# 3. System Architecture

## 3.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Angular 18 UI                                │
│  ┌──────────┐  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  │
│  │  Tutor   │  │  Dashboard  │  │   Practice   │  │  Settings   │  │
│  │  (Chat)  │  │  (Progress) │  │   (Quizzes)  │  │  (Config)   │  │
│  └──────────┘  └─────────────┘  └──────────────┘  └─────────────┘  │
│         │              │                │                │           │
│         └──────────────┴────────────────┴────────────────┘           │
│                              HTTP + SSE                               │
└─────────────────────────────┬───────────────────────────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │       FastAPI Application        │
              │  /api/tutor/stream (SSE)         │
              │  /api/tutor/chat                 │
              │  /api/health                     │
              │  /api/config/summary             │
              │  /api/integrations               │
              └────────────────┬────────────────┘
                               │
              ┌────────────────▼────────────────┐
              │      LangGraph StateGraph        │
              │                                  │
              │  ┌─────────────────────────┐     │
              │  │    TutorState           │     │
              │  │  user_id, session_id    │     │
              │  │  messages (append-only) │     │
              │  │  topic, intent          │     │
              │  │  active_decorators      │     │
              │  │  evaluation_result      │     │
              │  └─────────────────────────┘     │
              │                                  │
              │  intent_classifier               │
              │       │                          │
              │  ┌────┴──────────────────┐       │
              │  ▼    ▼      ▼     ▼     │       │
              │ plan eval  feed  chat    │       │
              │  └────┴──────────────────┘       │
              │               │                  │
              │             chat ──► END         │
              └────────────────┬────────────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
┌───────▼──────┐   ┌───────────▼────────┐   ┌────────▼────────┐
│  LLM Factory  │   │  Integration Bus   │   │  Supabase DB    │
│               │   │                   │   │                  │
│  llamacpp ◄── │   │  Discord          │   │  users           │
│  openai       │   │  Email            │   │  plans           │
│  anthropic    │   │  Slack            │   │  sessions        │
│  google       │   │  MCP (web-search) │   │  user_topics     │
│  ollama       │   │  Google Calendar  │   │  feedback        │
│  azure        │   │  Firebase Push    │   │  progress        │
└───────────────┘   └───────────────────┘   └──────────────────┘
        ▲                     ▲
        │                     │
        └─────────────────────┘
                    │
            ┌───────▼────────┐
            │  config.yaml   │
            │  (single conf) │
            └────────────────┘
```

## 3.2 LangGraph State Machine

### TutorState Definition

```python
class TutorState(TypedDict):
    # Identity
    user_id: str
    session_id: str

    # Conversation (append-only via add_messages reducer)
    messages: Annotated[list[BaseMessage], add_messages]

    # Context
    topic: str | None          # e.g. "system_design"
    subtopic: str | None       # e.g. "caching_strategies"
    plan: dict | None          # Active milestone plan

    # Routing
    intent: str | None         # "chat" | "plan" | "practice" | "feed"

    # Evaluation
    evaluation_result: dict | None
    mastery_level: float | None    # 0.0–1.0

    # Behaviour
    active_decorators: list[str]

    # Knowledge feed
    knowledge_items: list[dict] | None

    # Feedback loop
    last_feedback: dict | None

    # Internal
    iteration_count: int
    error: str | None
```

### Graph Topology

```
Entry
  │
  ▼
intent_classifier ──────────────────────────────────────┐
  │                                                      │
  │  "plan"        "practice"    "feed"        "chat"   │
  ▼        ▼             ▼              ▼               │
planner  evaluator  knowledge_feed  chat ◄──────────────┘
  │          │            │
  └──────────┴────────────┘
             │
             ▼
           chat
             │
             ▼
            END (→ checkpointed to Postgres)
```

### Checkpointing Strategy

```python
# Memory (default — zero setup)
from langgraph.checkpoint.memory import MemorySaver
checkpointer = MemorySaver()

# Postgres (persistent — requires SUPABASE_DATABASE_URL)
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
```

Switch between them via `config.yaml → graph.checkpointer`.

## 3.3 LLM Provider System

### Factory Pattern

```python
# PROVIDER_REGISTRY maps config type names to classes
PROVIDER_REGISTRY: dict[str, type[AbstractLLMProvider]] = {
    "llamacpp":    LlamaCppProvider,
    "openai":      OpenAIProvider,
    "anthropic":   AnthropicProvider,
    "google":      GoogleProvider,
    "ollama":      OllamaProvider,
    "azure_openai": AzureOpenAIProvider,
}

def get_llm(task: TaskType = "chat") -> BaseChatModel:
    provider_name = settings.get_task_provider(task)   # from config.yaml
    cfg = settings.get_provider_config(provider_name)  # with env refs resolved
    provider_class = PROVIDER_REGISTRY[provider_name]
    return provider_class(cfg).build()
```

### `*_env` Resolution Pattern

```yaml
# config.yaml — YAML is safe to commit; secrets stay in .env
llm:
  providers:
    openai:
      api_key_env: "OPENAI_API_KEY"     # → os.environ["OPENAI_API_KEY"]
      model: "gpt-4o"                   # → used as-is
```

### Circuit Breaker + Fallback Chain

```python
# config.yaml
llm:
  fallback_chain: ["llamacpp", "openai", "anthropic"]
  circuit_breaker:
    max_retries: 3
    wait_multiplier_seconds: 1
    wait_max_seconds: 10
```

Uses `tenacity` for exponential backoff and LangChain's `.with_fallbacks()` for provider-level failover.

## 3.4 Integration Plugin Bus

### Plugin Registry

```python
class IntegrationRegistry:
    _registry: dict[str, type[BaseIntegration]] = {}
    _instances: dict[str, BaseIntegration] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator: register a class under a config key name."""
        def wrapper(cls_):
            cls._registry[name] = cls_
            return cls_
        return wrapper

    @classmethod
    async def get(cls, name: str) -> BaseIntegration:
        """Return an initialised instance; lazily initialises on first access."""
        if name not in cls._instances:
            await cls._load(name)
        return cls._instances[name]

    @classmethod
    async def load_enabled(cls) -> None:
        """Load all integrations from config.yaml → integrations.enabled."""
        for name in settings.get_enabled_integrations():
            await cls._load(name)
```

### Adding a New Integration (3 steps)

**Step 1** — Create the class:
```python
# src/integrations/notifier/telegram.py
@IntegrationRegistry.register("telegram")
class TelegramIntegration(BaseIntegration):
    async def initialize(self):
        self._require("bot_token", "chat_id")
        self._mark_ready()

    async def shutdown(self): pass

    async def send(self, message: str) -> None:
        # ... implementation
```

**Step 2** — Add config:
```yaml
integrations:
  enabled: ["telegram"]
  telegram:
    type: "notifier"
    bot_token_env: "TELEGRAM_BOT_TOKEN"
    chat_id_env: "TELEGRAM_CHAT_ID"
```

**Step 3** — Done. No changes to `main.py` or any other file.

## 3.5 Decorator System

Decorators are higher-order functions that wrap a `BaseChatModel` to alter its behaviour at runtime. They are applied in order from `state["active_decorators"]`.

```python
@DecoratorRegistry.register("exam_mode")
def exam_mode(llm: BaseChatModel, cfg: dict) -> BaseChatModel:
    """Wraps the LLM with strict interview simulation behaviour."""
    extra = (
        "\n[EXAM MODE ACTIVE]\n"
        "• No hints allowed.\n"
        "• Evaluate strictly.\n"
    )
    async def _inject(messages, **kwargs):
        # Augment system message
        augmented = inject_system_suffix(messages, extra)
        return await llm.ainvoke(augmented, **kwargs)

    return RunnableLambda(_inject)
```

Built-in decorators:

| Decorator | Effect |
|---|---|
| `exam_mode` | Simulates real interview — no hints, strict scoring, timed |
| `socratic_mode` | Guides via questions (80% questions, max 2 direct answers) |
| `strict_pacing` | Blocks topic skipping, enforces ≥70% mastery before advancing |
| `spaced_repetition` | SM-2 algorithm schedules reviews at optimal intervals (Phase 2) |

---

# 4. Data Model

## 4.1 Supabase Schema

```sql
-- Users (synced from Clerk)
CREATE TABLE users (
    id          TEXT PRIMARY KEY,           -- Clerk user ID
    email       TEXT,
    preferences JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Curriculum topics
CREATE TABLE topics (
    id          TEXT PRIMARY KEY,           -- e.g. "system_design"
    name        TEXT NOT NULL,
    category    TEXT,
    subtopics   JSONB DEFAULT '[]',
    difficulty  SMALLINT DEFAULT 3          -- 1-5
);

-- Per-user topic mastery
CREATE TABLE user_topics (
    user_id          TEXT REFERENCES users(id),
    topic_id         TEXT REFERENCES topics(id),
    mastery_level    SMALLINT DEFAULT 0,    -- 0-100
    last_practiced_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, topic_id)
);

-- Learning plans
CREATE TABLE plans (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT REFERENCES users(id),
    topic_id    TEXT REFERENCES topics(id),
    milestones  JSONB DEFAULT '[]',
    schedule    JSONB DEFAULT '{}',
    status      TEXT DEFAULT 'active',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Chat sessions
CREATE TABLE sessions (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT REFERENCES users(id),
    topic_id    TEXT,
    plan_id     UUID REFERENCES plans(id),
    messages    JSONB DEFAULT '[]',
    score       SMALLINT,
    started_at  TIMESTAMPTZ DEFAULT NOW(),
    ended_at    TIMESTAMPTZ
);

-- User feedback
CREATE TABLE feedback (
    id                   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id           UUID REFERENCES sessions(id),
    user_id              TEXT REFERENCES users(id),
    rating               SMALLINT,           -- 1-5
    notes                TEXT,
    adjustments_applied  JSONB DEFAULT '{}',
    created_at           TIMESTAMPTZ DEFAULT NOW()
);

-- Progress metrics
CREATE TABLE progress (
    id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id      TEXT REFERENCES users(id),
    topic_id     TEXT,
    metric_type  TEXT,                       -- "mastery", "streak", "quiz_score"
    value        NUMERIC,
    recorded_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Integration registrations
CREATE TABLE integrations (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT REFERENCES users(id),
    provider    TEXT NOT NULL,
    config      JSONB DEFAULT '{}',          -- encrypted in production
    enabled     BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Notification log
CREATE TABLE notifications (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     TEXT REFERENCES users(id),
    channel     TEXT,
    type        TEXT,
    payload     JSONB DEFAULT '{}',
    status      TEXT DEFAULT 'pending',
    sent_at     TIMESTAMPTZ
);
```

## 4.2 Row-Level Security

```sql
-- Users can only read/write their own data
ALTER TABLE user_topics ENABLE ROW LEVEL SECURITY;
CREATE POLICY "users_own_data" ON user_topics
    USING (user_id = auth.uid());

-- (apply same pattern to all user-owned tables)
```

---

# 5. API Reference

## 5.1 Endpoints

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/tutor/stream` | SSE streaming chat response |
| `POST` | `/api/tutor/chat` | Non-streaming single-turn chat |
| `GET` | `/api/health` | Liveness + readiness check |
| `GET` | `/api/config/summary` | Non-sensitive config summary |
| `GET` | `/api/settings` | Runtime settings (providers, decorators) |
| `GET` | `/api/integrations` | Integration registry status |
| `POST` | `/api/integrations/{name}/reload` | Hot-reload an integration |
| `GET` | `/api/progress` | User progress metrics |

## 5.2 Stream Event Schema

```typescript
type StreamEvent =
  | { type: "chunk";         content: string }
  | { type: "node_complete"; node: string; data: Record<string, unknown> }
  | { type: "done" }
  | { type: "error";         message: string }
```

## 5.3 Auth Modes

Configured via `config.yaml → security.auth_mode`:

| Mode | Header | Notes |
|---|---|---|
| `none` | None | Dev/local only |
| `api_key` | `X-API-Key: <key>` | Keys from `API_KEYS` env var |
| `clerk` | `Authorization: Bearer <jwt>` | Clerk JWT verified against JWKS |

---

# 6. Frontend Architecture

## 6.1 Angular 18 Application

The frontend uses Angular 18 **standalone components** with **Signals** for reactive state — no NgRx or BehaviorSubjects needed for this scale.

### SSE Streaming (key implementation)

`EventSource` API cannot send custom headers (Authorization). The `TutorService` uses `fetch()` + `ReadableStream` instead:

```typescript
stream(request: TutorRequest): Observable<StreamEvent> {
  return new Observable<StreamEvent>(subscriber => {
    const controller = new AbortController();

    fetch(`${this.baseUrl}/api/tutor/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...this.auth.getAuthHeaders(),    // Bearer token or API key
      },
      body: JSON.stringify(request),
      signal: controller.signal,
    })
    .then(async response => {
      const reader = response.body!.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        for (const line of decoder.decode(value, { stream: true }).split('\n')) {
          if (line.startsWith('data: ')) {
            const event = JSON.parse(line.slice(6)) as StreamEvent;
            subscriber.next(event);
            if (event.type === 'done') { subscriber.complete(); return; }
          }
        }
      }
    });

    return () => controller.abort();    // Teardown: cancel the request
  });
}
```

### Component Signal Architecture

```typescript
// No BehaviorSubject, no NgRx — pure Signals
@Component({ ... })
export class TutorComponent {
  // State
  readonly messages = signal<ChatMessage[]>([]);
  readonly isStreaming = this.tutorService.isStreaming;
  readonly currentTopic = this.tutorService.currentTopic;

  // Derived state
  readonly canSend = computed(
    () => this.inputText().trim().length > 0 && !this.isStreaming()
  );
}
```

---

# 7. Deployment

## 7.1 Local Development

```bash
# Backend
cd backend
CMAKE_ARGS="-DLLAMA_METAL=on" uv add llama-cpp-python
mkdir -p models && curl -L -o models/llama.gguf <model_url>
uv run uvicorn src.main:app --reload --port 8000

# Frontend
cd frontend && npm install && ng serve
```

## 7.2 Production Deployment

### Backend → Railway

```toml
# railway.toml
[build]
builder = "NIXPACKS"
buildCommand = "uv sync"

[deploy]
startCommand = "uv run uvicorn src.main:app --host 0.0.0.0 --port $PORT --workers 4"
restartPolicyType = "ON_FAILURE"
```

### Frontend → Vercel

```json
// vercel.json
{
  "rewrites": [
    { "source": "/api/(.*)", "destination": "https://your-backend.railway.app/api/$1" }
  ]
}
```

## 7.3 Estimated Monthly Cost

| Service | Tier | Cost |
|---|---|---|
| Vercel | Pro | $20 |
| Railway | Starter | $5–10 |
| Supabase | Pro | $25 |
| Clerk | Free (<10k MAU) | $0 |
| LLM APIs | Personal use | $20–30 |
| SendGrid | Free (100/day) | $0 |
| **Total** | | **~$70–85/mo** |

---

# 8. Phase Roadmap

## Phase 1 — MVP (Weeks 1–7) ✅

- [x] Config layer (`config.yaml` + `*_env` resolver)
- [x] LLM factory (llamacpp default + 5 other providers)
- [x] LangGraph StateGraph (5 nodes + conditional routing)
- [x] Decorator system (3 built-in decorators + registry)
- [x] Integration bus (Discord, Email, MCP)
- [x] FastAPI streaming endpoint (SSE)
- [x] Angular 18 chat UI with streaming
- [x] Progress dashboard
- [x] Settings page (live config display)
- [x] Circuit breaker + fallback chain
- [ ] Supabase migrations (schema SQL)
- [ ] llama-cpp-python installed with GPU flags
- [ ] Model downloaded and configured

## Phase 2 — Enhancements (Weeks 8–14)

- [ ] Firebase FCM push notifications
- [ ] Google Calendar integration
- [ ] Browser alarm (Service Worker + Notification API)
- [ ] Spaced repetition decorator (SM-2)
- [ ] MCP GitHub integration
- [ ] Real-time dashboard (Supabase Realtime)
- [ ] Richer knowledge feed (RSS + HN + GitHub Trending)
- [ ] Slack integration

## Phase 3 — Maturity (Weeks 15+)

- [ ] Multi-agent ensemble (DSA, System Design, Behavioral specialists)
- [ ] Event sourcing + full audit trail
- [ ] Advanced self-healing (latency anomaly detection)
- [ ] Offline mode (IndexedDB + service worker sync)

---

# 9. Security Considerations

## 9.1 OWASP Top 10 Mitigations

| Risk | Mitigation |
|---|---|
| **A01 Broken Access Control** | Per-route auth middleware; RLS in Supabase |
| **A02 Cryptographic Failures** | Secrets never in YAML; `*_env` pattern only |
| **A03 Injection** | LangChain message objects (not string interpolation); parameterized DB queries via Supabase SDK |
| **A05 Security Misconfiguration** | `auth_mode: "none"` only in dev; `is_production` check hides OpenAPI docs |
| **A07 Auth Failures** | Clerk JWKS verification; short-lived JWTs; API key hashing |
| **A10 SSRF** | MCP server commands whitelisted in config; no user-supplied URLs executed |

## 9.2 Key Security Practices

- Secrets **always** via `*_env` config pattern — never hard-coded
- `.env` is in `.gitignore` — `.env.example` (no secrets) is committed
- Supabase Row-Level Security enforced on all user tables
- CORS origins explicitly whitelisted in `config.yaml → app.cors_origins`
- OpenAPI docs (`/docs`, `/redoc`) disabled in production

---

# 10. Converting This Document to PDF

```bash
# Install pandoc
brew install pandoc

# Convert with proper formatting
pandoc docs/PROJECT_OVERVIEW.md \
  --pdf-engine=xelatex \
  --variable geometry:margin=1in \
  --variable fontsize=11pt \
  --variable mainfont="DejaVu Sans" \
  --toc \
  --toc-depth=3 \
  -o docs/PersonalAITutor_Spec.pdf

# Alternative: VS Code extension
# Install "Markdown PDF" extension
# Open this file → Cmd+Shift+P → "Markdown PDF: Export (pdf)"
```

---

*Personal AI Tutor Agent — Apache 2.0 License — github.com/raj100456/ai-tutor-agent*
