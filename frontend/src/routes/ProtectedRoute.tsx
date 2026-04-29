import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../modules/auth/hooks";

export default function ProtectedRoute() {
  const { token, isLoadingUser } = useAuth();
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

  return <Outlet />;
}
