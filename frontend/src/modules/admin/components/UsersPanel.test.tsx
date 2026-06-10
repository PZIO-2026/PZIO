import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import UsersPanel from "./UsersPanel";
import type { User } from "../../auth/types";
import * as api from "../api";
import { useAuth } from "../../auth/hooks";

vi.mock("../api", () => ({
  fetchUsers: vi.fn(),
  updateUserRole: vi.fn(),
  updateUserStatus: vi.fn(),
}));

vi.mock("../../auth/hooks", () => ({
  useAuth: vi.fn(),
}));

function makeUser(overrides: Partial<User> = {}): User {
  return {
    userId: 1,
    email: "user@example.com",
    firstName: "Test",
    lastName: "User",
    avatar: null,
    role: "TeamMember",
    isActive: true,
    createdAt: "2026-01-01T00:00:00Z",
    ...overrides,
  };
}

const admin = makeUser({ userId: 99, email: "admin@example.com", role: "Administrator" });

describe("UsersPanel — zmiana statusu", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(useAuth).mockReturnValue({ user: admin } as ReturnType<typeof useAuth>);
  });

  it("blokuje konto i aktualizuje znacznik po kliknięciu", async () => {
    const target = makeUser({ userId: 1, email: "user@example.com", isActive: true });
    vi.mocked(api.fetchUsers).mockResolvedValue({ items: [target], total: 1, page: 1, size: 50 });
    vi.mocked(api.updateUserStatus).mockResolvedValue({ ...target, isActive: false });

    render(<UsersPanel />);

    const button = await screen.findByRole("button", {
      name: "Zablokuj użytkownika user@example.com",
    });
    await userEvent.click(button);

    await waitFor(() =>
      expect(api.updateUserStatus).toHaveBeenCalledWith(1, false),
    );
    expect(await screen.findByText("zablokowany")).toBeInTheDocument();
    expect(
      await screen.findByText("Zablokowano konto użytkownika user@example.com."),
    ).toBeInTheDocument();
  });

  it("nie pozwala administratorowi zablokować własnego konta", async () => {
    vi.mocked(api.fetchUsers).mockResolvedValue({ items: [admin], total: 1, page: 1, size: 50 });

    render(<UsersPanel />);

    const button = await screen.findByRole("button", {
      name: "Zablokuj użytkownika admin@example.com",
    });
    expect(button).toBeDisabled();
  });

  it("przywraca poprzedni status i pokazuje błąd, gdy żądanie się nie powiedzie", async () => {
    const target = makeUser({ userId: 1, email: "user@example.com", isActive: true });
    vi.mocked(api.fetchUsers).mockResolvedValue({ items: [target], total: 1, page: 1, size: 50 });
    vi.mocked(api.updateUserStatus).mockRejectedValue(new Error("boom"));

    render(<UsersPanel />);

    const button = await screen.findByRole("button", {
      name: "Zablokuj użytkownika user@example.com",
    });
    await userEvent.click(button);

    expect(
      await screen.findByText("Nie udało się zmienić statusu użytkownika. Spróbuj ponownie."),
    ).toBeInTheDocument();
    // Status wraca do "aktywny", a przycisk znów oferuje zablokowanie.
    expect(screen.getByText("aktywny")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Zablokuj użytkownika user@example.com" }),
    ).toBeInTheDocument();
  });
});
