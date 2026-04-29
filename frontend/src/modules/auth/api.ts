import { apiFetch } from "../../api/client";
import type { LoginInput, RegisterInput } from "./schemas";
import type { TokenResponse, User } from "./types";

export function register(input: RegisterInput): Promise<User> {
  return apiFetch<User>("/api/auth/register", {
    method: "POST",
    body: input,
  });
}

export function login(input: LoginInput): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/auth/login", {
    method: "POST",
    body: input,
  });
}

export function getMe(): Promise<User> {
  return apiFetch<User>("/api/users/me");
}

export interface UpdateMeInput {
  firstName: string;
  lastName: string;
  avatar: string | null;
}

export function updateMe(input: UpdateMeInput): Promise<User> {
  return apiFetch<User>("/api/users/me", {
    method: "PATCH",
    body: input,
  });
}
