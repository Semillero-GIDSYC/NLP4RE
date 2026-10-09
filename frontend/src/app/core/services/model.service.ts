import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, catchError, of, tap } from 'rxjs';
import { ApiKeysConfig, ModelInfo } from '../models/chat.model';

@Injectable({
  providedIn: 'root'
})
export class ModelService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = 'http://localhost:8001/models';

  private readonly defaultModels: ModelInfo[] = [
    {
      id: 'gemini-2.5-flash',
      name: 'Gemini 2.5 Flash',
      provider: 'gemini',
      description: 'Google - Rápido y preciso (Recomendado)',
      is_local: false,
      requires_key: true
    },
    {
      id: 'gemini-2.5-pro',
      name: 'Gemini 2.5 Pro',
      provider: 'gemini',
      description: 'Google - Mayor razonamiento analítico',
      is_local: false,
      requires_key: true
    },
    {
      id: 'gpt-4o-mini',
      name: 'GPT-4o Mini',
      provider: 'openai',
      description: 'OpenAI - Rápido y eficiente',
      is_local: false,
      requires_key: true
    },
    {
      id: 'claude-3-5-sonnet-20241022',
      name: 'Claude 3.5 Sonnet',
      provider: 'anthropic',
      description: 'Anthropic - Excelente para arquitectura y código',
      is_local: false,
      requires_key: true
    },
    {
      id: 'google/gemma-3-4b',
      name: 'Local: google/gemma-3-4b',
      provider: 'local',
      description: 'Local en LM Studio / Ollama (Sin Internet)',
      is_local: true,
      requires_key: false
    }
  ];

  readonly models = signal<ModelInfo[]>(this.defaultModels);
  readonly selectedModel = signal<ModelInfo>(this.defaultModels[0]);
  
  readonly apiKeys = signal<ApiKeysConfig>({
    gemini: '',
    openai: '',
    anthropic: '',
    localUrl: 'http://localhost:1234/v1'
  });

  constructor() {
    this.loadFromStorage();
    this.fetchModels();
  }

  private loadFromStorage(): void {
    try {
      const storedKeys = localStorage.getItem('nlp4re_api_keys');
      if (storedKeys) {
        this.apiKeys.set({
          ...this.apiKeys(),
          ...JSON.parse(storedKeys)
        });
      }

      const storedModel = localStorage.getItem('nlp4re_selected_model');
      if (storedModel) {
        this.selectedModel.set(JSON.parse(storedModel));
      }
    } catch (e) {
      console.error('Error cargando configuración local', e);
    }
  }

  fetchModels(): Observable<ModelInfo[]> {
    return this.http.get<ModelInfo[]>(this.apiUrl).pipe(
      tap((loaded) => {
        if (loaded && loaded.length > 0) {
          this.models.set(loaded);
          const current = this.selectedModel();
          const match = loaded.find(m => m.id === current.id);
          if (match) {
            this.selectedModel.set(match);
          }
        }
      }),
      catchError(() => {
        return of(this.defaultModels);
      })
    );
  }

  selectModel(model: ModelInfo): void {
    this.selectedModel.set(model);
    localStorage.setItem('nlp4re_selected_model', JSON.stringify(model));
  }

  selectModelById(modelId: string): void {
    const found = this.models().find(m => m.id === modelId);
    if (found) {
      this.selectModel(found);
    }
  }

  saveApiKeys(keys: Partial<ApiKeysConfig>): void {
    const updated = { ...this.apiKeys(), ...keys };
    this.apiKeys.set(updated);
    localStorage.setItem('nlp4re_api_keys', JSON.stringify(updated));
  }

  getCurrentApiKey(): string | undefined {
    const current = this.selectedModel();
    const keys = this.apiKeys();
    if (current.provider === 'gemini') return keys.gemini || undefined;
    if (current.provider === 'openai') return keys.openai || undefined;
    if (current.provider === 'anthropic') return keys.anthropic || undefined;
    return undefined;
  }

  getCurrentLocalUrl(): string | undefined {
    const current = this.selectedModel();
    if (current.provider === 'local') {
      return this.apiKeys().localUrl || undefined;
    }
    return undefined;
  }
}
