import { Navigate, Outlet, useLocation } from "react-router-dom";

import { useAuth } from "../modules/auth/hooks";

export default function ProtectedRoute() {
  const { token } = useAuth();
  const location = useLocation();

  if (token === null) {
    return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  }

  return <Outlet />;
}
