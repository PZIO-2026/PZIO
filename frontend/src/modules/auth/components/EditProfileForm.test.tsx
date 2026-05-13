import { describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { ApiError } from "../../../api/client";
import type { User } from "../types";

const { updateMeMock } = vi.hoisted(() => ({
  updateMeMock: vi.fn(),
}));

vi.mock("../api", () => ({
  updateMe: updateMeMock,
}));

import EditProfileForm from "./EditProfileForm";

const baseUser: User = {
  userId: 1,
  email: "anna@example.com",
  firstName: "Anna",
  lastName: "Kowalska",
  avatar: "https://example.com/old.png",
  role: "TeamMember",
  isActive: true,
  createdAt: "2026-05-13T12:00:00Z",
};

describe("EditProfileForm", () => {
  it("populates inputs with the user prop's values", () => {
    render(<EditProfileForm user={baseUser} onSuccess={vi.fn()} onCancel={vi.fn()} />);

    expect(screen.getByLabelText(/imię/i)).toHaveValue("Anna");
    expect(screen.getByLabelText(/nazwisko/i)).toHaveValue("Kowalska");
    expect(screen.getByLabelText(/awatar/i)).toHaveValue("https://example.com/old.png");
  });

  it("renders an empty avatar input when user.avatar is null", () => {
    render(
      <EditProfileForm
        user={{ ...baseUser, avatar: null }}
        onSuccess={vi.fn()}
        onCancel={vi.fn()}
      />,
    );

    expect(screen.getByLabelText(/awatar/i)).toHaveValue("");
  });

  it("calls updateMe with the (trimmed) form values and invokes onSuccess", async () => {
    const updatedUser: User = { ...baseUser, firstName: "Ania", avatar: "https://new.example/a.png" };
    updateMeMock.mockResolvedValueOnce(updatedUser);
    const onSuccess = vi.fn();
    const user = userEvent.setup();

    render(<EditProfileForm user={baseUser} onSuccess={onSuccess} onCancel={vi.fn()} />);

    const firstName = screen.getByLabelText(/imię/i);
    await user.clear(firstName);
    await user.type(firstName, "Ania");

    const avatar = screen.getByLabelText(/awatar/i);
    await user.clear(avatar);
    await user.type(avatar, "  https://new.example/a.png  ");

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    await waitFor(() => {
      expect(updateMeMock).toHaveBeenCalledWith({
        firstName: "Ania",
        lastName: "Kowalska",
        avatar: "https://new.example/a.png",
      });
    });
    expect(onSuccess).toHaveBeenCalledWith(updatedUser);
  });

  it("sends avatar: null when the avatar field is empty after trimming", async () => {
    updateMeMock.mockResolvedValueOnce({ ...baseUser, avatar: null });
    const user = userEvent.setup();

    render(<EditProfileForm user={baseUser} onSuccess={vi.fn()} onCancel={vi.fn()} />);

    const avatar = screen.getByLabelText(/awatar/i);
    await user.clear(avatar);
    await user.type(avatar, "   ");

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    await waitFor(() => {
      expect(updateMeMock).toHaveBeenCalledWith({
        firstName: "Anna",
        lastName: "Kowalska",
        avatar: null,
      });
    });
  });

  it("surfaces ApiError.detail when updateMe fails with ApiError", async () => {
    updateMeMock.mockRejectedValueOnce(new ApiError(400, "Avatar URL is invalid"));
    const onSuccess = vi.fn();
    const user = userEvent.setup();

    render(<EditProfileForm user={baseUser} onSuccess={onSuccess} onCancel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText("Avatar URL is invalid")).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("falls back to a generic message for non-ApiError failures", async () => {
    updateMeMock.mockRejectedValueOnce(new TypeError("fetch failed"));
    const onSuccess = vi.fn();
    const user = userEvent.setup();

    render(<EditProfileForm user={baseUser} onSuccess={onSuccess} onCancel={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(
      await screen.findByText("Nie udało się zapisać zmian. Spróbuj ponownie."),
    ).toBeInTheDocument();
    expect(onSuccess).not.toHaveBeenCalled();
  });

  it("invokes onCancel and does not call updateMe when clicking Anuluj", async () => {
    const onCancel = vi.fn();
    const user = userEvent.setup();

    render(<EditProfileForm user={baseUser} onSuccess={vi.fn()} onCancel={onCancel} />);

    await user.click(screen.getByRole("button", { name: /anuluj/i }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(updateMeMock).not.toHaveBeenCalled();
  });
});
