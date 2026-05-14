// src/modules/projects/layouts/ProjectDetailsLayout.tsx

import { NavLink, Outlet, useParams } from "react-router-dom";
import { useEffect, useState } from "react";

import { ApiError } from "../../../api/client";
import { fetchProject } from "../api";
import type { Project, ProjectDetail } from "../types";
import ProjectRoleBadge from "../components/ProjectRoleBadge";

const navigationItems = [
  {
    label: "Overview",
    path: "",
  },
  {
    label: "Członkowie",
    path: "members",
  },
  {
    label: "Sprinty",
    path: "sprints",
  },
  {
    label: "Backlog",
    path: "backlog",
  },
  {
    label: "Board",
    path: "board",
  },
];


export default function ProjectDetailsLayout() {
  const { projectId } = useParams();

  const [project, setProject] = useState<ProjectDetail | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (projectId === undefined) return;

    let cancelled = false;

    setIsLoading(true);
    setError(null);

    fetchProject(Number(projectId))
      .then((response) => {
        if (cancelled) return;
        setProject(response);
      })
      .catch((err) => {
        if (cancelled) return;

        setError(
          err instanceof ApiError
            ? err.detail
            : "Nie udało się pobrać szczegółów projektu.",
        );
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, [projectId]);

  if (isLoading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <p className="text-sm text-gray-500">
          Ładowanie szczegółów projektu...
        </p>
      </div>
    );
  }

  if (error !== null) {
    return (
      <div className="mx-auto max-w-3xl px-4 py-10">
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      </div>
    );
  }

  if (project === null) {
    return null;
  }

  function handleProjectUpdated(updatedProject: Project) {
    setProject((current) =>
      current === null
        ? current
        : {
            ...current,
            name: updatedProject.name,
            description: updatedProject.description,
            status: updatedProject.status,
            createdAt: updatedProject.createdAt,
          },
    );
  }

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <div className="grid gap-6 lg:grid-cols-[260px_minmax(0,1fr)]">
        {/* Sidebar */}
        <aside className="h-fit rounded-2xl bg-white p-4 shadow">
          <div className="border-b border-gray-200 pb-4">
            <h2 className="truncate text-lg font-bold text-gray-900">
              {project.name}
            </h2>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <span className="text-sm text-gray-500">
                Twoje role:
              </span>

              {project.currentUserRoles.map((role) => (
                <ProjectRoleBadge
                  key={role}
                  role={role}
                />
              ))}
            </div>
          </div>

          <nav className="mt-4 space-y-1">
            {navigationItems.map((item) => (
              <NavLink
                key={item.path}
                end={item.path === ""}
                to={item.path}
                className={({ isActive }) =>
                  [
                    "flex items-center rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-blue-50 text-blue-700"
                      : "text-gray-700 hover:bg-gray-50 hover:text-gray-900",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
        </aside>

        {/* Content */}
        <main className="min-w-0">
          <Outlet context={{ project, onProjectUpdated: handleProjectUpdated }} />
        </main>
      </div>
    </div>
  );
}
