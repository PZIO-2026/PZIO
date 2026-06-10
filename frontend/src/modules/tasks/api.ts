import { apiFetch } from "../../api/client";
import type { WorkItem } from "../projects/types";

export function fetchTask(id: number): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${id}`);
}

