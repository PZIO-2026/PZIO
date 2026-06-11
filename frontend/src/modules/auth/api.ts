import { apiFetch } from "../../api/client";
import type { LoginInput, RegisterPayload } from "./schemas";
import type { MessageResponse, TokenResponse, User } from "./types";

export function register(input: RegisterPayload): Promise<User> {
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

export interface OAuthLoginInput {
  provider: string;
  oauthToken: string;
}

export function oauthLogin(input: OAuthLoginInput): Promise<TokenResponse> {
  return apiFetch<TokenResponse>("/api/auth/oauth", {
    method: "POST",
    body: input,
  });
}
export function requestPasswordReset(email: string): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/auth/reset-password", {
    method: "POST",
    body: { email },
  });
}

export interface ConfirmPasswordResetInput {
  token: string;
  newPassword: string;
}

export function confirmPasswordReset(input: ConfirmPasswordResetInput): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/auth/reset-password/confirm", {
    method: "POST",
    body: input,
  });
}

export interface ChangeEmailApiInput {
  email: string;
}

export function changeEmail(input: ChangeEmailApiInput): Promise<User> {
  return apiFetch<User>("/api/users/me/email", {
    method: "PATCH",
    body: input,
  });
}

export interface ChangePasswordApiInput {
  oldPassword: string;
  newPassword: string;
}

export function changePassword(input: ChangePasswordApiInput): Promise<MessageResponse> {
  return apiFetch<MessageResponse>("/api/users/me/change-password", {
    method: "POST",
    body: input,
  });
}

export function deleteMe(): Promise<void> {
  return apiFetch<void>("/api/users/me", {
    method: "DELETE",
  });
}
