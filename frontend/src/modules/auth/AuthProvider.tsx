import { useState } from "react";
import type { ReactNode } from "react";

import { AuthContext } from "./context";
import type { AuthState } from "./context";
import { clearSession, getStoredEmail, getStoredToken, persistSession } from "./storage";
import type { JwtClaims } from "./types";

const EMPTY_STATE: AuthState = { token: null, email: null, userId: null, role: null };

function decodeClaims(token: string): JwtClaims | null {
  const parts = token.split(".");
  if (parts.length !== 3) return null;
  try {
    return JSON.parse(atob(parts[1])) as JwtClaims;
  } catch {
    return null;
  }
}

function buildState(token: string, email: string): AuthState {
  const claims = decodeClaims(token);
  if (claims === null) return EMPTY_STATE;
  if (Date.now() >= claims.exp * 1000) return EMPTY_STATE;
  const userId = Number.parseInt(claims.sub, 10);
  if (Number.isNaN(userId)) return EMPTY_STATE;
  return { token, email, userId, role: claims.role };
}

function loadInitialState(): AuthState {
  const token = getStoredToken();
  const email = getStoredEmail();
  if (token === null || email === null) return EMPTY_STATE;
  const state = buildState(token, email);
  // Token expired or malformed — wipe storage so we don't retry on next reload.
  if (state.token === null) clearSession();
  return state;
}

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AuthState>(loadInitialState);

  function login(token: string, email: string) {
    const next = buildState(token, email);
    if (next.token === null) return;
    persistSession(token, email);
    setState(next);
  }

  function logout() {
    clearSession();
    setState(EMPTY_STATE);
  }

  return <AuthContext value={{ ...state, login, logout }}>{children}</AuthContext>;
}
