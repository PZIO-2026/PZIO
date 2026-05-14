import { apiFetch } from "../../api/client";
import type { WorkItem } from "../projects/types";

export function fetchTask(id: number): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${id}`);
}

export function updateTaskAssignee(taskId: number, assigneeId: number | null): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: { assigneeId },
  });
}
