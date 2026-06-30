/**
 * TutorService — primary communication layer with the FastAPI backend.
 *
 * Key design decisions:
 *  • SSE streaming uses fetch() + ReadableStream (not EventSource) so that
 *    Authorization headers can be sent — EventSource does not support custom headers.
 *  • All streaming chunks are delivered as an Observable<StreamEvent> for idiomatic RxJS use.
 *  • Non-streaming calls use Angular HttpClient with the auth interceptor.
 */
import { HttpClient } from '@angular/common/http';
import { Injectable, inject, signal } from '@angular/core';
import { Observable, Subject, from } from 'rxjs';
import { environment } from '@env/environment';
import {
  ConfigSummary,
  StreamEvent,
  TutorRequest,
  TutorResponse,
  UserProgress,
} from '../models/tutor.models';
import { AuthService } from './auth.service';

@Injectable({ providedIn: 'root' })
export class TutorService {
  private readonly http = inject(HttpClient);
  private readonly auth = inject(AuthService);
  private readonly baseUrl = environment.apiUrl;

  // ── Signals for reactive UI state ────────────────────────────────────────
  readonly isStreaming = signal(false);
  readonly currentTopic = signal<string | null>(null);
  readonly activeDecorators = signal<string[]>([]);

  // ── SSE Streaming ─────────────────────────────────────────────────────────

  /**
   * Stream a tutor response via SSE.
   * Returns an Observable that emits StreamEvent objects.
   * The Observable completes when the server sends { "type": "done" }.
   *
   * Usage in component:
   *   this.tutor.stream(req).subscribe({
   *     next: event => { ... },
   *     complete: () => { ... },
   *     error: err => { ... },
   *   });
   */
  stream(request: TutorRequest): Observable<StreamEvent> {
    return new Observable<StreamEvent>(subscriber => {
      const controller = new AbortController();
      this.isStreaming.set(true);

      const body: TutorRequest = {
        ...request,
        topic: request.topic ?? this.currentTopic() ?? undefined,
        active_decorators: request.active_decorators ?? this.activeDecorators(),
      };

      fetch(`${this.baseUrl}/api/tutor/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...this.auth.getAuthHeaders(),
        },
        body: JSON.stringify(body),
        signal: controller.signal,
      })
        .then(async response => {
          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }
          if (!response.body) {
            throw new Error('Response body is null');
          }

          const reader = response.body.getReader();
          const decoder = new TextDecoder();

          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const text = decoder.decode(value, { stream: true });
              // SSE format: lines starting with "data: "
              for (const line of text.split('\n')) {
                if (!line.startsWith('data: ')) continue;
                const raw = line.slice(6).trim();
                if (!raw) continue;
                try {
                  const event = JSON.parse(raw) as StreamEvent;
                  subscriber.next(event);
                  if (event.type === 'done') {
                    subscriber.complete();
                    return;
                  }
                  if (event.type === 'error') {
                    subscriber.error(new Error(event.message));
                    return;
                  }
                } catch {
                  // Ignore malformed SSE lines
                }
              }
            }
            subscriber.complete();
          } finally {
            reader.releaseLock();
            this.isStreaming.set(false);
          }
        })
        .catch(err => {
          this.isStreaming.set(false);
          if (err.name !== 'AbortError') {
            subscriber.error(err);
          }
        });

      // Teardown: abort the fetch when the Observable is unsubscribed
      return () => {
        controller.abort();
        this.isStreaming.set(false);
      };
    });
  }

  // ── Non-streaming chat ────────────────────────────────────────────────────

  chat(request: TutorRequest): Observable<TutorResponse> {
    return this.http.post<TutorResponse>(`${this.baseUrl}/api/tutor/chat`, request);
  }

  // ── Configuration & progress ──────────────────────────────────────────────

  getConfigSummary(): Observable<ConfigSummary> {
    return this.http.get<ConfigSummary>(`${this.baseUrl}/api/config/summary`);
  }

  getProgress(): Observable<UserProgress[]> {
    return this.http.get<UserProgress[]>(`${this.baseUrl}/api/progress`);
  }

  getHealth(): Observable<Record<string, unknown>> {
    return this.http.get<Record<string, unknown>>(`${this.baseUrl}/api/health`);
  }

  // ── Local state helpers ───────────────────────────────────────────────────

  setTopic(topic: string): void {
    this.currentTopic.set(topic);
  }

  setDecorators(decorators: string[]): void {
    this.activeDecorators.set(decorators);
  }

  toggleDecorator(name: string): void {
    const current = this.activeDecorators();
    const updated = current.includes(name)
      ? current.filter(d => d !== name)
      : [...current, name];
    this.activeDecorators.set(updated);
  }
}
