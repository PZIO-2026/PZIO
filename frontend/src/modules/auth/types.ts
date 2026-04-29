export type UserRole = "Guest" | "TeamMember" | "Manager" | "Administrator";

export interface User {
  userId: number;
  email: string;
  firstName: string;
  lastName: string;
  avatar: string | null;
  role: UserRole;
  isActive: boolean;
  createdAt: string;
}

export interface TokenResponse {
  accessToken: string;
  tokenType: string;
  expiresIn: number;
}

export interface JwtClaims {
  sub: string;
  role: UserRole;
  iat: number;
  exp: number;
}
