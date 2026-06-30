/**
 * AuthService — pluggable auth facade.
 * Delegates to Clerk when configured; falls back to API key or no-auth mode.
 * Auth mode is read from the runtime config (mirrors config.yaml → security.auth_mode).
 */
import { Injectable, signal } from '@angular/core';

export type AuthMode = 'none' | 'api_key' | 'clerk';

@Injectable({ providedIn: 'root' })
export class AuthService {
  readonly user = signal<{ id: string; email?: string } | null>(null);
  private _token: string | null = null;
  private _apiKey: string | null = null;
  private _mode: AuthMode = 'none';

  /**
   * Called once at app startup from app.config.ts.
   * Detects auth mode from the backend config endpoint.
   */
  async initialize(): Promise<void> {
    try {
      const response = await fetch('/api/config/summary');
      const cfg = await response.json() as { auth_mode: AuthMode };
      this._mode = cfg.auth_mode ?? 'none';
    } catch {
      this._mode = 'none';
    }

    if (this._mode === 'none') {
      this.user.set({ id: 'local-user', email: 'local@localhost' });
    }
    // Clerk and api_key modes handled externally (Clerk SDK / settings)
  }

  setToken(token: string): void {
    this._token = token;
  }

  setApiKey(key: string): void {
    this._apiKey = key;
  }

  getAuthHeaders(): Record<string, string> {
    if (this._mode === 'clerk' && this._token) {
      return { Authorization: `Bearer ${this._token}` };
    }
    if (this._mode === 'api_key' && this._apiKey) {
      return { 'X-API-Key': this._apiKey };
    }
    return {};
  }

  get isAuthenticated(): boolean {
    return this.user() !== null;
  }

  get mode(): AuthMode {
    return this._mode;
  }
}
