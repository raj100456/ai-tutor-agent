/**
 * Tutor (Chat) Component — the primary learning interface.
 *
 * Features:
 *  • Real-time streaming via TutorService.stream() Observable
 *  • Auto-scroll to latest message
 *  • Markdown rendering for AI responses
 *  • Topic + decorator selection
 *  • Evaluation result display inline
 *  • Angular Signals for reactive state (no NgRx needed)
 */
import {
  AfterViewChecked,
  ChangeDetectionStrategy,
  Component,
  ElementRef,
  OnDestroy,
  ViewChild,
  computed,
  inject,
  signal,
} from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatChipsModule } from '@angular/material/chips';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTooltipModule } from '@angular/material/tooltip';
import { Subscription } from 'rxjs';
import { ChatMessage, StreamEvent } from '../../core/models/tutor.models';
import { TutorService } from '../../core/services/tutor.service';
import { MessageBubbleComponent } from '../../shared/components/message-bubble/message-bubble.component';

@Component({
  selector: 'app-tutor',
  standalone: true,
  changeDetection: ChangeDetectionStrategy.OnPush,
  imports: [
    FormsModule,
    MatButtonModule,
    MatChipsModule,
    MatFormFieldModule,
    MatIconModule,
    MatInputModule,
    MatProgressSpinnerModule,
    MatSelectModule,
    MatTooltipModule,
    MessageBubbleComponent,
  ],
  templateUrl: './tutor.component.html',
  styleUrl: './tutor.component.scss',
})
export class TutorComponent implements AfterViewChecked, OnDestroy {
  @ViewChild('messagesEnd') private messagesEnd!: ElementRef;

  private readonly tutorService = inject(TutorService);
  private streamSub: Subscription | null = null;

  // ── State signals ─────────────────────────────────────────────────────────
  readonly messages = signal<ChatMessage[]>([]);
  readonly inputText = signal('');
  readonly sessionId = signal(crypto.randomUUID());
  readonly isStreaming = this.tutorService.isStreaming;
  readonly currentTopic = this.tutorService.currentTopic;
  readonly activeDecorators = this.tutorService.activeDecorators;

  readonly canSend = computed(
    () => this.inputText().trim().length > 0 && !this.isStreaming(),
  );

  readonly availableTopics = [
    { id: 'system_design', label: 'System Design' },
    { id: 'dsa', label: 'DSA' },
    { id: 'behavioral', label: 'Behavioral' },
    { id: 'coding_patterns', label: 'Coding Patterns' },
  ];

  readonly availableDecorators = [
    { id: 'exam_mode', label: '🎯 Exam Mode' },
    { id: 'socratic_mode', label: '🤔 Socratic' },
    { id: 'strict_pacing', label: '📏 Strict Pacing' },
  ];

  // ── Lifecycle ─────────────────────────────────────────────────────────────

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  ngOnDestroy(): void {
    this.streamSub?.unsubscribe();
  }

  // ── Actions ───────────────────────────────────────────────────────────────

  onTopicChange(topicId: string): void {
    this.tutorService.setTopic(topicId);
  }

  toggleDecorator(name: string): void {
    this.tutorService.toggleDecorator(name);
  }

  isDecoratorActive(name: string): boolean {
    return this.activeDecorators().includes(name);
  }

  sendMessage(): void {
    const text = this.inputText().trim();
    if (!text || this.isStreaming()) return;

    // Add user message immediately
    const userMsg: ChatMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    this.messages.update(msgs => [...msgs, userMsg]);
    this.inputText.set('');

    // Add a streaming placeholder for the AI response
    const aiMsgId = crypto.randomUUID();
    const aiMsg: ChatMessage = {
      id: aiMsgId,
      role: 'assistant',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };
    this.messages.update(msgs => [...msgs, aiMsg]);

    this.streamSub?.unsubscribe();
    this.streamSub = this.tutorService
      .stream({
        message: text,
        session_id: this.sessionId(),
      })
      .subscribe({
        next: (event: StreamEvent) => this.handleStreamEvent(event, aiMsgId),
        error: (err: Error) => this.handleStreamError(err, aiMsgId),
        complete: () => this.finaliseStreamingMessage(aiMsgId),
      });
  }

  onEnterKey(event: KeyboardEvent): void {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      this.sendMessage();
    }
  }

  // ── Stream event handlers ─────────────────────────────────────────────────

  private handleStreamEvent(event: StreamEvent, msgId: string): void {
    if (event.type === 'chunk') {
      this.messages.update(msgs =>
        msgs.map(m =>
          m.id === msgId ? { ...m, content: m.content + event.content } : m,
        ),
      );
    } else if (event.type === 'node_complete' && event.node === 'evaluator') {
      this.messages.update(msgs =>
        msgs.map(m =>
          m.id === msgId
            ? { ...m, metadata: { ...m.metadata, evaluation: event.data as any } }
            : m,
        ),
      );
    }
  }

  private handleStreamError(err: Error, msgId: string): void {
    this.messages.update(msgs =>
      msgs.map(m =>
        m.id === msgId
          ? { ...m, content: `Error: ${err.message}`, isStreaming: false }
          : m,
      ),
    );
  }

  private finaliseStreamingMessage(msgId: string): void {
    this.messages.update(msgs =>
      msgs.map(m => (m.id === msgId ? { ...m, isStreaming: false } : m)),
    );
  }

  private scrollToBottom(): void {
    try {
      this.messagesEnd.nativeElement.scrollIntoView({ behavior: 'smooth' });
    } catch {
      // ignore
    }
  }
}
