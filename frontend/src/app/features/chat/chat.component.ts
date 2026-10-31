import { Component, ElementRef, OnInit, ViewChild, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { ChatService } from '../../core/services/chat.service';
import { WebSocketService } from '../../core/services/websocket.service';
import { ModelService } from '../../core/services/model.service';
import { TypewriterComponent } from '../../shared/typewriter/typewriter.component';
import { ConversationResponse, MessageResponse, WebSocketMessage } from '../../core/models/chat.model';

@Component({
  selector: 'app-chat',
  imports: [CommonModule, FormsModule, RouterLink, TypewriterComponent],
  templateUrl: './chat.component.html',
  styleUrl: './chat.component.css'
})
export class ChatComponent implements OnInit {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef;

  private readonly authService = inject(AuthService);
  private readonly chatService = inject(ChatService);
  private readonly websocketService = inject(WebSocketService);
  readonly modelService = inject(ModelService);

  readonly currentUser = this.authService.currentUser;
  readonly conversations = signal<ConversationResponse[]>([]);
  readonly activeConversation = signal<ConversationResponse | null>(null);
  readonly messages = signal<MessageResponse[]>([]);

  readonly typingMessageId = signal<string | null>(null);
  readonly typingElapsed = signal(0);
  readonly typingSpeed = 10;
  private typingTimer?: ReturnType<typeof setInterval>;
  private followTyping = true;
  private lastScrollTop = 0;
  private readonly dimensions = ['VERIFIABILITY', 'ATOMICITY', 'AMBIGUITY', 'COMPLETENESS', 'TRACEABLE'];

  
  readonly inputValue = signal('');
  readonly isAnalyzing = signal(false);
  readonly currentStatus = signal('');
  
  // Real-time Token Streaming Signals
  readonly streamingEvaluation = signal<any>(null);
  readonly streamingFeedback = signal<any>(null);
  readonly streamingSuggestions = signal<string[]>([]);
  readonly chatReply = signal('');

  private accumulatedEval = '';
  private accumulatedFeedback = '';

  // API Key & Model Configuration Modal State
  readonly isConfigModalOpen = signal(false);
  readonly configGeminiKey = signal('');
  readonly configOpenAIKey = signal('');
  readonly configAnthropicKey = signal('');
  readonly configLocalUrl = signal('http://localhost:1234/v1');

  ngOnInit(): void {
    this.loadConversations();
    this.modelService.fetchModels().subscribe();
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
    this.resetStreaming();
    this.stopTyping();

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
    this.resetStreaming();
    this.inputValue.set('');
    this.stopTyping();
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

  typingDelay(aiData: any, kind: 'dim' | 'sug', index: number): number {
    const texts: string[] = [
      ...this.dimensions.map(d => aiData.evaluation[d]?.explanation ?? ''),
      ...aiData.feedback.suggestions
    ];
    const position = kind === 'dim' ? index : this.dimensions.length + index;
    const charsBefore = texts.slice(0, position).reduce((sum, t) => sum + t.length, 0);
    return charsBefore * this.typingSpeed;
  }

  // Una tarjeta o sugerencia del mensaje que se está escribiendo solo aparece cuando le toca
  isTypingVisible(msgId: string, aiData: any, kind: 'dim' | 'sug', index: number): boolean {
    if (msgId !== this.typingMessageId()) return true;
    return this.typingElapsed() >= this.typingDelay(aiData, kind, index);
  }

  private startTyping(msg: MessageResponse): void {
    const aiData = this.parseJSONContent(msg.content);
    const isEvaluation = aiData?.evaluation && aiData?.feedback;

    this.stopTyping();
    // Una evaluación escribe tarjeta por tarjeta; una respuesta de texto plano se escribe completa
    const total = isEvaluation
      ? this.typingDelay(aiData, 'sug', aiData.feedback.suggestions.length)
      : msg.content.length * this.typingSpeed;
    this.followTyping = true;
    const start = Date.now();
    this.typingMessageId.set(msg.id);
    this.typingElapsed.set(0);
    this.typingTimer = setInterval(() => {
      const elapsed = Date.now() - start;
      this.typingElapsed.set(elapsed);
      // Solo baja si el usuario no subió a leer algo
      if (this.followTyping) {
        requestAnimationFrame(() => {
          const el = this.scrollContainer.nativeElement;
          el.scrollTop = el.scrollHeight;
          this.lastScrollTop = el.scrollTop;
        });
      }
      // Margen para que el último texto termine antes de pasar a mostrarlo estático
      if (elapsed > total + 300) {
        this.stopTyping();
      }
    }, 30);
  }

  private stopTyping(): void {
    clearInterval(this.typingTimer);
    this.typingMessageId.set(null);
  }


  openConfigModal(): void {
    const keys = this.modelService.apiKeys();
    this.configGeminiKey.set(keys.gemini);
    this.configOpenAIKey.set(keys.openai);
    this.configAnthropicKey.set(keys.anthropic);
    this.configLocalUrl.set(keys.localUrl);
    this.isConfigModalOpen.set(true);
  }

  closeConfigModal(): void {
    this.isConfigModalOpen.set(false);
  }

  saveConfig(): void {
    this.modelService.saveApiKeys({
      gemini: this.configGeminiKey().trim(),
      openai: this.configOpenAIKey().trim(),
      anthropic: this.configAnthropicKey().trim(),
      localUrl: this.configLocalUrl().trim() || 'http://localhost:1234/v1'
    });
    this.isConfigModalOpen.set(false);
  }

  onModelSelectChange(event: Event): void {
    const select = event.target as HTMLSelectElement;
    if (select && select.value) {
      this.modelService.selectModelById(select.value);
    }
  }

  private resetStreaming(): void {
    this.streamingEvaluation.set(null);
    this.streamingFeedback.set(null);
    this.streamingSuggestions.set([]);
    this.accumulatedEval = '';
    this.accumulatedFeedback = '';
    this.chatReply.set('');
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
        this.resetStreaming();

        const selModel = this.modelService.selectedModel();
        const apiKey = this.modelService.getCurrentApiKey();
        const localUrl = this.modelService.getCurrentLocalUrl();

        this.websocketService.analyzeRequirement(text, {
          provider: selModel.provider,
          model: selModel.id,
          apiKey,
          localUrl
        }).subscribe({
          next: (msg: WebSocketMessage) => {
            if (msg.type === 'status') {
              this.currentStatus.set(msg.content);
              this.scrollToBottom();
            } else if (msg.type === 'evaluation_chunk') {
              // Parse token by token streaming for evaluation dimensions
              this.accumulatedEval += msg.content;
              for (const dim of ['VERIFIABILITY', 'ATOMICITY', 'AMBIGUITY', 'COMPLETENESS', 'TRACEABLE']) {
                const regex = new RegExp(`"${dim}"\\s*:\\s*\\{[\\s\\S]*?"score"\\s*:\\s*(\\d)[\\s\\S]*?"explanation"\\s*:\\s*"([^"\\\\]*(?:\\\\.[^"\\\\]*)*)`);
                const match = this.accumulatedEval.match(regex);
                if (match) {
                  const current = this.streamingEvaluation() || {};
                  current[dim] = {
                    score: parseInt(match[1], 10),
                    explanation: match[2].replace(/\\"/g, '"').replace(/\\n/g, '\n')
                  };
                  this.streamingEvaluation.set({ ...current });
                }
              }
              this.scrollToBottom();
            } else if (msg.type === 'evaluation_result') {
              this.streamingEvaluation.set(msg.content);
              this.scrollToBottom();
            } else if (msg.type === 'feedback_chunk') {
              // Parse token by token streaming for suggestions
              this.accumulatedFeedback += msg.content;

              // Extract suggestions in real time
              const suggMatch = this.accumulatedFeedback.match(/"suggestions"\s*:\s*\[([\s\S]*?)(\]|$)/);
              if (suggMatch) {
                const items = [...suggMatch[1].matchAll(/"((?:[^"\\]|\\.)*)"/g)].map(m => m[1].replace(/\\"/g, '"'));
                const unclosed = suggMatch[1].match(/"((?:[^"\\]|\\.)*)$/);
                if (unclosed && unclosed[1]) {
                  items.push(unclosed[1].replace(/\\"/g, '"'));
                }
                if (items.length > 0) {
                  this.streamingSuggestions.set(items);
                }
              }
              this.scrollToBottom();
            } else if (msg.type === 'feedback_result') {
              this.streamingFeedback.set(msg.content);
              if (msg.content.suggestions) {
                this.streamingSuggestions.set(msg.content.suggestions);
              }
              this.scrollToBottom();
            } else if (msg.type === 'chat_reply') {
              this.chatReply.set(msg.content);
            }
          },
          error: (err) => {
            console.error('Error en websocket streaming', err);
            this.isAnalyzing.set(false);
            this.currentStatus.set('');
          },
          complete: () => {
            this.isAnalyzing.set(false);
            this.currentStatus.set('');

            const evalObj = this.streamingEvaluation();
            const feedObj = this.streamingFeedback() || {
              suggestions: this.streamingSuggestions().length > 0 ? this.streamingSuggestions() : ['Evaluación completada.']
            };

            let finalAIContent = '';
            if (this.chatReply()) {
              finalAIContent = this.chatReply();
            } else if (evalObj && feedObj) {
              finalAIContent = JSON.stringify({
                evaluation: evalObj,
                feedback: feedObj
              });
            } else {
              finalAIContent = 'No se pudo completar el análisis del requisito.';
            }

            this.chatService.addMessage(convId, 'AI', finalAIContent).subscribe({
              next: (aiMsg) => {
                this.messages.update(list => [...list, aiMsg]);
                this.resetStreaming();
                this.scrollToBottom();
                this.startTyping(aiMsg);
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

  // Si el usuario sube, se deja de seguir el texto; si vuelve al final, se retoma
  onChatScroll(): void {
    const el = this.scrollContainer.nativeElement;
    if (el.scrollTop < this.lastScrollTop) {
      this.followTyping = false;
    } else if (el.scrollHeight - el.scrollTop - el.clientHeight < 20) {
      this.followTyping = true;
    }
    this.lastScrollTop = el.scrollTop;
  }

  private scrollToBottom(): void {
    setTimeout(() => {
      if (this.scrollContainer) {
        const el = this.scrollContainer.nativeElement;
        el.scrollTop = el.scrollHeight;
      }
    }, 50);
  }
}
