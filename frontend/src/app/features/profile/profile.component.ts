import { Component, ElementRef, OnInit, ViewChild, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HttpErrorResponse } from '@angular/common/http';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../core/services/auth.service';
import { UserResponse } from '../../core/models/auth.model';

@Component({
  selector: 'app-profile',
  imports: [ReactiveFormsModule, RouterLink, DatePipe],
  templateUrl: './profile.component.html',
  styleUrl: './profile.component.css',
  host: { '(document:keydown.escape)': 'closeDeleteModal()' }
})
export class ProfileComponent implements OnInit {
  private readonly fb = inject(FormBuilder);
  private readonly authService = inject(AuthService);

  readonly profile = signal<UserResponse | null>(null);
  readonly isSaving = signal(false);
  readonly errorMessage = signal<string | null>(null);
  readonly successMessage = signal<string | null>(null);

  // Delete account modal state
  readonly isDeleteModalOpen = signal(false);
  readonly isDeleting = signal(false);
  readonly deleteError = signal<string | null>(null);
  readonly deleteConfirmation = signal('');
  readonly canDelete = computed(() => this.deleteConfirmation() === this.profile()?.username);

  @ViewChild('confirmInput') set confirmInput(input: ElementRef<HTMLInputElement> | undefined) {
    input?.nativeElement.focus();
  }

  readonly profileForm = this.fb.nonNullable.group({
    username: ['', [Validators.required, Validators.minLength(3), Validators.maxLength(50)]],
    email: ['', [Validators.required, Validators.email, Validators.maxLength(100)]]
  });

  ngOnInit(): void {
    this.authService.getProfile().subscribe({
      next: (data) => {
        this.profile.set(data);
        this.profileForm.reset({ username: data.username, email: data.email });
      },
      error: (err) => this.errorMessage.set(this.getErrorMessage(err, 'No se pudo cargar el perfil'))
    });
  }

  onSubmit(): void {
    if (this.profileForm.invalid || this.profileForm.pristine) return;

    this.isSaving.set(true);
    this.errorMessage.set(null);
    this.successMessage.set(null);

    const { username, email } = this.profileForm.getRawValue();

    this.authService.updateProfile({ username: username.trim(), email: email.trim() }).subscribe({
      next: (response) => {
        this.isSaving.set(false);
        this.profile.update(current => current
          ? { ...current, username: response.username, email: response.email }
          : current);
        this.profileForm.reset({ username: response.username, email: response.email });
        this.successMessage.set('Cambios guardados');
      },
      error: (err) => {
        this.isSaving.set(false);
        this.errorMessage.set(this.getErrorMessage(err, 'Ocurrió un error al actualizar el perfil'));
      }
    });
  }

  discardChanges(): void {
    const current = this.profile();
    if (!current) return;
    this.profileForm.reset({ username: current.username, email: current.email });
    this.errorMessage.set(null);
  }

  openDeleteModal(): void {
    this.deleteConfirmation.set('');
    this.deleteError.set(null);
    this.isDeleteModalOpen.set(true);
  }

  closeDeleteModal(): void {
    if (this.isDeleting()) return;
    this.isDeleteModalOpen.set(false);
  }

  onDeleteConfirmationInput(event: Event): void {
    this.deleteConfirmation.set((event.target as HTMLInputElement).value);
  }

  onDeleteAccount(): void {
    if (!this.canDelete() || this.isDeleting()) return;

    this.isDeleting.set(true);
    this.deleteError.set(null);

    // On success the service closes the session and redirects to /login
    this.authService.deactivateAccount().subscribe({
      error: (err) => {
        this.isDeleting.set(false);
        this.deleteError.set(this.getErrorMessage(err, 'No se pudo eliminar la cuenta. Intenta de nuevo.'));
      }
    });
  }

  private getErrorMessage(err: HttpErrorResponse, fallback: string): string {
    if (typeof err.error === 'string' && err.error) return err.error;
    return err.error?.message || fallback;
  }
}
