import { describe, expect, it, vi } from "vitest";
import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { AUTH_EXPIRED_EVENT } from "../../api/client";
import { getStoredToken, setStoredToken } from "./storage";
import { useAuth } from "./hooks";
import type { User } from "./types";

const { getMeMock } = vi.hoisted(() => ({
  getMeMock: vi.fn(),
}));

vi.mock("./api", () => ({
  getMe: getMeMock,
}));

import AuthProvider from "./AuthProvider";

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

function TestConsumer() {
  const auth = useAuth();
  return (
    <div>
      <div data-testid="token">{auth.token ?? "null"}</div>
      <div data-testid="user-email">{auth.user?.email ?? "null"}</div>
      <div data-testid="is-loading-user">{String(auth.isLoadingUser)}</div>
      <button onClick={() => auth.login("new-token")}>Login</button>
      <button onClick={auth.logout}>Logout</button>
      <button
        onClick={() =>
          auth.updateUser({
            ...baseUser,
            firstName: "Updated",
            email: "updated@example.com",
          })
        }
      >
        UpdateUser
      </button>
    </div>
  );
}

function renderAuthProvider() {
  return render(
    <AuthProvider>
      <TestConsumer />
    </AuthProvider>,
  );
}

describe("AuthProvider", () => {
  it("starts unauthenticated when localStorage is empty and does not call getMe", () => {
    renderAuthProvider();

    expect(screen.getByTestId("token")).toHaveTextContent("null");
    expect(screen.getByTestId("user-email")).toHaveTextContent("null");
    expect(screen.getByTestId("is-loading-user")).toHaveTextContent("false");
    expect(getMeMock).not.toHaveBeenCalled();
  });

  it("seeds token from localStorage and fetches /me on mount", async () => {
    setStoredToken("stored-token");
    getMeMock.mockResolvedValueOnce(baseUser);

    renderAuthProvider();

    expect(screen.getByTestId("token")).toHaveTextContent("stored-token");
    expect(screen.getByTestId("is-loading-user")).toHaveTextContent("true");

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("anna@example.com");
    });
    expect(screen.getByTestId("is-loading-user")).toHaveTextContent("false");
    expect(getMeMock).toHaveBeenCalledTimes(1);
  });

  it("clears the session when getMe fails (token rejected / expired)", async () => {
    setStoredToken("stale-token");
    getMeMock.mockRejectedValueOnce(new Error("401"));

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId("token")).toHaveTextContent("null");
    });
    expect(screen.getByTestId("user-email")).toHaveTextContent("null");
    expect(getStoredToken()).toBeNull();
  });

  it("login() stores the new token, resets user, and re-fetches /me", async () => {
    getMeMock.mockResolvedValueOnce(baseUser);
    const user = userEvent.setup();

    renderAuthProvider();

    await user.click(screen.getByRole("button", { name: /^login$/i }));

    expect(screen.getByTestId("token")).toHaveTextContent("new-token");
    expect(getStoredToken()).toBe("new-token");

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("anna@example.com");
    });
    expect(getMeMock).toHaveBeenCalledTimes(1);
  });

  it("logout() clears the token and user from state and storage", async () => {
    setStoredToken("stored-token");
    getMeMock.mockResolvedValueOnce(baseUser);
    const user = userEvent.setup();

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("anna@example.com");
    });

    await user.click(screen.getByRole("button", { name: /^logout$/i }));

    expect(screen.getByTestId("token")).toHaveTextContent("null");
    expect(screen.getByTestId("user-email")).toHaveTextContent("null");
    expect(getStoredToken()).toBeNull();
  });

  it("updateUser() replaces the user in state without touching the token", async () => {
    setStoredToken("stored-token");
    getMeMock.mockResolvedValueOnce(baseUser);
    const user = userEvent.setup();

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("anna@example.com");
    });

    await user.click(screen.getByRole("button", { name: /updateuser/i }));

    expect(screen.getByTestId("user-email")).toHaveTextContent("updated@example.com");
    expect(screen.getByTestId("token")).toHaveTextContent("stored-token");
    expect(getStoredToken()).toBe("stored-token");
  });

  it("clears the session when AUTH_EXPIRED_EVENT is dispatched on window", async () => {
    setStoredToken("stored-token");
    getMeMock.mockResolvedValueOnce(baseUser);

    renderAuthProvider();

    await waitFor(() => {
      expect(screen.getByTestId("user-email")).toHaveTextContent("anna@example.com");
    });

    act(() => {
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    });

    expect(screen.getByTestId("token")).toHaveTextContent("null");
    expect(screen.getByTestId("user-email")).toHaveTextContent("null");
    expect(getStoredToken()).toBeNull();
  });
});
