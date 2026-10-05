export interface User {
  id: string;
  email: string;
  full_name: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
}

export interface Credentials {
  email: string;
  password: string;
}

export interface Registration extends Credentials {
  full_name: string;
}
