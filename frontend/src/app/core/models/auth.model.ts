export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

export interface AuthResponse {
  token: string;
  username: string;
  email: string;
  roles: string[];
}

export interface UserResponse {
  id: string;
  username: string;
  email: string;
  roles: string[];
  createdAt: string;
}

export interface UpdateProfileRequest {
  username: string;
  email: string;
}
