import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";

import type { User, UserRole } from "../modules/auth/types";

const { useAuthMock } = vi.hoisted(() => ({
  useAuthMock: vi.fn(),
}));

vi.mock("../modules/auth/hooks", () => ({
  useAuth: useAuthMock,
}));

import ProtectedRoute from "./ProtectedRoute";

const baseUser: User = {
  userId: 1,
  email: "anna@example.com",
  firstName: "Anna",
  lastName: "Kowalska",
  avatar: null,
  role: "TeamMember",
  isActive: true,
  createdAt: "2026-05-13T12:00:00Z",
};

interface RenderOptions {
  initialPath?: string;
  requiredRole?: UserRole;
}

function renderProtectedRoute({ initialPath = "/protected", requiredRole }: RenderOptions = {}) {
  return render(
    <MemoryRouter initialEntries={[initialPath]}>
      <Routes>
        <Route element={<ProtectedRoute requiredRole={requiredRole} />}>
          <Route path="/protected" element={<div>Tajne treści</div>} />
        </Route>
        <Route path="/login" element={<div>Strona logowania</div>} />
        <Route path="/" element={<div>Strona główna</div>} />
      </Routes>
    </MemoryRouter>,
  );
}

describe("ProtectedRoute", () => {
  it("redirects to /login when there is no token", () => {
    useAuthMock.mockReturnValue({
      token: null,
      user: null,
      isLoadingUser: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtectedRoute();

    expect(screen.getByText("Strona logowania")).toBeInTheDocument();
    expect(screen.queryByText("Tajne treści")).not.toBeInTheDocument();
  });

  it("renders the loading indicator while the user profile is being fetched", () => {
    useAuthMock.mockReturnValue({
      token: "the-token",
      user: null,
      isLoadingUser: true,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtectedRoute();

    const status = screen.getByRole("status");
    expect(status).toHaveTextContent("Ładowanie...");
    expect(screen.queryByText("Tajne treści")).not.toBeInTheDocument();
  });

  it("renders the nested route when authenticated and no role is required", () => {
    useAuthMock.mockReturnValue({
      token: "the-token",
      user: baseUser,
      isLoadingUser: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtectedRoute();

    expect(screen.getByText("Tajne treści")).toBeInTheDocument();
  });

  it("redirects to / when the user's role does not match requiredRole", () => {
    useAuthMock.mockReturnValue({
      token: "the-token",
      user: { ...baseUser, role: "TeamMember" },
      isLoadingUser: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtectedRoute({ requiredRole: "Administrator" });

    expect(screen.getByText("Strona główna")).toBeInTheDocument();
    expect(screen.queryByText("Tajne treści")).not.toBeInTheDocument();
  });

  it("renders the nested route when the user's role matches requiredRole", () => {
    useAuthMock.mockReturnValue({
      token: "the-token",
      user: { ...baseUser, role: "Administrator" },
      isLoadingUser: false,
      login: vi.fn(),
      logout: vi.fn(),
      updateUser: vi.fn(),
    });

    renderProtectedRoute({ requiredRole: "Administrator" });

    expect(screen.getByText("Tajne treści")).toBeInTheDocument();
  });
});
