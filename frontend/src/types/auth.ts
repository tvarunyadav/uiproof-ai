export interface User {
  user_id: string;
  email: string;
  created_at: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface LogoutResponse {
  message: string;
}

export interface AuthError {
  message: string;
  status?: number;
}
