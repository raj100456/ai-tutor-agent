/**
 * Dashboard component — progress charts and milestone overview.
 */
import { ChangeDetectionStrategy, Component, OnInit, inject, signal } from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { TutorService } from '../../core/services/tutor.service';
import { UserProgress } from '../../core/models/tutor.models';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatIconModule, MatProgressBarModule, MatChipsModule],
  template: `
    <div class="dashboard">
      <h1 class="page-title">
        <mat-icon>bar_chart</mat-icon> Progress Dashboard
      </h1>

      <div class="progress-grid">
        @for (p of progress(); track p.topic_id) {
          <mat-card class="progress-card">
            <mat-card-header>
              <mat-icon mat-card-avatar>{{ topicIcon(p.topic_id) }}</mat-icon>
              <mat-card-title>{{ topicLabel(p.topic_id) }}</mat-card-title>
              <mat-card-subtitle>Mastery: {{ p.mastery_level }}%</mat-card-subtitle>
            </mat-card-header>
            <mat-card-content>
              <mat-progress-bar
                mode="determinate"
                [value]="p.mastery_level"
                [color]="p.mastery_level >= 70 ? 'primary' : 'warn'">
              </mat-progress-bar>
              <p class="last-practiced">Last practiced: {{ p.last_practiced_at | slice:0:10 }}</p>
            </mat-card-content>
          </mat-card>
        }

        @if (progress().length === 0) {
          <div class="empty-state">
            <mat-icon>school</mat-icon>
            <p>Start studying to see your progress here!</p>
          </div>
        }
      </div>
    </div>
  `,
  styles: [`
    .dashboard { padding: 2rem; color: #e2e8f0; }

    .page-title {
      display: flex; align-items: center; gap: 0.5rem;
      font-size: 1.5rem; font-weight: 700; color: #a78bfa; margin-bottom: 2rem;
    }

    .progress-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
      gap: 1.5rem;
    }

    .progress-card {
      background: #1a1d27 !important;
      border: 1px solid #2d3748;
      color: #e2e8f0;
    }

    .last-practiced { font-size: 0.75rem; color: #718096; margin-top: 0.5rem; }

    .empty-state {
      grid-column: 1 / -1;
      text-align: center; color: #4a5568; padding: 3rem;
      mat-icon { font-size: 3rem; height: 3rem; width: 3rem; }
    }
  `],
})
export class DashboardComponent implements OnInit {
  private readonly tutorService = inject(TutorService);
  readonly progress = signal<UserProgress[]>([]);

  ngOnInit(): void {
    this.tutorService.getProgress().subscribe({
      next: data => this.progress.set(data),
      error: () => this.progress.set([]),
    });
  }

  topicLabel(id: string): string {
    const labels: Record<string, string> = {
      system_design: 'System Design',
      dsa: 'DSA',
      behavioral: 'Behavioral',
      coding_patterns: 'Coding Patterns',
    };
    return labels[id] ?? id;
  }

  topicIcon(id: string): string {
    const icons: Record<string, string> = {
      system_design: 'architecture',
      dsa: 'data_array',
      behavioral: 'psychology',
      coding_patterns: 'code',
    };
    return icons[id] ?? 'school';
  }
}
