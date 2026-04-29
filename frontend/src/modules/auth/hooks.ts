import { use } from "react";

import { AuthContext } from "./context";

export function useAuth() {
  const ctx = use(AuthContext);
  if (ctx === null) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return ctx;
}
