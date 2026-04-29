import { createContext } from "react";

import type { UserRole } from "./types";

export interface AuthState {
  token: string | null;
  email: string | null;
  userId: number | null;
  role: UserRole | null;
}

export interface AuthContextValue extends AuthState {
  login: (token: string, email: string) => void;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
