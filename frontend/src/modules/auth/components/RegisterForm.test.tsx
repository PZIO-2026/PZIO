import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ApiError } from "../../../api/client";

const { registerMock, navigateMock } = vi.hoisted(() => ({
  registerMock: vi.fn(),
  navigateMock: vi.fn(),
}));

vi.mock("../api", () => ({
  register: registerMock,
}));

vi.mock("react-router-dom", () => ({
  useNavigate: () => navigateMock,
}));

import RegisterForm from "./RegisterForm";

async function fillValidForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/imię/i), "Anna");
  await user.type(screen.getByLabelText(/nazwisko/i), "Kowalska");
  await user.type(screen.getByLabelText(/email/i), "anna@example.com");
  await user.type(screen.getByLabelText(/^hasło$/i), "haslo1234");
}

describe("RegisterForm", () => {
  it("shows validation errors when fields are empty", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    expect(await screen.findByText("Imię jest wymagane")).toBeInTheDocument();
    expect(screen.getByText("Nazwisko jest wymagane")).toBeInTheDocument();
    expect(screen.getByText("Nieprawidłowy format adresu email")).toBeInTheDocument();
    expect(screen.getByText("Hasło musi mieć co najmniej 8 znaków")).toBeInTheDocument();
    expect(registerMock).not.toHaveBeenCalled();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it("shows the password-length error for a short password", async () => {
    const user = userEvent.setup();
    render(<RegisterForm />);

    await user.type(screen.getByLabelText(/imię/i), "Anna");
    await user.type(screen.getByLabelText(/nazwisko/i), "Kowalska");
    await user.type(screen.getByLabelText(/email/i), "anna@example.com");
    await user.type(screen.getByLabelText(/^hasło$/i), "krótkie");

    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    expect(await screen.findByText("Hasło musi mieć co najmniej 8 znaków")).toBeInTheDocument();
    expect(registerMock).not.toHaveBeenCalled();
  });

  it("calls register() with the form values and navigates to /login on success", async () => {
    registerMock.mockResolvedValueOnce({
      userId: 1,
      email: "anna@example.com",
      firstName: "Anna",
      lastName: "Kowalska",
      role: "TeamMember",
      isActive: true,
      avatar: null,
      createdAt: "2026-05-13T12:00:00Z",
    });
    const user = userEvent.setup();
    render(<RegisterForm />);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    await waitFor(() => {
      expect(registerMock).toHaveBeenCalledWith({
        firstName: "Anna",
        lastName: "Kowalska",
        email: "anna@example.com",
        password: "haslo1234",
      });
    });
    expect(navigateMock).toHaveBeenCalledWith("/login", {
      state: { registeredEmail: "anna@example.com" },
      replace: true,
    });
  });

  it("shows a duplicate-email message on 409 and does not navigate", async () => {
    registerMock.mockRejectedValueOnce(new ApiError(409, "Email already in use"));
    const user = userEvent.setup();
    render(<RegisterForm />);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    expect(
      await screen.findByText("Konto z tym adresem email już istnieje."),
    ).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it("surfaces ApiError.detail for non-409 server errors", async () => {
    registerMock.mockRejectedValueOnce(new ApiError(500, "Internal Server Error"));
    const user = userEvent.setup();
    render(<RegisterForm />);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    expect(await screen.findByText("Internal Server Error")).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });

  it("falls back to a generic message for non-ApiError failures (e.g. network)", async () => {
    registerMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    const user = userEvent.setup();
    render(<RegisterForm />);

    await fillValidForm(user);
    await user.click(screen.getByRole("button", { name: /utwórz konto/i }));

    expect(
      await screen.findByText("Nie udało się połączyć z serwerem. Spróbuj ponownie."),
    ).toBeInTheDocument();
    expect(navigateMock).not.toHaveBeenCalled();
  });
});
