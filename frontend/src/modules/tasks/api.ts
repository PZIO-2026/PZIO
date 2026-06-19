import { apiFetch } from "../../api/client";
import type { CreateWorklogInput, WorkItem, Worklog } from "../projects/types";

export function fetchTask(id: number): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${id}`);
}

export function fetchWorklogs(taskId: number): Promise<Worklog[]> {
  return apiFetch<Worklog[]>(`/api/tasks/${taskId}/worklogs`);
}

export function createWorklog(taskId: number, payload: CreateWorklogInput): Promise<Worklog> {
  return apiFetch<Worklog>(`/api/tasks/${taskId}/worklogs`, {
    method: "POST",
    body: payload,
  });
}

