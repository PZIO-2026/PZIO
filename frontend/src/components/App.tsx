import { Toaster } from "react-hot-toast";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";

import AdminPanelPage from "../modules/admin/pages/AdminPanelPage";
import AuthProvider from "../modules/auth/AuthProvider";
import ForgotPasswordPage from "../modules/auth/pages/ForgotPasswordPage";
import LoginPage from "../modules/auth/pages/LoginPage";
import ProfilePage from "../modules/auth/pages/ProfilePage";
import RegisterPage from "../modules/auth/pages/RegisterPage";
import ResetPasswordPage from "../modules/auth/pages/ResetPasswordPage";
import OAuthCallbackPage from "../modules/auth/pages/OAuthCallbackPage";
import ProjectsListPage from "../modules/projects/pages/ProjectsListPage";
import ProjectDetailsLayout  from "../modules/projects/layouts/ProjectDetailsLayout";
import ProjectsOverviewPage from "../modules/projects/pages/ProjectsOverviewPage";
import ProjectsMembersPage from "../modules/projects/pages/ProjectsMembersPage";
import ProjectsSprintsPage from "../modules/projects/pages/ProjectsSprintsPage";
import HomePage from "../pages/HomePage";
import ProtectedRoute from "../routes/ProtectedRoute";
import AppLayout from "./AppLayout";
import { ConfirmProvider } from "./ConfirmProvider";

export default function App() {
  return (
    <BrowserRouter>
      <ConfirmProvider>          
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />
          <Route path="/oauth/callback" element={<OAuthCallbackPage />} />
          <Route element={<ProtectedRoute />}>
            <Route element={<AppLayout />}>
              <Route path="/" element={<HomePage />} />
              <Route path="/profile" element={<ProfilePage />} />
              <Route path="/projects" element={<ProjectsListPage />} />
              <Route path="/projects/:projectId" element={<ProjectDetailsLayout  />}>
                <Route index element={<ProjectsOverviewPage />} />
                <Route path="members" element={<ProjectsMembersPage />} />
                <Route path="sprints" element={<ProjectsSprintsPage />} />
                <Route path="backlog" element={<div>Backlog view</div>} />
                <Route path="board" element={<div>Board view</div>} />
              </Route>
            </Route>
            <Route element={<ProtectedRoute requiredRole="Administrator" />}>
              <Route element={<AppLayout />}>
                <Route path="/admin" element={<AdminPanelPage />} />
              </Route>
            </Route>
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </AuthProvider>
      </ConfirmProvider>
    </BrowserRouter>
  );
}