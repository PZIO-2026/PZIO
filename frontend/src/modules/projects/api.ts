import { apiFetch } from "../../api/client";
import type {
  BurndownData,
  MembersQueryParams,
  PaginatedResponse,
  Project,
  ProjectDetail,
  ProjectMember,
  ProjectsQueryParams,
  Sprint,
  WorkItem,
} from "./types";
import type { TaskFormInput } from "./schemas";
import type {
  AddMemberFormInput,
  CreateProjectFormInput,
  SprintFormInput,
  UpdateProjectFormInput,
} from "./schemas";

// ============================================================
// Pomocnik: budowanie query stringa
// ============================================================

function toQueryString(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(
    ([, v]) => v !== undefined && v !== null && v !== "",
  );
  if (entries.length === 0) return "";
  const qs = entries.map(([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`).join("&");
  return `?${qs}`;
}

// ============================================================
// Projekty
// ============================================================

export function fetchProjects(
  params: ProjectsQueryParams = {},
): Promise<PaginatedResponse<Project>> {
  return apiFetch<PaginatedResponse<Project>>(
    `/api/projects${toQueryString(params as Record<string, unknown>)}`,
  );
}

export function fetchProject(id: number): Promise<ProjectDetail> {
  return apiFetch<ProjectDetail>(`/api/projects/${id}`);
}

export function createProject(input: CreateProjectFormInput): Promise<Project> {
  return apiFetch<Project>("/api/projects", {
    method: "POST",
    body: input,
  });
}

export function updateProject(
  id: number,
  input: UpdateProjectFormInput,
): Promise<Project> {
  return apiFetch<Project>(`/api/projects/${id}`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteProject(id: number): Promise<void> {
  return apiFetch<void>(`/api/projects/${id}`, {
    method: "DELETE",
  });
}

// ============================================================
// Członkowie projektu
// ============================================================

export function fetchProjectMembers(
  projectId: number,
  params: MembersQueryParams = {},
): Promise<PaginatedResponse<ProjectMember>> {
  return apiFetch<PaginatedResponse<ProjectMember>>(
    `/api/projects/${projectId}/members${toQueryString(params as Record<string, unknown>)}`,
  );
}

export function addProjectMember(
  projectId: number,
  input: AddMemberFormInput,
): Promise<ProjectMember> {
  return apiFetch<ProjectMember>(`/api/projects/${projectId}/members`, {
    method: "POST",
    body: input,
  });
}

export function removeProjectMember(
  projectId: number,
  userId: number,
): Promise<void> {
  return apiFetch<void>(`/api/projects/${projectId}/members/${userId}`, {
    method: "DELETE",
  });
}

export async function updateProjectMemberRoles(projectId: number, userId: number, roles: string[]) {
  return apiFetch(`/api/projects/${projectId}/members/${userId}`, {
    method: "PATCH",
    body: { roles },
  });
}

// ============================================================
// Sprinty
// ============================================================

export function fetchSprints(projectId: number): Promise<Sprint[]> {
  return apiFetch<Sprint[]>(`/api/projects/${projectId}/sprints`);
}

export function createSprint(
  projectId: number,
  input: SprintFormInput,
): Promise<Sprint> {
  return apiFetch<Sprint>(`/api/projects/${projectId}/sprints`, {
    method: "POST",
    body: {
      name: input.name,
      startDate: input.startDate,
      endDate: input.endDate,
      goal: input.goal,
    },
  });
}

export function updateSprint(
  sprintId: number,
  input: SprintFormInput,
): Promise<Sprint> {
  return apiFetch<Sprint>(`/api/sprints/${sprintId}`, {
    method: "PATCH",
    body: input,
  });
}

export function deleteSprint(sprintId: number): Promise<void> {
  return apiFetch<void>(`/api/sprints/${sprintId}`, {
    method: "DELETE",
  });
}

export function fetchBurndown(sprintId: number): Promise<BurndownData> {
  return apiFetch<BurndownData>(`/api/sprints/${sprintId}/burndown`);
}

// ============================================================
// Zadania (Work Items)
// ============================================================

export function fetchTasks(
  projectId: number,
  params: { status?: string; sprintId?: number } = {},
): Promise<WorkItem[]> {
  return apiFetch<WorkItem[]>(
    `/api/projects/${projectId}/tasks${toQueryString(params as Record<string, unknown>)}`,
  );
}

export function createTask(
  projectId: number,
  input: TaskFormInput & { status: string },
): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/projects/${projectId}/tasks`, {
    method: "POST",
    body: input,
  });
}

export function updateTask(taskId: number, input: TaskFormInput): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${taskId}`, {
    method: "PATCH",
    body: input,
  });
}

export function updateTaskStatus(taskId: number, status: string): Promise<WorkItem> {
  return apiFetch<WorkItem>(`/api/tasks/${taskId}/status`, {
    method: "PATCH",
    body: { status },
  });
}

export function deleteTask(taskId: number): Promise<void> {
  return apiFetch<void>(`/api/tasks/${taskId}`, { method: "DELETE" });
}
