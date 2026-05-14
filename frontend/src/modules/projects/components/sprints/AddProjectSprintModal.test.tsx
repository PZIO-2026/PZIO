import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import AddProjectSprintModal from "./AddProjectSprintModal";
import * as api from "../../api";
import { ApiError } from "../../../../api/client";

vi.mock("../../api", () => ({
  createSprint: vi.fn(),
}));

describe("AddProjectSprintModal", () => {
  const mockOnClose = vi.fn();
  const mockOnSprintCreated = vi.fn();
  
  const defaultProps = {
    projectId: 1,
    isOpen: true,
    onClose: mockOnClose,
    onSprintCreated: mockOnSprintCreated,
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("powinien poprawnie wyrenderować otwarty modal", () => {
    render(<AddProjectSprintModal {...defaultProps} />);
    
    expect(screen.getByText(/Dodaj sprint/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Utwórz sprint/i })).toBeInTheDocument();
  });

  it("nie powinien renderować zawartości modala, gdy isOpen wynosi false", () => {
    render(<AddProjectSprintModal {...defaultProps} isOpen={false} />);
    
    expect(screen.queryByText(/Dodaj sprint/i)).not.toBeInTheDocument();
  });

  it("powinien zablokować formularz w przypadku pustych danych", async () => {
    const user = userEvent.setup();
    render(<AddProjectSprintModal {...defaultProps} />);

    await user.click(screen.getByRole("button", { name: /Utwórz sprint/i }));

    await waitFor(() => {
      expect(api.createSprint).not.toHaveBeenCalled();
    });
  });

  it("powinien zabezpieczyć przycisk przed podwójnym kliknięciem", async () => {
    const user = userEvent.setup();
    
    let resolveApi: any;
    vi.mocked(api.createSprint).mockImplementationOnce(() => new Promise(resolve => {
      resolveApi = resolve;
    }));

    render(<AddProjectSprintModal {...defaultProps} />);

    const inputs = screen.getAllByRole('textbox');
    const nameInput = inputs[0]; 
    const startDateInput = document.querySelector('input[name="startDate"]') as HTMLInputElement;
    const endDateInput = document.querySelector('input[name="endDate"]') as HTMLInputElement;

    await user.type(nameInput, "Szybki Sprint");
    await user.type(startDateInput, "2026-10-10");
    await user.type(endDateInput, "2026-10-20");

    const submitBtn = screen.getByRole("button", { name: /Utwórz sprint/i });

    await user.click(submitBtn);
    
    expect(submitBtn).toBeDisabled();
    expect(submitBtn).toHaveTextContent(/Tworzenie/i);
    
    await user.click(submitBtn);
    await user.click(submitBtn);

    resolveApi({ sprintId: 10, name: "Szybki Sprint" });

    await waitFor(() => {
      expect(api.createSprint).toHaveBeenCalledTimes(1);
    });
  });

  it("powinien poprawnie przetworzyć dane i zamknąć modal w przypadku sukcesu", async () => {
    const user = userEvent.setup();
    const fakeSprint = { sprintId: 10, name: "Idealny Sprint" };
    vi.mocked(api.createSprint).mockResolvedValueOnce(fakeSprint as any);

    render(<AddProjectSprintModal {...defaultProps} />);

    const inputs = screen.getAllByRole('textbox');
    const nameInput = inputs[0]; 
    const startDateInput = document.querySelector('input[name="startDate"]') as HTMLInputElement;
    const endDateInput = document.querySelector('input[name="endDate"]') as HTMLInputElement;

    await user.type(nameInput, "Idealny Sprint");
    await user.type(startDateInput, "2026-10-10");
    await user.type(endDateInput, "2026-10-20");

    await user.click(screen.getByRole("button", { name: /Utwórz sprint/i }));

    await waitFor(() => {
      expect(api.createSprint).toHaveBeenCalledWith(1, {
        name: "Idealny Sprint",
        startDate: "2026-10-10",
        endDate: "2026-10-20",
        goal: ""
      });
    });
    
    expect(mockOnSprintCreated).toHaveBeenCalledWith(fakeSprint);
    expect(mockOnClose).toHaveBeenCalledTimes(1);
  });

  it("powinien elegancko obsłużyć błąd serwera", async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.createSprint).mockRejectedValueOnce(
      new ApiError(409, "W tym projekcie jest już trwający sprint.")
    );

    render(<AddProjectSprintModal {...defaultProps} />);

    const inputs = screen.getAllByRole('textbox');
    const nameInput = inputs[0]; 
    const startDateInput = document.querySelector('input[name="startDate"]') as HTMLInputElement;
    const endDateInput = document.querySelector('input[name="endDate"]') as HTMLInputElement;

    await user.type(nameInput, "Sprint");
    await user.type(startDateInput, "2026-10-10");
    await user.type(endDateInput, "2026-10-20");
    
    await user.click(screen.getByRole("button", { name: /Utwórz sprint/i }));

    expect(await screen.findByText("W tym projekcie jest już trwający sprint.")).toBeInTheDocument();
    
    expect(mockOnSprintCreated).not.toHaveBeenCalled();
    expect(mockOnClose).not.toHaveBeenCalled();
  });
});