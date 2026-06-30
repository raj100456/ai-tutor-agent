/**
 * Settings component — runtime configuration, integration status, provider info.
 * All config is read from the backend /api/config/summary endpoint.
 * Changes to decorators and topics are applied via TutorService signals.
 */
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSlideToggleModule } from '@angular/material/slide-toggle';
import { ConfigSummary } from '../../core/models/tutor.models';
import { TutorService } from '../../core/services/tutor.service';

@Component({
  selector: 'app-settings',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatChipsModule, MatDividerModule, MatIconModule, MatListModule, MatSlideToggleModule],
  template: `
    <div class="settings-page">
      <h1 class="page-title"><mat-icon>settings</mat-icon> Settings</h1>

      @if (config()) {
        <div class="settings-grid">

          <!-- LLM Providers -->
          <mat-card class="settings-card">
            <mat-card-header>
              <mat-icon mat-card-avatar>psychology</mat-icon>
              <mat-card-title>LLM Providers</mat-card-title>
              <mat-card-subtitle>Configured in config.yaml → llm</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              @for (entry of providerEntries(); track entry.task) {
                <div class="provider-row">
                  <span class="task-label">{{ entry.task }}</span>
                  <mat-chip>{{ entry.provider }}</mat-chip>
                </div>
              }
              <mat-divider />
              <p class="hint">Change provider: edit <code>config.yaml → llm.task_providers</code></p>
            </mat-card-content>
          </mat-card>

          <!-- Integrations -->
          <mat-card class="settings-card">
            <mat-card-header>
              <mat-icon mat-card-avatar>extension</mat-icon>
              <mat-card-title>Integrations</mat-card-title>
              <mat-card-subtitle>Enabled in config.yaml → integrations.enabled</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              @for (item of config()!.integrations.active; track item.name) {
                <div class="integration-row">
                  <mat-icon [class]="item.ready ? 'ready' : 'error'">
                    {{ item.ready ? 'check_circle' : 'error' }}
                  </mat-icon>
                  <span>{{ item.name }}</span>
                  <mat-chip [color]="item.ready ? 'primary' : 'warn'">
                    {{ item.ready ? 'Ready' : 'Error' }}
                  </mat-chip>
                </div>
              }
              @if (!config()!.integrations.active.length) {
                <p class="hint">No integrations enabled. Add names to <code>integrations.enabled</code> in config.yaml.</p>
              }
            </mat-card-content>
          </mat-card>

          <!-- Decorators -->
          <mat-card class="settings-card">
            <mat-card-header>
              <mat-icon mat-card-avatar>tune</mat-icon>
              <mat-card-title>Learning Mode Decorators</mat-card-title>
              <mat-card-subtitle>Active this session</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <mat-chip-set>
                @for (d of config()!.tutor.active_decorators; track d) {
                  <mat-chip color="primary" selected>{{ d }}</mat-chip>
                }
                @if (!config()!.tutor.active_decorators.length) {
                  <p class="hint">No decorators active. Toggle them from the Tutor sidebar.</p>
                }
              </mat-chip-set>
            </mat-card-content>
          </mat-card>

          <!-- System info -->
          <mat-card class="settings-card">
            <mat-card-header>
              <mat-icon mat-card-avatar>info</mat-icon>
              <mat-card-title>System</mat-card-title>
            </mat-card-header>
            <mat-card-content>
              <div class="info-row"><span>Environment</span><mat-chip>{{ config()!.environment }}</mat-chip></div>
              <div class="info-row"><span>Auth mode</span><mat-chip>{{ config()!.auth_mode }}</mat-chip></div>
              <div class="info-row"><span>Graph checkpointer</span><mat-chip>{{ config()!.graph.checkpointer }}</mat-chip></div>
            </mat-card-content>
          </mat-card>

        </div>
      }
    </div>
  `,
  styles: [`
    .settings-page { padding: 2rem; color: #e2e8f0; }
    .page-title {
      display: flex; align-items: center; gap: 0.5rem;
      font-size: 1.5rem; font-weight: 700; color: #a78bfa; margin-bottom: 2rem;
    }
    .settings-grid {
      display: grid; grid-template-columns: repeat(auto-fill, minmax(360px, 1fr)); gap: 1.5rem;
    }
    .settings-card { background: #1a1d27 !important; border: 1px solid #2d3748; color: #e2e8f0; }
    .provider-row, .integration-row, .info-row {
      display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0;
    }
    .task-label { color: #a0aec0; min-width: 120px; font-size: 0.85rem; }
    .ready { color: #68d391; }
    .error { color: #fc8181; }
    .hint { font-size: 0.78rem; color: #718096; margin: 0.5rem 0 0; }
    code { background: #0f1117; padding: 0.1rem 0.3rem; border-radius: 3px; font-size: 0.8rem; }
    mat-divider { margin: 0.75rem 0; }
  `],
})
export class SettingsComponent implements OnInit {
  private readonly tutorService = inject(TutorService);
  readonly config = signal<ConfigSummary | null>(null);

  ngOnInit(): void {
    this.tutorService.getConfigSummary().subscribe({
      next: data => this.config.set(data),
    });
  }

  providerEntries(): Array<{ task: string; provider: string }> {
    const providers = this.config()?.llm.task_providers ?? {};
    return Object.entries(providers).map(([task, provider]) => ({ task, provider }));
  }
}
