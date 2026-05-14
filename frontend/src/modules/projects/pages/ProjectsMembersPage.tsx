// src/modules/projects/pages/ProjectsMembersPage.tsx

import { useEffect, useMemo, useState } from "react";

import {
  useOutletContext,
  useSearchParams,
} from "react-router-dom";

import ProjectRoleBadge from "../components/ProjectRoleBadge";

import AddProjectMemberModal from "../components/members/AddProjectMemberModal";
import EditProjectMemberModal from "../components/members/EditProjectMemberModal";

import { ApiError } from "../../../api/client";
import { useAuth } from "../../auth/hooks";

import {
  fetchProjectMembers,
  removeProjectMember,
} from "../api";

import type {
  ProjectDetail,
  ProjectMember,
  ProjectRole,
} from "../types";

import { hasProjectRole } from "../helpers/permissions";

// ============================================================
// Types
// ============================================================

interface OutletContext {
  project: ProjectDetail;
  refreshProject: () => Promise<void>;
}

// ============================================================
// Styles
// ============================================================

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

// ============================================================
// Component
// ============================================================

const PAGE_SIZE = 10;

export default function ProjectsMembersPage() {
  const { project, refreshProject } =
    useOutletContext<OutletContext>();
  const { user: currentUser } = useAuth();

  const canManageMembers = hasProjectRole(
    project.currentUserRoles,
    ["project_owner", "scrum_master"],
  );

  const [searchParams, setSearchParams] =
    useSearchParams();

  const [members, setMembers] = useState<ProjectMember[]>(
    [],
  );

  const [total, setTotal] = useState(0);

  const [isLoading, setIsLoading] = useState(true);

  const [loadError, setLoadError] = useState<
    string | null
  >(null);

  const [removeLoadingId, setRemoveLoadingId] =
    useState<number | null>(null);

  const [isAddModalOpen, setIsAddModalOpen] =
    useState(false);

  const [editingMember, setEditingMember] = useState<ProjectMember | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const page = Number(searchParams.get("page") ?? "1");

  const search = searchParams.get("search") ?? "";

  const role =
    (searchParams.get("role") as ProjectRole | null) ??
    "";

  const totalPages = Math.max(
    1,
    Math.ceil(total / PAGE_SIZE),
  );

  const filters = useMemo(
    () => ({
      page,
      size: PAGE_SIZE,
      search: search || undefined,
      role: role || undefined,
    }),
    [page, search, role],
  );

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoadError(null);
      setIsLoading(true);

      try {
        const response = await fetchProjectMembers(project.projectId, filters);

        if (cancelled) return;

        setMembers(response.items);
        setTotal(response.total);
      } catch (err) {
        if (cancelled) return;

        setLoadError(
          err instanceof ApiError
            ? err.detail
            : "Nie udało się pobrać członków projektu.",
        );
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
  }, [project.projectId, filters, refreshKey]);

  function updateFilters(next: {
    page?: number;
    search?: string;
    role?: string;
  }) {
    const params = new URLSearchParams(searchParams);

    if (next.search !== undefined) {
      if (next.search.length > 0) {
        params.set("search", next.search);
      } else {
        params.delete("search");
      }
    }

    if (next.role !== undefined) {
      if (next.role.length > 0) {
        params.set("role", next.role);
      } else {
        params.delete("role");
      }
    }

    params.set("page", String(next.page ?? 1));

    setSearchParams(params);
  }

  async function handleRemove(userId: number) {
    const confirmed = window.confirm(
      "Czy na pewno chcesz usunąć użytkownika z projektu?",
    );

    if (!confirmed) return;

    setRemoveLoadingId(userId);

    try {
      await removeProjectMember(
        project.projectId,
        userId,
      );

      setMembers((current) =>
        current.filter(
          (member) => member.userId !== userId,
        ),
      );

      setTotal((current) => Math.max(0, current - 1));

      if (currentUser !== null && userId === currentUser.userId) {
        await refreshProject();
      }
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.detail);
      } else {
        alert(
          "Nie udało się usunąć użytkownika z projektu.",
        );
      }
    } finally {
      setRemoveLoadingId(null);
    }
  }

  return (
    <>
      <div className="space-y-6">
        {/* Members list */}

        <section className="rounded-2xl bg-white p-6 shadow">
          <div className="flex justify-between">
            <h1 className="text-2xl font-bold text-gray-900">
              Członkowie projektu
            </h1>
            {canManageMembers && (
              <button
                type="button"
                onClick={() =>
                  setIsAddModalOpen(true)
                }
                className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700"
              >
                Dodaj użytkownika
              </button>
            )}

          </div>
         

          <div className="mb-6 flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
            <div className="grid gap-4 sm:grid-cols-2">
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Wyszukiwanie
                </label>

                <input
                  type="text"
                  value={search}
                  placeholder="Imię, nazwisko lub email..."
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
                <label className="mb-1 block text-sm font-medium text-gray-700">
                  Rola
                </label>

                <select
                  value={role}
                  className={inputClass}
                  onChange={(e) =>
                    updateFilters({
                      role: e.target.value,
                      page: 1,
                    })
                  }
                >
                  <option value="">Wszystkie</option>

                  <option value="project_owner">
                    Project Owner
                  </option>

                  <option value="scrum_master">
                    Scrum Master
                  </option>

                  <option value="developer">
                    Developer
                  </option>
                  
                  <option value="qa">
                    QA Engineer
                  </option>

                  <option value="maintainer">
                    Maintainer
                  </option>

                </select>
              </div>
            </div>

            <div className="text-sm text-gray-500">
              Łącznie użytkowników:{" "}
              <span className="font-medium">
                {total}
              </span>
            </div>
          </div>

          {isLoading ? (
              <div className="py-10 text-center text-sm text-gray-500">
                Ładowanie członków projektu...
              </div>
            ) : loadError !== null ? (
              <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
                {loadError}
              </div>
            ) : members.length === 0 ? (
              <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
                <p className="text-sm text-gray-500">
                  Brak użytkowników w projekcie.
                </p>
              </div>
            ) : (
              <>
                <div className="overflow-hidden rounded-xl border border-gray-200">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Użytkownik
                        </th>

                        <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Role
                        </th>

                        <th className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wide text-gray-500">
                          Dołączono
                        </th>

                        {canManageMembers && (
                          <th className="px-6 py-3 text-right text-xs font-semibold uppercase tracking-wide text-gray-500">
                            Akcje
                          </th>
                        )}
                      </tr>
                    </thead>

                    <tbody className="divide-y divide-gray-200 bg-white">
                      {members.map((member) => (
                        <tr key={member.userId}>
                          <td className="px-6 py-4">
                            <div>
                              <p className="font-medium text-gray-900">
                                {member.firstName} {member.lastName}
                              </p>

                              <p className="mt-1 text-sm text-gray-500">
                                {member.email}
                              </p>
                            </div>
                          </td>

                          <td className="px-6 py-4">
                            <div className="flex flex-wrap gap-2">
                              {member.roles.map((roleValue) => (
                                <ProjectRoleBadge
                                  key={roleValue}
                                  role={roleValue}
                                />
                              ))}
                            </div>
                          </td>

                          <td className="px-6 py-4 text-sm text-gray-500">
                            {new Date(
                              member.joinedAt,
                            ).toLocaleDateString("pl-PL")}
                          </td>

                          {canManageMembers && (
                            <td className="px-6 py-4 text-right">
                              <div className="flex justify-end gap-2">
                                <button
                                  type="button"
                                  onClick={() => setEditingMember(member)}
                                  className="rounded-md border border-blue-200 px-3 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50"
                                >
                                  Edytuj
                                </button>
                                
                                <button
                                  type="button"
                                  disabled={
                                    removeLoadingId === member.userId
                                  }
                                  onClick={() =>
                                    handleRemove(member.userId)
                                  }
                                  className="rounded-md border border-red-200 px-3 py-2 text-sm font-medium text-red-700 hover:bg-red-50 disabled:cursor-not-allowed disabled:opacity-60"
                                >
                                  {removeLoadingId === member.userId
                                    ? "Usuwanie..."
                                    : "Usuń"}
                                </button>
                              </div>
                            </td>
                          )}
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
                      onClick={() =>
                        updateFilters({
                          page: page - 1,
                        })
                      }
                      className="rounded-md border border-gray-300 px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      Poprzednia
                    </button>

                    <button
                      type="button"
                      disabled={page >= totalPages}
                      onClick={() =>
                        updateFilters({
                          page: page + 1,
                        })
                      }
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

      <AddProjectMemberModal
        isOpen={isAddModalOpen}
        onClose={() =>
          setIsAddModalOpen(false)
        }
        projectId={project.projectId}
        onMemberAdded={() => {
          setRefreshKey((prev) => prev + 1);
        }}
      />
      {editingMember && (
        <EditProjectMemberModal
          projectId={project.projectId}
          userId={editingMember.userId}
          email={editingMember.email}
          currentRoles={editingMember.roles}
          onClose={() => setEditingMember(null)}
          onSuccess={() => {
            setRefreshKey((prev) => prev + 1);
            if (
              currentUser !== null &&
              editingMember.userId === currentUser.userId
            ) {
              refreshProject();
            }
          }}
        />
      )}
    </>
  );
}