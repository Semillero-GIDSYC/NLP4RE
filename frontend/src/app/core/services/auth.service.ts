import { Injectable, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Observable, tap } from 'rxjs';
import { LoginRequest, RegisterRequest, AuthResponse } from '../models/auth.model';

@Injectable({
  providedIn: 'root'
})
export class AuthService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly apiUrl = 'http://localhost:8081/api/v1/auth';

  readonly currentUser = signal<AuthResponse | null>(null);

  constructor() {
    const stored = localStorage.getItem('auth_data');
    if (stored) {
      try {
        this.currentUser.set(JSON.parse(stored));
      } catch {
        localStorage.removeItem('auth_data');
      }
    }
  }

  get token(): string | null {
    return this.currentUser()?.token || null;
  }

  get isAuthenticated(): boolean {
    return this.currentUser() !== null;
  }

  login(request: LoginRequest): Observable<AuthResponse> {
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, request).pipe(
      tap(response => {
        this.currentUser.set(response);
        localStorage.setItem('auth_data', JSON.stringify(response));
      })
    );
  }

  register(request: RegisterRequest): Observable<any> {
    return this.http.post(`${this.apiUrl}/register`, request);
  }

  logout(): void {
    this.currentUser.set(null);
    localStorage.removeItem('auth_data');
    this.router.navigate(['/login']);
  }
}
