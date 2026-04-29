import { Link, NavLink, Outlet } from "react-router-dom";

import { useAuth } from "../modules/auth/hooks";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  isActive
    ? "text-sm font-medium text-blue-600"
    : "text-sm font-medium text-gray-600 hover:text-gray-900";

export default function AppLayout() {
  const { user, logout } = useAuth();

  if (user === null) return null;

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="border-b border-gray-200 bg-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-3">
          <div className="flex items-center gap-6">
            <Link to="/" className="text-xl font-bold text-gray-900">
              PZIO
            </Link>
            <div className="hidden items-center gap-4 sm:flex">
              <NavLink to="/" end className={navLinkClass}>
                Strona główna
              </NavLink>
              <NavLink to="/profile" className={navLinkClass}>
                Profil
              </NavLink>
            </div>
          </div>

          <div className="flex items-center gap-4">
            <span className="hidden text-sm text-gray-600 sm:inline">
              {user.firstName} {user.lastName}
            </span>
            <button
              type="button"
              onClick={logout}
              className="rounded-md bg-gray-900 px-3 py-1.5 text-sm font-medium text-white hover:bg-gray-700"
            >
              Wyloguj się
            </button>
          </div>
        </div>
      </nav>

      <main>
        <Outlet />
      </main>
    </div>
  );
}
