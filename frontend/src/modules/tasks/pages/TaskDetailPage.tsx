import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { fetchTask } from "../api";
import { useAuth } from "../../auth/hooks";
import {
  deleteTask,
  fetchProjectMembers,
  fetchSprints,
  updateTask,
  updateTaskStatus,
} from "../../projects/api";
import type { ProjectMember, Sprint, WorkItem } from "../../projects/types";
import EditTaskModal from "../../projects/components/backlog/EditTaskModal";

const selectClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm text-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

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


export default function TaskDetailPage() {
  const { taskId } = useParams<{ taskId: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [task, setTask] = useState<WorkItem | null>(null);
  const [parentTask, setParentTask] = useState<WorkItem | null>(null);
  const [members, setMembers] = useState<ProjectMember[]>([]);
  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) return;
    let cancelled = false;
    const id = Number(taskId);

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const loadedTask = await fetchTask(id);
        if (cancelled) return;

        const [loadedMembers, loadedSprints, loadedParent] = await Promise.all([
          fetchProjectMembers(loadedTask.projectId),
          fetchSprints(loadedTask.projectId),
          loadedTask.parentId !== null ? fetchTask(loadedTask.parentId) : Promise.resolve(null),
        ]);

        if (cancelled) return;
        setTask(loadedTask);
        setParentTask(loadedParent);
        setMembers(loadedMembers.items);
        setSprints(loadedSprints);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.detail
            : "Nie udało się pobrać szczegółów zadania.",
        );
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [taskId]);

  async function handleStatusChange(newStatus: string) {
    if (!task) return;
    try {
      const updated = await updateTaskStatus(task.id, newStatus);
      setTask(updated);
    } catch {
      // status stays unchanged on error
    }
  }

  async function handleAssigneeChange(assigneeId: number | null) {
    if (!task) return;
    try {
      const updated = await updateTask(task.id, { assigneeId });
      setTask(updated);
    } catch {
      // assignee stays unchanged on error
    }
  }

  async function handleDelete() {
    if (!task) return;
    if (!window.confirm("Czy na pewno chcesz usunąć to zadanie? Tej operacji nie można cofnąć.")) return;
    setIsDeleting(true);
    setDeleteError(null);
    try {
      await deleteTask(task.id);
      navigate("/tasks");
    } catch (err) {
      setDeleteError(
        err instanceof ApiError ? err.detail : "Nie udało się usunąć zadania.",
      );
      setIsDeleting(false);
    }
  }

  if (isLoading) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="py-20 text-center text-sm text-gray-500">Ładowanie zadania...</div>
      </div>
    );
  }

  if (error || !task) {
    return (
      <div className="mx-auto max-w-7xl px-4 py-10">
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {error ?? "Nie znaleziono zadania."}
        </div>
        <Link to="/tasks" className="mt-4 inline-block text-sm text-blue-600 hover:underline">
          ← Wróć do wszystkich zadań
        </Link>
      </div>
    );
  }

  const sprint = sprints.find((s) => s.sprintId === task.sprintId);
  const sprintName = sprint?.name ?? "—";

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-10">
      {/* Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <Link
          to="/tasks"
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          ← Wszystkie zadania
        </Link>
        <div className="flex gap-3">
          <button
            type="button"
            onClick={() => setIsEditModalOpen(true)}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Edytuj zadanie
          </button>
          <button
            type="button"
            onClick={handleDelete}
            disabled={isDeleting}
            className="rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isDeleting ? "Usuwanie..." : "Usuń zadanie"}
          </button>
        </div>
      </div>

      {deleteError && (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {deleteError}
        </div>
      )}

      {/* Two-column layout */}
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        {/* Left column — title + description */}
        <div className="space-y-6 rounded-xl bg-white p-6 shadow">
          <div>
            <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
              {task.type}
            </span>
          </div>
          <h1 className="flex flex-wrap items-baseline gap-3 text-2xl font-bold text-gray-900">
            {task.title}
            <span className="text-base font-normal text-gray-400">#{task.id}</span>
          </h1>
          <div>
            <h2 className="mb-2 text-sm font-semibold uppercase tracking-wide text-gray-500">
              Opis
            </h2>
            {task.description ? (
              <p className="whitespace-pre-wrap text-sm text-gray-700">
                {task.description}
              </p>
            ) : (
              <p className="text-sm italic text-gray-400">Brak opisu.</p>
            )}
          </div>
        </div>

        {/* Right column — attributes */}
        <div className="rounded-xl bg-white p-6 shadow">
          <h2 className="mb-4 text-sm font-semibold uppercase tracking-wide text-gray-500">
            Szczegóły
          </h2>

          <dl className="space-y-4">
            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Status</dt>
              <dd>
                <select
                  value={task.status}
                  className={selectClass}
                  onChange={(e) => handleStatusChange(e.target.value)}
                >
                  <option value="ToDo">Do zrobienia</option>
                  <option value="InProgress">W trakcie</option>
                  <option value="Done">Ukończone</option>
                </select>
              </dd>
            </div>

            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Priorytet</dt>
              <dd>
                <span
                  className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-700"}`}
                >
                  {PRIORITY_LABELS[task.priority] ?? task.priority}
                </span>
              </dd>
            </div>

            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Story Points</dt>
              <dd className="text-sm text-gray-900">
                {task.storyPoints !== null ? task.storyPoints : "—"}
              </dd>
            </div>

            <div>
              <dt className="mb-2 text-xs font-medium text-gray-500">Przypisano do</dt>
              <dd className="space-y-2">
                <select
                  value={task.assigneeId?.toString() ?? ""}
                  className={selectClass}
                  onChange={(e) =>
                    handleAssigneeChange(e.target.value === "" ? null : Number(e.target.value))
                  }
                >
                  <option value="">Nieprzypisane</option>
                  {members.map((m) => (
                    <option key={m.userId} value={m.userId.toString()}>
                      {m.firstName} {m.lastName}
                    </option>
                  ))}
                </select>
                {user && task.assigneeId !== user.userId && (
                  <button
                    type="button"
                    onClick={() => handleAssigneeChange(user.userId)}
                    className="text-xs text-blue-600 hover:text-blue-800 hover:underline"
                  >
                    Przypisz do mnie
                  </button>
                )}
              </dd>
            </div>

            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Sprint</dt>
              <dd className="text-sm text-gray-900">{sprintName}</dd>
            </div>

            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Projekt</dt>
              <dd>
                <Link
                  to={`/projects/${task.projectId}`}
                  className="text-sm text-blue-600 hover:underline"
                >
                  Projekt #{task.projectId}
                </Link>
              </dd>
            </div>

            {task.parentId !== null && (
              <div>
                <dt className="mb-1 text-xs font-medium text-gray-500">
                  Zadanie nadrzędne
                </dt>
                <dd>
                  <Link
                    to={`/tasks/${task.parentId}`}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {parentTask ? parentTask.title : `#${task.parentId}`}
                  </Link>
                </dd>
              </div>
            )}

            <div className="border-t border-gray-100 pt-4">
              <dt className="mb-1 text-xs font-medium text-gray-500">Utworzono</dt>
              <dd className="text-sm text-gray-500">
                {new Date(task.createdAt).toLocaleDateString("pl-PL", {
                  year: "numeric",
                  month: "long",
                  day: "numeric",
                })}
              </dd>
            </div>

            <div>
              <dt className="mb-1 text-xs font-medium text-gray-500">Zaktualizowano</dt>
              <dd className="text-sm text-gray-500">
                {task.updatedAt
                  ? new Date(task.updatedAt).toLocaleDateString("pl-PL", {
                      year: "numeric",
                      month: "long",
                      day: "numeric",
                    })
                  : "—"}
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <EditTaskModal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        task={task}
        projectId={task.projectId}
        onTaskUpdated={(updated) => {
          setTask(updated);
          setIsEditModalOpen(false);
        }}
      />
    </div>
  );
}
