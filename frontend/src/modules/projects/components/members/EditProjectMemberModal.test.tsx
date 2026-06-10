import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import EditProjectMemberModal from "./EditProjectMemberModal";

import * as api from "../../api";
import { useAuth } from "../../../auth/hooks";

vi.mock("../../api", () => ({
  updateProjectMemberRoles: vi.fn(),
}));

vi.mock("../../../auth/hooks", () => ({
  useAuth: vi.fn(),
}));

describe("EditProjectMemberModal", () => {
  const mockOnClose = vi.fn();
  const mockOnSuccess = vi.fn();
  
  const defaultProps = {
    projectId: 1,
    userId: 123,
    email: "test@example.com",
    currentRoles: ["developer"],
    onClose: mockOnClose,
    onSuccess: mockOnSuccess,
  };

  beforeEach(() => {
    vi.clearAllMocks();
    
    vi.mocked(useAuth).mockReturnValue({ user: { userId: 999 } } as any);
  });

  it("powinien wyrenderować modal z poprawnym adresem email w inputcie i zaznaczoną obecną rolą", () => {
    render(<EditProjectMemberModal {...defaultProps} />);

    expect(screen.getByText("Edytuj użytkownika")).toBeInTheDocument();

    const emailInput = screen.getByDisplayValue("test@example.com");
    expect(emailInput).toBeDisabled();

    const devCheckbox = screen.getByRole("checkbox", { name: "Developer" });
    expect(devCheckbox).toBeChecked();

    const smCheckbox = screen.getByRole("checkbox", { name: "Scrum Master" });
    expect(smCheckbox).not.toBeChecked();
  });

  it("powinien zablokować wysyłkę i pokazać błąd Zoda, gdy odznaczono wszystkie role", async () => {
    const user = userEvent.setup();
    render(<EditProjectMemberModal {...defaultProps} />);

    const devCheckbox = screen.getByRole("checkbox", { name: "Developer" });
    await user.click(devCheckbox);

    const submitButton = screen.getByRole("button", { name: /zapisz zmiany/i });
    await user.click(submitButton);

    expect(await screen.findByText("Wybierz przynajmniej jedną rolę")).toBeInTheDocument();
    expect(api.updateProjectMemberRoles).not.toHaveBeenCalled();
  });

  it("powinien pomyślnie wysłać formularz i zamknąć modal", async () => {
    const user = userEvent.setup();
    vi.mocked(api.updateProjectMemberRoles).mockResolvedValueOnce(undefined as any);

    render(<EditProjectMemberModal {...defaultProps} />);

    const smCheckbox = screen.getByRole("checkbox", { name: "Scrum Master" });
    await user.click(smCheckbox);
    
    expect(smCheckbox).toBeChecked();

    const submitButton = screen.getByRole("button", { name: /zapisz zmiany/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.updateProjectMemberRoles).toHaveBeenCalledWith(
        1,
        123,
        expect.arrayContaining(["developer", "scrum_master"])
      );
    });

    expect(mockOnSuccess).toHaveBeenCalledTimes(1);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("powinien wyświetlić ostrzeżenie (window.confirm) przy próbie odebrania sobie uprawnień", async () => {
    const user = userEvent.setup();

    vi.mocked(useAuth).mockReturnValue({ user: { userId: 123 } } as any);

    const confirmSpy = vi.spyOn(window, "confirm").mockReturnValue(false);

    render(<EditProjectMemberModal {...defaultProps} currentRoles={["project_owner"]} />);

    const poCheckbox = screen.getByRole("checkbox", { name: "Project Owner" });
    await user.click(poCheckbox);
    
    const devCheckbox = screen.getByRole("checkbox", { name: "Developer" });
    await user.click(devCheckbox);

    const submitButton = screen.getByRole("button", { name: /zapisz zmiany/i });
    await user.click(submitButton);

    expect(confirmSpy).toHaveBeenCalledTimes(1);
    expect(api.updateProjectMemberRoles).not.toHaveBeenCalled();
    
    confirmSpy.mockRestore();
  });
});