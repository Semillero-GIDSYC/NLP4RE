import { Component, ElementRef, OnInit, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../core/services/auth.service';
import { ChatService } from '../../core/services/chat.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { ConversationResponse, MessageResponse, WebSocketMessage } from '../../core/models/chat.model';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  private readonly authService = inject(AuthService);
  private readonly chatService = inject(ChatService);
  private readonly websocketService = inject(WebSocketService);

  readonly currentUser = this.authService.currentUser;
  readonly conversations = signal<ConversationResponse[]>([]);
  readonly activeConversation = signal<ConversationResponse | null>(null);
  readonly messages = signal<MessageResponse[]>([]);
  
  readonly inputValue = signal('');
  readonly isAnalyzing = signal(false);
  readonly currentStatus = signal('');
  
  readonly streamingEvaluation = signal<any>(null);
  readonly streamingFeedback = signal<any>(null);

  ngOnInit(): void {
    this.loadConversations();
  }

  loadConversations(): void {
    this.chatService.getConversations().subscribe({
      next: (data) => this.conversations.set(data),
      error: (err) => console.error('Error cargando conversaciones', err)
    });
  }

  selectConversation(conv: ConversationResponse): void {
    if (this.isAnalyzing()) return;
    this.activeConversation.set(conv);
    this.streamingEvaluation.set(null);
    this.streamingFeedback.set(null);
    
    this.chatService.getMessages(conv.id).subscribe({
      next: (data) => {
        this.messages.set(data);
        this.scrollToBottom();
      },
      error: (err) => console.error('Error cargando mensajes', err)
    });
  }

  startNewConversation(): void {
    if (this.isAnalyzing()) return;
    this.activeConversation.set(null);
    this.messages.set([]);
    this.streamingEvaluation.set(null);
    this.streamingFeedback.set(null);
    this.inputValue.set('');
  }

  deleteConversation(event: Event, convId: string): void {
    event.stopPropagation();
    if (this.isAnalyzing()) return;
    
    this.chatService.deleteConversation(convId).subscribe({
      next: () => {
        this.conversations.update(list => list.filter(c => c.id !== convId));
        if (this.activeConversation()?.id === convId) {
          this.startNewConversation();
        }
      },
      error: (err) => console.error('Error al borrar conversacion', err)
    });
  }

  onSend(): void {
    const text = this.inputValue().trim();
    if (!text || this.isAnalyzing()) return;

    this.inputValue.set('');
    
    if (!this.activeConversation()) {
      const title = text.length > 35 ? text.substring(0, 35) + '...' : text;
      this.chatService.createConversation(title).subscribe({
        next: (conv) => {
          this.activeConversation.set(conv);
          this.conversations.update(list => [conv, ...list]);
          this.saveAndAnalyzeMessage(conv.id, text);
        },
        error: (err) => console.error('Error creando conversacion', err)
      });
    } else {
      this.saveAndAnalyzeMessage(this.activeConversation()!.id, text);
    }
  }

  private saveAndAnalyzeMessage(convId: string, text: string): void {
    this.chatService.addMessage(convId, 'USER', text).subscribe({
      next: (userMsg) => {
        this.messages.update(list => [...list, userMsg]);
        this.scrollToBottom();
        
        this.isAnalyzing.set(true);
        this.currentStatus.set('Iniciando analizador...');
        this.streamingEvaluation.set(null);
        this.streamingFeedback.set(null);

        this.websocketService.analyzeRequirement(text).subscribe({
          next: (msg: WebSocketMessage) => {
            if (msg.type === 'status') {
              this.currentStatus.set(msg.content);
            } else if (msg.type === 'evaluation_result') {
              this.streamingEvaluation.set(msg.content);
            } else if (msg.type === 'feedback_result') {
              this.streamingFeedback.set(msg.content);
            }
          },
          error: (err) => {
            console.error('Error in websocket stream', err);
            this.isAnalyzing.set(false);
            this.currentStatus.set('');
          },
          complete: () => {
            this.isAnalyzing.set(false);
            this.currentStatus.set('');

            const evalObj = this.streamingEvaluation();
            const feedObj = this.streamingFeedback();
            let finalAIContent = '';
            
            if (evalObj && feedObj) {
              finalAIContent = JSON.stringify({
                evaluation: evalObj,
                feedback: feedObj
              });
            } else {
              finalAIContent = 'Lo siento, no se pudo completar el análisis del requisito.';
            }

            this.chatService.addMessage(convId, 'AI', finalAIContent).subscribe({
              next: (aiMsg) => {
                this.messages.update(list => [...list, aiMsg]);
                this.streamingEvaluation.set(null);
                this.streamingFeedback.set(null);
                this.scrollToBottom();
              },
              error: (err) => console.error('Error al guardar respuesta IA', err)
            });
          }
        });
      },
      error: (err) => console.error('Error al guardar mensaje usuario', err)
    });
  }

  parseJSONContent(content: string): any {
    try {
      return JSON.parse(content);
    } catch {
      return null;
    }
  }

  logout(): void {
    this.authService.logout();
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.scrollContainer) {
        const el = this.scrollContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 100);
  }
}
