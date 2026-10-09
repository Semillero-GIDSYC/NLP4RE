import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { WebSocketMessage } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class WebSocketService {
  private readonly wsUrl = 'ws://localhost:8001/ws/analyze';

  analyzeRequirement(
    text: string, 
    options?: { provider?: string; model?: string; apiKey?: string; localUrl?: string }
  ): Observable<WebSocketMessage> {
    return new Observable<WebSocketMessage>(observer => {
      const socket = new WebSocket(this.wsUrl);

      socket.onopen = () => {
        socket.send(JSON.stringify({
          text,
          provider: options?.provider,
          model: options?.model,
          apiKey: options?.apiKey,
          localUrl: options?.localUrl
        }));
      };

      socket.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          observer.next(data);
          if (data.type === 'done') {
            observer.complete();
            socket.close();
          }
        } catch (e) {
          observer.error(e);
        }
      };

      socket.onerror = (error) => {
        observer.error(error);
      };

      socket.onclose = () => {
        observer.complete();
      };

      return () => {
        if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
          socket.close();
        }
      };
    });
  }
}
