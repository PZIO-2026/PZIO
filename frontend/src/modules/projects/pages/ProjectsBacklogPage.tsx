import { useEffect, useMemo, useState } from "react";
import { Link, useOutletContext } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { useConfirm } from "../../../components/ConfirmProvider";
import { deleteTask, fetchSprints, fetchTasks } from "../api";
import AssignSprintModal from "../components/backlog/AssignSprintModal";
import AddTaskModal from "../components/backlog/AddTaskModal";
import EditTaskModal from "../components/backlog/EditTaskModal";
import { hasProjectRole } from "../helpers/permissions";
import type { ProjectDetail, Sprint, WorkItem } from "../types";

interface OutletContext {
  project: ProjectDetail;
}

const PRIORITY_STYLES: Record<string, string> = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

const PRIORITY_LABELS: Record<string, string> = {
  High: "Wysoki",
  Medium: "Średni",
  Low: "Niski",
};

export default function ProjectsBacklogPage() {
  const { project } = useOutletContext<OutletContext>();
  const confirm = useConfirm();

  const canManageTasks = hasProjectRole(project.currentUserRoles, [
    "project_owner",
    "scrum_master",
    "developer",
    "maintainer",
  ]);

  const [tasks, setTasks] = useState<WorkItem[]>([]);
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [editingTask, setEditingTask] = useState<WorkItem | null>(null);
  const [assigningTask, setAssigningTask] = useState<WorkItem | null>(null);
  const [sprintFilter, setSprintFilter] = useState<"all" | "none" | number>("all");

  const filteredTasks = useMemo(() => {
    if (sprintFilter === "all") return tasks;
    if (sprintFilter === "none") return tasks.filter((task) => task.sprintId === null);
    return tasks.filter((task) => task.sprintId === sprintFilter);
  }, [tasks, sprintFilter]);

  function getDescendantIds(rootTaskId: number): number[] {
    const descendantIds: number[] = [];
    let pendingParentIds = [rootTaskId];

    while (pendingParentIds.length > 0) {
      const currentChildren = tasks
        .filter((task) => pendingParentIds.includes(task.parentId ?? -1))
        .map((task) => task.id);
      if (currentChildren.length === 0) break;
      descendantIds.push(...currentChildren);
      pendingParentIds = currentChildren;
    }

    return descendantIds;
  }

  async function reloadBacklog() {
    try {
      const [taskResponse, sprintResponse] = await Promise.all([
        fetchTasks(project.projectId, { status: "ToDo" }),
        fetchSprints(project.projectId),
      ]);
      setTasks(taskResponse);
      setSprints(sprintResponse);
    } catch (err) {
      alert(err instanceof ApiError ? err.detail : "Nie udało się odświeżyć backlogu.");
    }
  }

  async function handleDelete(taskId: number) {
    const descendantIds = getDescendantIds(taskId);
    const confirmed = await confirm(
      descendantIds.length > 0
        ? `Usunięcie tego zadania usunie też ${descendantIds.length} zadań podrzędnych. Czy kontynuować?`
        : "Czy na pewno chcesz usunąć zadanie?",
    );
    if (!confirmed) return;

    try {
      await deleteTask(taskId);
      const idsToRemove = new Set([taskId, ...descendantIds]);
      setTasks((current) => current.filter((task) => !idsToRemove.has(task.id)));
    } catch (err) {
      alert(err instanceof ApiError ? err.detail : "Nie udało się usunąć zadania.");
    }
  }

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const [taskResponse, sprintResponse] = await Promise.all([
          fetchTasks(project.projectId, { status: "ToDo" }),
          fetchSprints(project.projectId),
        ]);

        if (cancelled) return;
        setTasks(taskResponse);
        setSprints(sprintResponse);
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

  return (
    <>
      <div className="space-y-6">
        <section className="rounded-2xl bg-white p-6 shadow">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Backlog</h1>
            {canManageTasks && (
              <button
                type="button"
                onClick={() => setIsAddModalOpen(true)}
                className="cursor-pointer rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700"
              >
                Dodaj element
              </button>
            )}
          </div>

          <div className="mt-3 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <span className="text-sm text-gray-500">
              Wyświetlane: {filteredTasks.length} / {tasks.length}
            </span>
            <div className="flex items-center gap-2">
              <label htmlFor="sprint-filter" className="shrink-0 text-sm text-gray-600">
                Filtruj sprint:
              </label>
              <select
                id="sprint-filter"
                value={sprintFilter}
                onChange={(event) => {
                  const value = event.target.value;
                  if (value === "all") setSprintFilter("all");
                  else if (value === "none") setSprintFilter("none");
                  else setSprintFilter(Number(value));
                }}
                className="rounded-md border border-gray-300 px-3 py-1.5 text-sm text-gray-700 focus:border-blue-400 focus:outline-none"
              >
                <option value="all">Wszystkie</option>
                <option value="none">Bez sprintu</option>
                {sprints.map((sprint) => (
                  <option key={sprint.sprintId} value={sprint.sprintId}>
                    {sprint.name}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {isLoading ? (
            <div className="py-10 text-center text-sm text-gray-500">Ładowanie backlogu...</div>
          ) : loadError !== null ? (
            <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{loadError}</div>
          ) : filteredTasks.length === 0 ? (
            <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
              <p className="text-sm text-gray-500">
                {tasks.length === 0 ? "Backlog jest pusty." : "Brak zadań pasujących do filtra."}
              </p>
            </div>
          ) : (
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                    <th className="pb-2 pr-4">Tytuł</th>
                    <th className="pb-2 pr-4">Typ</th>
                    <th className="pb-2 pr-4">Priorytet</th>
                    <th className="pb-2 pr-4">Story Points</th>
                    <th className="pb-2 pr-4">Sprint</th>
                    {canManageTasks && <th className="pb-2" />}
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredTasks.map((task) => {
                    const sprint = sprints.find((item) => item.sprintId === task.sprintId);
                    return (
                      <tr key={task.id} className="hover:bg-gray-50">
                        <td className="py-3 pr-4 font-medium text-gray-900">
                          <Link to={`/tasks/${task.id}`} className="text-blue-600 hover:underline">
                            {task.title}
                          </Link>
                          {task.parentId !== null && (
                            <span className="ml-2 text-xs text-gray-400">(#{task.parentId})</span>
                          )}
                        </td>
                        <td className="py-3 pr-4">
                          <span className="rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                            {task.type}
                          </span>
                        </td>
                        <td className="py-3 pr-4">
                          <span
                            className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-600"}`}
                          >
                            {PRIORITY_LABELS[task.priority] ?? task.priority}
                          </span>
                        </td>
                        <td className="py-3 pr-4 text-gray-600">
                          {task.storyPoints !== null ? task.storyPoints : <span className="text-gray-400">—</span>}
                        </td>
                        <td className="py-3 pr-4 text-gray-600">
                          {sprint ? <span className="text-gray-800">{sprint.name}</span> : <span className="text-gray-400">—</span>}
                        </td>
                        {canManageTasks && (
                          <td className="py-3 text-right">
                            <div className="flex justify-end gap-2">
                              <button
                                type="button"
                                onClick={() => setAssigningTask(task)}
                                className="cursor-pointer rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                              >
                                Przypisz
                              </button>
                              <button
                                type="button"
                                onClick={() => setEditingTask(task)}
                                className="cursor-pointer rounded-md border border-blue-200 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
                              >
                                Edytuj
                              </button>
                              <button
                                type="button"
                                onClick={() => handleDelete(task.id)}
                                className="cursor-pointer rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50"
                              >
                                Usuń
                              </button>
                            </div>
                          </td>
                        )}
                      </tr>
                    );
                  })}
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

      <EditTaskModal
        isOpen={editingTask !== null}
        onClose={() => setEditingTask(null)}
        task={editingTask}
        projectId={project.projectId}
        onTaskUpdated={(updated) => {
          void updated;
          void reloadBacklog().finally(() => setEditingTask(null));
        }}
      />

      <AssignSprintModal
        isOpen={assigningTask !== null}
        onClose={() => setAssigningTask(null)}
        task={assigningTask}
        sprints={sprints}
        childCount={assigningTask ? getDescendantIds(assigningTask.id).length : 0}
        onAssigned={(updated) => {
          void updated;
          void reloadBacklog().finally(() => setAssigningTask(null));
        }}
      />
    </>
  );
}
