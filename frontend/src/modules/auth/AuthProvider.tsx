import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { getMe } from "./api";
import { AuthContext } from "./context";
import { clearStoredToken, getStoredToken, setStoredToken } from "./storage";
import type { User } from "./types";

export default function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => getStoredToken());
  const [user, setUser] = useState<User | null>(null);

  // We're loading the profile whenever we have a token but haven't resolved a
  // user yet. Failed fetches clear the token, so this naturally goes back to
  // false instead of getting stuck.
  const isLoadingUser = token !== null && user === null;

  useEffect(() => {
    if (token === null || user !== null) return;

    let cancelled = false;

    getMe()
      .then((fetchedUser) => {
        if (cancelled) return;
        setUser(fetchedUser);
      })
      .catch(() => {
        if (cancelled) return;
        // Token rejected (expired, revoked, server unreachable) — drop the
        // session so ProtectedRoute bounces the user back to /login.
        clearStoredToken();
        setToken(null);
        setUser(null);
      });

    return () => {
      cancelled = true;
    };
  }, [token, user]);

  function login(newToken: string) {
    setStoredToken(newToken);
    setUser(null);
    setToken(newToken);
  }

  function logout() {
    clearStoredToken();
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext value={{ token, user, isLoadingUser, login, logout }}>{children}</AuthContext>
  );
}
