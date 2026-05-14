// src/modules/projects/pages/ProjectsListPage.tsx

import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { useAuth } from "../../auth/hooks";
import { fetchProjects } from "../api";
import ProjectRoleBadge from "../components/ProjectRoleBadge";
import Modal from "../components/Modal";
import type { Project, ProjectStatus } from "../types";
import CreateProjectModal from "../components/projects/CreateProjectModal";

const inputClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const selectClass =
  "block rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const PAGE_SIZE = 10;

const statusLabels: Record<ProjectStatus, string> = {
  active: "Aktywny",
  archived: "Zarchiwizowany",
};

export default function ProjectsListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();
  const canCreateProject =
    user?.role === "Manager" || user?.role === "Administrator";

  const [projects, setProjects] = useState<Project[]>([]);
  const [total, setTotal] = useState(0);

  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);

  const [refreshKey, setRefreshKey] = useState(0);

  const page = Number(searchParams.get("page") ?? "1");
  const search = searchParams.get("search") ?? "";
  const status = (searchParams.get("status") as ProjectStatus | null) ?? "";

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const filters = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      search: search || undefined,
      status: status || undefined,
      sortBy: "created_at",
      sortDirection: "desc" as const,
    }),
    [page, search, status],
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetchProjects(filters);

        if (cancelled) return;

        setProjects(response.items);
        setTotal(response.total);
      } catch (err) {
        if (cancelled) return;

        if (err instanceof ApiError) {
          setError("Nie udało się pobrać listy projektów.");
        } else {
          setError("Nie udało się połączyć z serwerem. Spróbuj ponownie.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [filters, refreshKey]);

  function updateFilters(next: {
    search?: string;
    status?: string;
    page?: number;
  }) {
    const params = new URLSearchParams(searchParams);

    if (next.search !== undefined) {
      if (next.search.length > 0) {
        params.set("search", next.search);
      } else {
        params.delete("search");
      }
    }

    if (next.status !== undefined) {
      if (next.status.length > 0) {
        params.set("status", next.status);
      } else {
        params.delete("status");
      }
    }

    params.set("page", String(next.page ?? 1));

    setSearchParams(params);
  }

  function handleProjectCreated() {
    setIsCreateModalOpen(false);
    setRefreshKey((prev) => prev + 1);
  }

  return (
    <div className="mx-auto max-w-7xl space-y-6 px-4 py-10">
      <header className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Projekty</h1>
          <p className="mt-1 text-sm text-gray-600">
            Zarządzanie projektami, sprintami i członkami zespołów.
          </p>
        </div>
      </header>

      <section className="rounded-xl bg-white p-6 shadow">
        <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <label
                htmlFor="project-search"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Wyszukiwarka
              </label>

              <input
                id="project-search"
                type="text"
                value={search}
                placeholder="Szukaj po nazwie projektu..."
                className={inputClass}
                onChange={(e) =>
                  updateFilters({
                    search: e.target.value,
                    page: 1,
                  })
                }
              />
            </div>

            <div>
              <label
                htmlFor="project-status"
                className="mb-1 block text-sm font-medium text-gray-700"
              >
                Status
              </label>

              <select
                id="project-status"
                value={status}
                className={selectClass}
                onChange={(e) =>
                  updateFilters({
                    status: e.target.value,
                    page: 1,
                  })
                }
              >
                <option value="">Wszystkie</option>
                <option value="active">Aktywne</option>
                <option value="archived">Zarchiwizowane</option>
              </select>
            </div>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <div className="text-sm text-gray-500">
              Łącznie projektów: <span className="font-medium">{total}</span>
            </div>

            {canCreateProject && (
              <button
                type="button"
                onClick={() => setIsCreateModalOpen(true)}
                className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
              >
                Dodaj projekt
              </button>
            )}
          </div>
        </div>

        {isLoading ? (
          <div className="py-10 text-center text-sm text-gray-500">
            Ładowanie projektów...
          </div>
        ) : error !== null ? (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {error}
          </div>
        ) : projects.length === 0 ? (
          <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
            <p className="text-sm text-gray-500">
              Nie znaleziono projektów spełniających kryteria.
            </p>
          </div>
        ) : (
          <>
            <div className="overflow-y-auto min-w-[300px] rounded-lg border border-gray-200">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Projekt
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Status
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Twoje role
                    </th>

                    <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Utworzono
                    </th>

                    <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                      Akcje
                    </th>
                  </tr>
                </thead>

                <tbody className="divide-y divide-gray-200 bg-white">
                  {projects.map((project) => (
                    <tr key={project.projectId}>
                      <td className="px-6 py-4">
                        <div>
                          <p className="font-medium text-gray-900">
                            {project.name}
                          </p>

                          <p className="mt-1 line-clamp-2 text-sm text-gray-500">
                            {project.description || "Brak opisu projektu."}
                          </p>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span
                          className={
                            project.status === "active"
                              ? "inline-flex rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700"
                              : "inline-flex rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700"
                          }
                        >
                          {statusLabels[project.status]}
                        </span>
                      </td>

                      <td className="px-6 py-4">
                        <div className="flex flex-wrap gap-2">
                          {project.currentUserRoles.map((role) => (
                            <ProjectRoleBadge key={role} role={role} />
                          ))}
                        </div>
                      </td>

                      <td className="px-6 py-4 text-sm text-gray-500">
                        {new Date(project.createdAt).toLocaleDateString(
                          "pl-PL",
                        )}
                      </td>

                      <td className="px-6 py-4 text-right">
                        <Link
                          to={`/projects/${project.projectId}`}
                          className="inline-flex items-center rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
                        >
                          Szczegóły
                        </Link>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="mt-6 flex items-center justify-between">
              <p className="text-sm text-gray-500">
                Strona {page} z {totalPages}
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
                  disabled={page >= totalPages}
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

      <Modal
        title="Dodaj projekt"
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
      >
        <CreateProjectModal
          variant="modal"
          onCreated={handleProjectCreated}
        />
      </Modal>
    </div>
  );
}