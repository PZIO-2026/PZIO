import { useEffect, useState } from "react";

import { useOutletContext } from "react-router-dom";

import { ApiError } from "../../../api/client";

import { fetchTasks } from "../api";

import type { ProjectDetail, WorkItem } from "../types";

import { hasProjectRole } from "../helpers/permissions";

import AddTaskModal from "../components/backlog/AddTaskModal";

// ============================================================
// Context
// ============================================================

interface OutletContext {
  project: ProjectDetail;
}

// ============================================================
// Helpers
// ============================================================

const PRIORITY_STYLES: Record<string, string> = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

// ============================================================
// Component
// ============================================================

export default function ProjectsBacklogPage() {
  const { project } = useOutletContext<OutletContext>();

  const canAddTasks = hasProjectRole(project.currentUserRoles, [
    "project_owner",
    "scrum_master",
    "developer",
    "maintainer",
  ]);

  const [tasks, setTasks] = useState<WorkItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);

  // ============================================================
  // Effects
  // ============================================================

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const response = await fetchTasks(project.projectId, { status: "Backlog" });

        if (cancelled) return;

        setTasks(response);
      } catch (err) {
        if (cancelled) return;

        setLoadError(err instanceof ApiError ? err.detail : "Nie udało się pobrać backlogu.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [project.projectId]);

  // ============================================================
  // Render
  // ============================================================

  return (
    <>
      <div className="space-y-6">
        <section className="rounded-2xl bg-white p-6 shadow">

          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Backlog</h1>
            {canAddTasks && (
              <button
                type="button"
                onClick={() => setIsAddModalOpen(true)}
                className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 cursor-pointer"
              >
                Dodaj element
              </button>
            )}
          </div>

          <span className="text-sm text-gray-500">Łącznie: {tasks.length}</span>

          {isLoading ? (
            <div className="py-10 text-center text-sm text-gray-500">Ładowanie backlogu...</div>
          ) : loadError !== null ? (
            <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{loadError}</div>
          ) : tasks.length === 0 ? (
            <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
              <p className="text-sm text-gray-500">Backlog jest pusty.</p>
            </div>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                    <th className="pb-2 pr-4">Tytuł</th>
                    <th className="pb-2 pr-4">Typ</th>
                    <th className="pb-2 pr-4">Priorytet</th>
                    <th className="pb-2">Story Points</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {tasks.map((task) => (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="py-3 pr-4 font-medium text-gray-900">{task.title}</td>
                      <td className="py-3 pr-4">
                        <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                          {task.type}
                        </span>
                      </td>
                      <td className="py-3 pr-4">
                        <span
                          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-600"}`}
                        >
                          {task.priority}
                        </span>
                      </td>
                      <td className="py-3 text-gray-600">
                        {task.storyPoints !== null ? task.storyPoints : <span className="text-gray-400">—</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      </div>

      <AddTaskModal
        isOpen={isAddModalOpen}
        onClose={() => setIsAddModalOpen(false)}
        projectId={project.projectId}
        onTaskCreated={(task) => setTasks((current) => [task, ...current])}
      />
    </>
  );
}
