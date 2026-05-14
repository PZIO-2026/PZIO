import { Toaster } from "react-hot-toast";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AdminPanelPage from "../modules/admin/pages/AdminPanelPage";
import AuthProvider from "../modules/auth/AuthProvider";
import LoginPage from "../modules/auth/pages/LoginPage";
import ProfilePage from "../modules/auth/pages/ProfilePage";
import RegisterPage from "../modules/auth/pages/RegisterPage";
import HomePage from "../pages/HomePage";
import ProtectedRoute from "../routes/ProtectedRoute";
import AppLayout from "./AppLayout";
import { ConfirmProvider } from "./ConfirmProvider";

export default function App() {
  return (
    <BrowserRouter>
      <ConfirmProvider>
        <AuthProvider>
          <Toaster position="bottom-right" />
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route element={<ProtectedRoute />}>
              <Route element={<AppLayout />}>
                <Route path="/" element={<HomePage />} />
                <Route path="/profile" element={<ProfilePage />} />
              </Route>
            </Route>
            <Route element={<ProtectedRoute requiredRole="Administrator" />}>
              <Route element={<AppLayout />}>
                <Route path="/admin" element={<AdminPanelPage />} />
              </Route>
            </Route>
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </ConfirmProvider>
    </BrowserRouter>
  );
}
