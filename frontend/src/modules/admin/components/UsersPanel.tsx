import { useEffect, useState } from "react";

import { ApiError } from "../../../api/client";
import { useAuth } from "../../auth/hooks";
import type { User, UserRole } from "../../auth/types";
import { fetchUsers, updateUserRole } from "../api";

const PAGE_SIZE = 50;

const ROLE_OPTIONS: { value: UserRole; label: string }[] = [
  { value: "Guest", label: "Gość" },
  { value: "TeamMember", label: "Członek zespołu" },
  { value: "Manager", label: "Manager" },
  { value: "Administrator", label: "Administrator" },
];

const inputClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

function formatFullName(user: User): string {
  return `${user.firstName} ${user.lastName}`.trim();
}

export default function UsersPanel() {
  const { user: currentUser } = useAuth();

  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [appliedSearch, setAppliedSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [pendingUserId, setPendingUserId] = useState<number | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchUsers({ page, size: PAGE_SIZE, search: appliedSearch || undefined })
      .then((response) => {
        if (cancelled) return;
        setUsers(response.items);
        setTotal(response.total);
        setLoadError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(
          err instanceof ApiError ? err.detail : "Nie udało się pobrać listy użytkowników.",
        );
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [page, appliedSearch]);

  function handleSearchSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setPage(1);
    setAppliedSearch(searchInput.trim());
  }

  async function handleRoleChange(target: User, newRole: UserRole) {
    if (newRole === target.role) return;

    setActionError(null);
    setActionSuccess(null);
    setPendingUserId(target.userId);

    const previousRole = target.role;
    setUsers((current) =>
      current.map((u) => (u.userId === target.userId ? { ...u, role: newRole } : u)),
    );

    try {
      const updated = await updateUserRole(target.userId, newRole);
      setUsers((current) => current.map((u) => (u.userId === updated.userId ? updated : u)));
      setActionSuccess(`Zmieniono rolę użytkownika ${target.email} na ${roleLabel(updated.role)}.`);
    } catch (err) {
      setUsers((current) =>
        current.map((u) => (u.userId === target.userId ? { ...u, role: previousRole } : u)),
      );
      if (err instanceof ApiError) {
        setActionError(err.detail);
      } else {
        setActionError("Nie udało się zmienić roli użytkownika. Spróbuj ponownie.");
      }
    } finally {
      setPendingUserId(null);
    }
  }

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-2 text-xl font-bold text-gray-900">Użytkownicy</h2>
      <p className="mb-4 text-sm text-gray-600">
        Lista wszystkich kont w systemie. Możesz zmienić rolę dowolnemu użytkownikowi poza sobą.
      </p>

      <form onSubmit={handleSearchSubmit} className="mb-4 flex gap-2" noValidate>
        <input
          type="search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          placeholder="Szukaj po e-mailu lub nazwisku"
          aria-label="Szukaj użytkownika"
          className={inputClass}
        />
        <button
          type="submit"
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          Szukaj
        </button>
      </form>

      {actionError !== null && (
        <p className="mb-3 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{actionError}</p>
      )}
      {actionSuccess !== null && (
        <p className="mb-3 rounded-md bg-green-50 px-3 py-2 text-sm text-green-800">
          {actionSuccess}
        </p>
      )}

      {isLoading ? (
        <p className="text-sm text-gray-500">Ładowanie...</p>
      ) : loadError !== null ? (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{loadError}</p>
      ) : users.length === 0 ? (
        <p className="text-sm text-gray-500">Brak użytkowników pasujących do wyszukiwania.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead>
              <tr className="text-left text-xs font-medium uppercase tracking-wide text-gray-500">
                <th className="py-2 pr-4">E-mail</th>
                <th className="py-2 pr-4">Imię i nazwisko</th>
                <th className="py-2 pr-4">Rola</th>
                <th className="py-2 pr-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 text-sm text-gray-800">
              {users.map((user) => {
                const isSelf = currentUser?.userId === user.userId;
                const isPending = pendingUserId === user.userId;
                return (
                  <tr key={user.userId}>
                    <td className="py-2 pr-4 font-medium text-gray-900">{user.email}</td>
                    <td className="py-2 pr-4">{formatFullName(user)}</td>
                    <td className="py-2 pr-4">
                      <select
                        value={user.role}
                        disabled={isSelf || isPending}
                        title={isSelf ? "Nie możesz zmienić własnej roli" : undefined}
                        aria-label={`Rola użytkownika ${user.email}`}
                        onChange={(event) =>
                          handleRoleChange(user, event.target.value as UserRole)
                        }
                        className="rounded-md border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:cursor-not-allowed disabled:bg-gray-100 disabled:text-gray-500"
                      >
                        {ROLE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                    </td>
                    <td className="py-2 pr-4">
                      <span
                        className={
                          user.isActive
                            ? "rounded-full bg-green-100 px-2 py-0.5 text-xs font-medium text-green-800"
                            : "rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-700"
                        }
                      >
                        {user.isActive ? "aktywny" : "zablokowany"}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {!isLoading && loadError === null && total > PAGE_SIZE && (
        <div className="mt-4 flex items-center justify-between text-sm text-gray-600">
          <span>
            Strona {page} z {totalPages} ({total} kont)
          </span>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setPage((current) => Math.max(1, current - 1))}
              disabled={page === 1}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Poprzednia
            </button>
            <button
              type="button"
              onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              disabled={page >= totalPages}
              className="rounded-md border border-gray-300 px-3 py-1 text-sm hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Następna
            </button>
          </div>
        </div>
      )}
    </section>
  );
}

function roleLabel(role: UserRole): string {
  return ROLE_OPTIONS.find((option) => option.value === role)?.label ?? role;
}
