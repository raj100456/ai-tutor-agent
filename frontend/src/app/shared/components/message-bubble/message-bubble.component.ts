/**
 * MessageBubble — renders a single chat message with Markdown support.
 * Handles user and assistant roles with distinct visual treatment.
 * Displays inline evaluation scores when present.
 */
import {
  ChangeDetectionStrategy,
  Component,
  Input,
  OnChanges,
  SimpleChanges,
} from '@angular/core';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';
import { marked } from 'marked';
import { ChatMessage } from '../../../core/models/tutor.models';

@Component({
  selector: 'app-message-bubble',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [MatCardModule, MatIconModule, MatProgressBarModule],
  template: `
    <div class="bubble-wrapper" [class.user]="message.role === 'user'" [class.assistant]="message.role === 'assistant'">

      <div class="avatar">
        <mat-icon>{{ message.role === 'user' ? 'person' : 'smart_toy' }}</mat-icon>
      </div>

      <div class="bubble">
        <div class="content" [innerHTML]="renderedContent"></div>

        <!-- Streaming cursor -->
        @if (message.isStreaming) {
          <span class="cursor">▊</span>
        }

        <!-- Evaluation result inline display -->
        @if (message.metadata?.['evaluation']) {
          <div class="eval-card">
            <div class="eval-header">
              <mat-icon>analytics</mat-icon>
              Score: {{ message.metadata!['evaluation'].score }}/100
              <span [class]="message.metadata!['evaluation'].passed ? 'passed' : 'failed'">
                {{ message.metadata!['evaluation'].passed ? '✓ Passed' : '✗ Needs work' }}
              </span>
            </div>
            <mat-progress-bar
              mode="determinate"
              [value]="message.metadata!['evaluation'].score"
              [color]="message.metadata!['evaluation'].passed ? 'primary' : 'warn'">
            </mat-progress-bar>
            @if (message.metadata!['evaluation'].gaps?.length) {
              <p class="gaps-label">Gaps: {{ message.metadata!['evaluation'].gaps.join(' · ') }}</p>
            }
          </div>
        }

        <span class="timestamp">{{ message.timestamp | date:'HH:mm' }}</span>
      </div>
    </div>
  `,
  styles: [`
    .bubble-wrapper {
      display: flex;
      gap: 0.75rem;
      max-width: 85%;
      align-items: flex-start;

      &.user {
        flex-direction: row-reverse;
        align-self: flex-end;
        margin-left: auto;

        .bubble { background: #7c3aed; border-radius: 18px 4px 18px 18px; }
        .avatar mat-icon { color: #a78bfa; }
      }

      &.assistant {
        align-self: flex-start;
        .bubble { background: #1e2235; border-radius: 4px 18px 18px 18px; }
        .avatar mat-icon { color: #38bdf8; }
      }
    }

    .avatar {
      width: 36px;
      height: 36px;
      border-radius: 50%;
      background: #2d3748;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    .bubble {
      padding: 0.75rem 1rem;
      color: #e2e8f0;
      font-size: 0.9rem;
      line-height: 1.6;
      position: relative;

      .content ::ng-deep {
        pre { background: #0f1117; padding: 0.75rem; border-radius: 6px; overflow-x: auto; }
        code { font-family: 'JetBrains Mono', monospace; font-size: 0.85em; }
        p:last-child { margin-bottom: 0; }
        ul, ol { padding-left: 1.5rem; }
      }
    }

    .cursor {
      animation: blink 1s step-end infinite;
      color: #7c3aed;
    }
    @keyframes blink { 50% { opacity: 0; } }

    .eval-card {
      margin-top: 0.75rem;
      padding: 0.75rem;
      background: rgba(0,0,0,0.3);
      border-radius: 8px;
      font-size: 0.8rem;

      .eval-header {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-bottom: 0.5rem;
        font-weight: 600;
      }

      .passed { color: #68d391; }
      .failed { color: #fc8181; }

      .gaps-label {
        margin: 0.5rem 0 0;
        color: #fc8181;
        font-size: 0.75rem;
      }
    }

    .timestamp {
      display: block;
      text-align: right;
      font-size: 0.65rem;
      color: #4a5568;
      margin-top: 0.25rem;
    }
  `],
})
export class MessageBubbleComponent implements OnChanges {
  @Input({ required: true }) message!: ChatMessage;

  renderedContent: SafeHtml = '';

  constructor(private sanitizer: DomSanitizer) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['message']) {
      const html = marked.parse(this.message.content || '') as string;
      this.renderedContent = this.sanitizer.bypassSecurityTrustHtml(html);
    }
  }
}
