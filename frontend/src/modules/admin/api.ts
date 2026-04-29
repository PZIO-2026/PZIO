import { apiFetch } from "../../api/client";
import type { ActivityLogEntry, BackupResponse, TaskType } from "./types";

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
