import type { ProjectRole } from "../types";

interface ProjectRoleBadgeProps {
  role: ProjectRole;
}

const roleConfig: Record<
  ProjectRole,
  {
    label: string;
    className: string;
  }
> = {
  project_owner: {
    label: "Project Owner",
    className:
      "bg-purple-100 text-purple-700 border border-purple-200",
  },

  scrum_master: {
    label: "Scrum Master",
    className:
      "bg-blue-100 text-blue-700 border border-blue-200",
  },

  developer: {
    label: "Developer",
    className:
      "bg-emerald-100 text-emerald-700 border border-emerald-200",
  },

  qa: {
    label: "QA Engineer",
    className:
      "bg-orange-100 text-orange-700 border border-orange-200",
  },

  maintainer: {
    label: "Maintainer",
    className:
      "bg-slate-100 text-slate-700 border border-slate-200",
  },
};

export default function ProjectRoleBadge({
  role,
}: ProjectRoleBadgeProps) {
  const config = roleConfig[role];

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium ${config.className}`}
    >
      {config.label}
    </span>
  );
}