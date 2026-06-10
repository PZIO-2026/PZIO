// ============================================================
// Projekty
// ============================================================

export type ProjectStatus = "active" | "archived";

export interface Project {
  projectId: number;
  name: string;
  description: string | null;
  status: ProjectStatus;
  createdAt: string;
  currentUserRoles: ProjectRole[];
}

export interface ProjectStats {
  memberCount: number;
  sprintCount: number;
}


export interface ProjectDetail extends Project {
  stats: ProjectStats;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}

export interface ProjectsQueryParams {
  status?: ProjectStatus;
  search?: string;
  sortBy?: string;
  sortDirection?: "asc" | "desc";
  page?: number;
  size?: number;
}

// ============================================================
// Członkowie projektu
// ============================================================

export type ProjectRole =
  | "project_owner"
  | "scrum_master"
  | "developer"
  | "qa"
  | "maintainer";

export interface ProjectMember {
  userId: number;
  firstName: string;
  lastName: string;
  email: string;
  roles: ProjectRole[];
  joinedAt: string;
}

export interface MembersQueryParams {
  role?: ProjectRole;
  search?: string;
  page?: number;
  size?: number;
}

// ============================================================
// Sprinty
// ============================================================

export type SprintStatus = "planned" | "active" | "completed";

export interface Sprint {
  sprintId: number;
  projectId: number;
  name: string;
  startDate: string;
  endDate: string;
  status: SprintStatus;
  goal?: string;
}

// ============================================================
// Zadania (Work Items)
// ============================================================

export type WorkItemStatus = "ToDo" | "InProgress" | "Done";

export interface WorkItem {
  id: number;
  projectId: number;
  title: string;
  description: string | null;
  type: string;
  priority: string;
  storyPoints: number | null;
  parentId: number | null;
  assigneeId: number | null;
  sprintId: number | null;
  status: WorkItemStatus;
  createdAt: string;
  updatedAt: string | null;
}

export interface BurndownDay {
  date: string;
  remainingPoints: number;
}

export interface BurndownData {
  sprintId: number;
  totalPoints: number;
  days: BurndownDay[];
}
