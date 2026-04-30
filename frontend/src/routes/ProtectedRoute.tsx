import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../modules/auth/hooks";
import type { UserRole } from "../modules/auth/types";

interface ProtectedRouteProps {
  // When set, only users with this role may render the nested routes; others are
  // bounced back to the home page.
  requiredRole?: UserRole;
}

export default function ProtectedRoute({ requiredRole }: ProtectedRouteProps = {}) {
  const { token, user, isLoadingUser } = useAuth();
  const location = useLocation();

  if (token === null) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  if (isLoadingUser) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-screen items-center justify-center bg-gray-50 text-gray-500"
      >
        Ładowanie...
      </div>
    );
  }

  if (requiredRole !== undefined && user?.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }

  return <Outlet />;
}
