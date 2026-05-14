import { apiFetch } from "../../api/client";
import type { User, UserRole } from "../auth/types";
import type {
  ActivityLogEntry,
  BackupResponse,
  ListUsersParams,
  PaginatedUsersResponse,
  TaskType,
} from "./types";

export function fetchTaskTypes(): Promise<TaskType[]> {
  return apiFetch<TaskType[]>("/api/task-types");
}

export interface CreateTaskTypeInput {
  name: string;
}

export function createTaskType(input: CreateTaskTypeInput): Promise<TaskType> {
  return apiFetch<TaskType>("/api/admin/task-types", {
    method: "POST",
    body: input,
  });
}

export function createBackup(): Promise<BackupResponse> {
  return apiFetch<BackupResponse>("/api/admin/backups", {
    method: "POST",
  });
}

export function fetchTaskHistory(taskId: number): Promise<ActivityLogEntry[]> {
  return apiFetch<ActivityLogEntry[]>(`/api/tasks/${taskId}/history`);
}

export function fetchUsers(params: ListUsersParams = {}): Promise<PaginatedUsersResponse> {
  const search = new URLSearchParams();
  if (params.search) search.set("search", params.search);
  if (params.page) search.set("page", String(params.page));
  if (params.size) search.set("size", String(params.size));
  const qs = search.toString();
  return apiFetch<PaginatedUsersResponse>(`/api/users${qs ? `?${qs}` : ""}`);
}

export function updateUserRole(userId: number, role: UserRole): Promise<User> {
  return apiFetch<User>(`/api/users/${userId}/role`, {
    method: "PATCH",
    body: { role },
  });
}
