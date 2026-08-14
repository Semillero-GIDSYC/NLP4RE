import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { ConversationResponse, MessageResponse } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8081/api/v1/conversations';

  getConversations(): Observable<ConversationResponse[]> {
    return this.http.get<ConversationResponse[]>(this.apiUrl);
  }

  createConversation(title: string): Observable<ConversationResponse> {
    return this.http.post<ConversationResponse>(this.apiUrl, { title });
  }

  getMessages(conversationId: string): Observable<MessageResponse[]> {
    return this.http.get<MessageResponse[]>(`${this.apiUrl}/${conversationId}/messages`);
  }

  addMessage(conversationId: string, sender: string, content: string): Observable<MessageResponse> {
    return this.http.post<MessageResponse>(`${this.apiUrl}/${conversationId}/messages`, { sender, content });
  }

  deleteConversation(conversationId: string): Observable<void> {
    return this.http.delete<void>(`${this.apiUrl}/${conversationId}`);
  }
}
