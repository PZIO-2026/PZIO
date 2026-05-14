import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AddProjectMemberModal from "./AddProjectMemberModal";
import * as api from "../../api";
import { ApiError } from "../../../../api/client";

vi.mock("../../api", () => ({
  addProjectMember: vi.fn(),
}));

describe("AddProjectMemberModal", () => {
  const mockOnClose = vi.fn();
  const mockOnMemberAdded = vi.fn();

  const defaultProps = {
    isOpen: true,
    onClose: mockOnClose,
    projectId: 1,
    onMemberAdded: mockOnMemberAdded,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("powinien poprawnie wyrenderować otwarty modal", () => {
    render(<AddProjectMemberModal {...defaultProps} />);

    expect(screen.getAllByText("Dodaj użytkownika").length).toBeGreaterThan(0);
  });

  it("nie powinien renderować zawartości, gdy isOpen wynosi false", () => {
    render(<AddProjectMemberModal {...defaultProps} isOpen={false} />);

    expect(screen.queryByText("E-mail użytkownika")).not.toBeInTheDocument();
  });

  it("powinien zablokować formularz w przypadku pustego adresu email", async () => {
    const user = userEvent.setup();
    render(<AddProjectMemberModal {...defaultProps} />);

    const submitButtons = screen.getAllByRole("button", { name: "Dodaj użytkownika" });
    const submitBtn = submitButtons[submitButtons.length - 1];
    
    await user.click(submitBtn);

    await waitFor(() => {
      expect(api.addProjectMember).not.toHaveBeenCalled();
    });
  });

  it("powinien zablokować formularz, gdy odznaczono wszystkie role", async () => {
    const user = userEvent.setup();
    render(<AddProjectMemberModal {...defaultProps} />);

    const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
    await user.type(emailInput, "test@example.com");

    const developerCheckbox = document.querySelector('input[value="developer"]') as HTMLInputElement;
    await user.click(developerCheckbox);

    const submitButtons = screen.getAllByRole("button", { name: "Dodaj użytkownika" });
    const submitBtn = submitButtons[submitButtons.length - 1];
    
    await user.click(submitBtn);

    await waitFor(() => {
      expect(api.addProjectMember).not.toHaveBeenCalled();
    });
  });

  it("powinien zabezpieczyć przycisk przed podwójnym kliknięciem", async () => {
    const user = userEvent.setup();

    let resolveApi: any;
    vi.mocked(api.addProjectMember).mockImplementationOnce(() => new Promise(resolve => {
      resolveApi = resolve;
    }));

    render(<AddProjectMemberModal {...defaultProps} />);

    const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
    await user.type(emailInput, "spam@example.com");

    const submitButtons = screen.getAllByRole("button", { name: "Dodaj użytkownika" });
    const submitBtn = submitButtons[submitButtons.length - 1];

    await user.click(submitBtn);

    expect(submitBtn).toBeDisabled();
    expect(submitBtn).toHaveTextContent("Dodawanie...");

    await user.click(submitBtn);
    await user.click(submitBtn);

    resolveApi({ id: 99, email: "spam@example.com", roles: ["developer"] });

    await waitFor(() => {
      expect(api.addProjectMember).toHaveBeenCalledTimes(1);
    });
  });

  it("powinien poprawnie przetworzyć dane i zamknąć modal w przypadku sukcesu", async () => {
    const user = userEvent.setup();
    const fakeMember = { id: 10, email: "nowy@example.com", roles: ["developer"] };
    vi.mocked(api.addProjectMember).mockResolvedValueOnce(fakeMember as any);

    render(<AddProjectMemberModal {...defaultProps} />);

    const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
    await user.type(emailInput, "nowy@example.com");

    const submitButtons = screen.getAllByRole("button", { name: "Dodaj użytkownika" });
    const submitBtn = submitButtons[submitButtons.length - 1];
    
    await user.click(submitBtn);

    await waitFor(() => {
      expect(api.addProjectMember).toHaveBeenCalledWith(1, {
        email: "nowy@example.com",
        roles: ["developer"],
      });
    });

    expect(mockOnMemberAdded).toHaveBeenCalledWith(fakeMember);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("powinien elegancko obsłużyć błąd serwera", async () => {
    const user = userEvent.setup();

    vi.mocked(api.addProjectMember).mockRejectedValueOnce(
      new ApiError(404, "Użytkownik o podanym adresie email nie istnieje.")
    );

    render(<AddProjectMemberModal {...defaultProps} />);

    const emailInput = document.querySelector('input[name="email"]') as HTMLInputElement;
    await user.type(emailInput, "brak@example.com");

    const submitButtons = screen.getAllByRole("button", { name: "Dodaj użytkownika" });
    const submitBtn = submitButtons[submitButtons.length - 1];
    
    await user.click(submitBtn);

    expect(await screen.findByText("Użytkownik o podanym adresie email nie istnieje.")).toBeInTheDocument();

    expect(mockOnMemberAdded).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});