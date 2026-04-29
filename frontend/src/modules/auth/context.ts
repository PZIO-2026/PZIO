import { createContext } from "react";

import type { User } from "./types";

export interface AuthState {
  token: string | null;
  user: User | null;
  isLoadingUser: boolean;
}

export interface AuthContextValue extends AuthState {
  login: (token: string) => void;
  logout: () => void;
  updateUser: (user: User) => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);
