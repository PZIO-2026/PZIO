export type ProjectStatus = "active" | "archived";
export type ProjectRole = "project_owner" | "scrum_master" | "developer" | "qa";

export interface Project {
  projectId: number;
  name: string;
  description: string | null;
  status: ProjectStatus;
  createdAt: string;
  updatedAt: string | null;
}

export interface ProjectStats {
  memberCount: number;
  sprintCount: number;
}

export interface ProjectDetail extends Project {
  stats: ProjectStats;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
}