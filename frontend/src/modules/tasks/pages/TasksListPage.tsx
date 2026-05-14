import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { fetchProjects, fetchProjectMembers, fetchTasks } from "../../projects/api";
import type { WorkItem } from "../../projects/types";

const AVATAR_COLORS = [
  "bg-blue-500",
  "bg-purple-500",
  "bg-green-600",
  "bg-orange-500",
  "bg-pink-500",
  "bg-teal-500",
  "bg-indigo-500",
  "bg-rose-500",
];

interface AssigneeInfo { firstName: string; lastName: string }

function AssigneeCell({ userId, map }: { userId: number | null; map: Map<number, AssigneeInfo> }) {
  if (userId === null) return <span className="text-sm text-gray-400">—</span>;
  const person = map.get(userId);
  if (!person) return <span className="text-sm text-gray-400">—</span>;

  const initials = `${person.firstName[0]}${person.lastName[0]}`.toUpperCase();
  const color = AVATAR_COLORS[userId % AVATAR_COLORS.length];

  return (
    <div className="flex items-center gap-2">
      <span
        className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold text-white ${color}`}
      >
        {initials}
      </span>
      <span className="text-sm text-gray-900">{person.firstName} {person.lastName}</span>
    </div>
  );
}

const inputClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const selectClass =
  "block rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const PAGE_SIZE = 20;

const STATUS_STYLES: Record<string, string> = {
  ToDo: "bg-blue-100 text-blue-700",
  InProgress: "bg-yellow-100 text-yellow-700",
  Done: "bg-green-100 text-green-700",
};

const STATUS_LABELS: Record<string, string> = {
  ToDo: "Do zrobienia",
  InProgress: "W trakcie",
  Done: "Ukończone",
};

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

export default function TasksListPage() {
  const [searchParams, setSearchParams] = useSearchParams();

  const [allTasks, setAllTasks] = useState<WorkItem[]>([]);
  const [assigneeMap, setAssigneeMap] = useState<Map<number, AssigneeInfo>>(new Map());
  const [projectNames, setProjectNames] = useState<Map<number, string>>(new Map());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey] = useState(0);

  const page = Number(searchParams.get("page") ?? "1");
  const search = searchParams.get("search") ?? "";
  const status = searchParams.get("status") ?? "";
  const priority = searchParams.get("priority") ?? "";

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const firstPage = await fetchProjects({ size: 100, page: 1 });
        if (cancelled) return;

        const totalPages = Math.ceil(firstPage.total / 100);
        const rest = totalPages > 1
          ? await Promise.all(
              Array.from({ length: totalPages - 1 }, (_, i) =>
                fetchProjects({ size: 100, page: i + 2 }),
              ),
            )
          : [];
        if (cancelled) return;

        const projects = [firstPage, ...rest].flatMap((p) => p.items);

        const nameMap = new Map<number, string>();
        for (const project of projects) {
          nameMap.set(project.projectId, project.name);
        }

        const taskArrays = await Promise.all(projects.map((p) => fetchTasks(p.projectId)));
        if (cancelled) return;

        const tasks = taskArrays.flat().sort(
          (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime(),
        );

        setAllTasks(tasks);
        setProjectNames(nameMap);

        const projectsWithAssignees = projects.filter((p) =>
          tasks.some((t) => t.projectId === p.projectId && t.assigneeId !== null),
        );

        const memberPages = await Promise.all(
          projectsWithAssignees.map((p) => fetchProjectMembers(p.projectId, { size: 100 })),
        );
        if (cancelled) return;

        const memberMap = new Map<number, AssigneeInfo>();
        for (const mp of memberPages) {
          for (const m of mp.items) {
            memberMap.set(m.userId, { firstName: m.firstName, lastName: m.lastName });
          }
        }
        setAssigneeMap(memberMap);
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError
            ? err.detail
            : "Nie udało się pobrać listy zadań.",
        );
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [refreshKey]);

  const filteredTasks = useMemo(() => {
    return allTasks.filter((task) => {
      if (search && !task.title.toLowerCase().includes(search.toLowerCase())) return false;
      if (status && task.status !== status) return false;
      if (priority && task.priority.toLowerCase() !== priority.toLowerCase()) return false;
      return true;
    });
  }, [allTasks, search, status, priority]);

  function updateFilters(next: {
    search?: string;
    status?: string;
    priority?: string;
    page?: number;
  }) {
    const params = new URLSearchParams(searchParams);

    if (next.search !== undefined) {
      next.search.length > 0 ? params.set("search", next.search) : params.delete("search");
    }
    if (next.status !== undefined) {
      next.status.length > 0 ? params.set("status", next.status) : params.delete("status");
    }
    if (next.priority !== undefined) {
      next.priority.length > 0 ? params.set("priority", next.priority) : params.delete("priority");
    }

    params.set("page", String(next.page ?? 1));
    setSearchParams(params);
  }

  const pageCount = Math.max(1, Math.ceil(filteredTasks.length / PAGE_SIZE));
  const tasks = filteredTasks.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-10">
      <header>
        <h1 className="text-3xl font-bold text-gray-900">Zadania</h1>
        <p className="mt-1 text-sm text-gray-600">
          Wszystkie zadania z projektów, do których masz dostęp.
        </p>
      </header>

      <section className="rounded-xl bg-white p-6 shadow">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="grid gap-4 sm:grid-cols-3">
            <div>
              <label
                htmlFor="task-search"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Wyszukiwarka
              </label>
              <input
                id="task-search"
                type="text"
                value={search}
                placeholder="Szukaj po tytule..."
                className={inputClass}
                onChange={(e) => updateFilters({ search: e.target.value, page: 1 })}
              />
            </div>

            <div>
              <label
                htmlFor="task-status"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Status
              </label>
              <select
                id="task-status"
                value={status}
                className={selectClass}
                onChange={(e) => updateFilters({ status: e.target.value, page: 1 })}
              >
                <option value="">Wszystkie</option>
                <option value="ToDo">Do zrobienia</option>
                <option value="InProgress">W trakcie</option>
                <option value="Done">Ukończone</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="task-priority"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Priorytet
              </label>
              <select
                id="task-priority"
                value={priority}
                className={selectClass}
                onChange={(e) => updateFilters({ priority: e.target.value, page: 1 })}
              >
                <option value="">Wszystkie</option>
                <option value="High">Wysoki</option>
                <option value="Medium">Średni</option>
                <option value="Low">Niski</option>
              </select>
            </div>
          </div>

          <div className="text-sm text-gray-500">
            Łącznie zadań: <span className="font-medium">{filteredTasks.length}</span>
          </div>
        </div>

        {isLoading ? (
          <div className="py-10 text-center text-sm text-gray-500">
            Ładowanie zadań...
          </div>
        ) : error !== null ? (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : tasks.length === 0 ? (
          <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
            <p className="text-sm text-gray-500">
              Nie znaleziono zadań spełniających kryteria.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto min-w-[300px] rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Tytuł
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Projekt
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Priorytet
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Typ
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      SP
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Przypisano
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Utworzono
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 bg-white">
                  {tasks.map((task) => (
                    <tr key={task.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4">
                        <Link
                          to={`/tasks/${task.id}`}
                          className="font-medium text-blue-600 hover:text-blue-800 hover:underline"
                        >
                          {task.title}
                        </Link>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        <Link
                          to={`/projects/${task.projectId}`}
                          className="block max-w-[160px] truncate hover:text-blue-600 hover:underline"
                          title={projectNames.get(task.projectId)}
                        >
                          {projectNames.get(task.projectId) ?? `#${task.projectId}`}
                        </Link>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${STATUS_STYLES[task.status] ?? "bg-gray-100 text-gray-700"}`}
                        >
                          {STATUS_LABELS[task.status] ?? task.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-700"}`}
                        >
                          {PRIORITY_LABELS[task.priority] ?? task.priority}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700">
                          {task.type}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {task.storyPoints ?? "—"}
                      </td>
                      <td className="px-6 py-4">
                        <AssigneeCell userId={task.assigneeId} map={assigneeMap} />
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(task.createdAt).toLocaleDateString("pl-PL")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Strona {page} z {pageCount}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => updateFilters({ page: page - 1 })}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Poprzednia
                </button>
                <button
                  type="button"
                  disabled={page >= pageCount}
                  onClick={() => updateFilters({ page: page + 1 })}
                  className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Następna
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </div>
  );
}
