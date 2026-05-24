import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";

import EditProjectSprintModal from "./EditProjectSprintModal";
import { updateSprint } from "../../api";
import { ApiError } from "../../../../api/client";
import type { Sprint } from "../../types";

vi.mock("../../api", () => ({
  updateSprint: vi.fn(),
}));

const mockUpdateSprint = vi.mocked(updateSprint);

const mockSprint: Sprint = {
  sprintId: 10,
  projectId: 5,
  name: "Sprint Testowy",
  goal: "Stworzenie testów",
  startDate: "2026-05-01T00:00:00.000Z",
  endDate: "2026-05-14T00:00:00.000Z",
  status: "planned",
};

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  sprint: mockSprint,
  onSprintUpdated: vi.fn(),
};

describe("EditProjectSprintModal", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });


  it("nie powinien renderować zawartości, gdy isOpen wynosi false", () => {
    render(<EditProjectSprintModal {...defaultProps} isOpen={false} />);
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("powinien poprawnie wypełnić formularz danymi ze sprintu", () => {
    const { container } = render(<EditProjectSprintModal {...defaultProps} />);

    expect(container.querySelector('[name="name"]')).toHaveValue("Sprint Testowy");
    expect(container.querySelector('[name="goal"]')).toHaveValue("Stworzenie testów");
    expect(container.querySelector('[name="startDate"]')).toHaveValue("2026-05-01");
    expect(container.querySelector('[name="endDate"]')).toHaveValue("2026-05-14");
    expect(container.querySelector('[name="status"]')).toHaveValue("planned");
  });

  it("powinien zamknąć modal po kliknięciu 'Anuluj'", async () => {
    const user = userEvent.setup();
    render(<EditProjectSprintModal {...defaultProps} />);

    await user.click(screen.getByRole("button", { name: /anuluj/i }));
    
    expect(defaultProps.onClose).toHaveBeenCalledTimes(1);
    expect(mockUpdateSprint).not.toHaveBeenCalled();
  });

  it("nie powinien wywoływać API, jeśli prop sprint wynosi null", async () => {
    const user = userEvent.setup();
    render(<EditProjectSprintModal {...defaultProps} sprint={null} />);

    const submitBtn = screen.getByRole("button", { name: /zapisz/i });
    await user.click(submitBtn);

    expect(mockUpdateSprint).not.toHaveBeenCalled();
  });


  it("powinien zablokować wysyłkę, jeśli wyczyszczono wymaganą nazwę sprintu", async () => {
    const user = userEvent.setup();
    const { container } = render(<EditProjectSprintModal {...defaultProps} />);

    const nameInput = container.querySelector('[name="name"]') as HTMLInputElement;
    await user.clear(nameInput);
    await user.type(nameInput, "ab"); 
    
    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText(/Nazwa sprintu musi mieć minimum 3 znaki/i)).toBeInTheDocument();
    expect(mockUpdateSprint).not.toHaveBeenCalled();
  });

  it("powinien zablokować wysyłkę, jeśli sprint trwa dłużej niż 60 dni", async () => {
    const user = userEvent.setup();
    const { container } = render(<EditProjectSprintModal {...defaultProps} />);

    const endDateInput = container.querySelector('[name="endDate"]') as HTMLInputElement;
    await user.clear(endDateInput);
    await user.type(endDateInput, "2026-08-01"); 
    
    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText(/Sprint nie może trwać dłużej niż 60 dni/i)).toBeInTheDocument();
    expect(mockUpdateSprint).not.toHaveBeenCalled();
  });


  it("powinien poprawnie wysłać formularz, wywołać callbacki i zamknąć modal", async () => {
    const user = userEvent.setup();
    const updatedSprint = { ...mockSprint, name: "Zmieniona Nazwa" };
    mockUpdateSprint.mockResolvedValueOnce(updatedSprint);

    const { container } = render(<EditProjectSprintModal {...defaultProps} />);

    const nameInput = container.querySelector('[name="name"]') as HTMLInputElement;
    await user.clear(nameInput);
    await user.type(nameInput, "Zmieniona Nazwa");

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    await waitFor(() => {
      expect(mockUpdateSprint).toHaveBeenCalledWith(10, {
        name: "Zmieniona Nazwa",
        startDate: "2026-05-01",
        endDate: "2026-05-14",
        goal: "Stworzenie testów",
        status: "planned",
      });
    });

    expect(defaultProps.onSprintUpdated).toHaveBeenCalledWith(updatedSprint);
    expect(defaultProps.onClose).toHaveBeenCalled();
  });

  it("powinien zablokować przycisk podczas wysyłania", async () => {
    const user = userEvent.setup();
    let resolveApi!: (val: Sprint) => void;
    mockUpdateSprint.mockImplementationOnce(() => {
      return new Promise((resolve) => {
        resolveApi = resolve;
      });
    });

    render(<EditProjectSprintModal {...defaultProps} />);

    const submitBtn = screen.getByRole("button", { name: /zapisz zmiany/i });
    await user.click(submitBtn);

    await waitFor(() => {
      expect(submitBtn).toBeDisabled();
    });
    expect(submitBtn).toHaveTextContent("Zapisywanie...");

    resolveApi!(mockSprint);
  });

  it.each([
    [400, "Data zakończenia sprintu musi być późniejsza niż data rozpoczęcia."],
    [403, "Nie masz uprawnień do edycji tego sprintu."],
    [404, "Sprint nie istnieje lub został usunięty."],
    [409, "W projekcie jest już aktywny sprint — nie można aktywować drugiego."],
    [422, "Podane dane sprintu są nieprawidłowe."],
    [500, "Nie udało się zaktualizować sprintu."],
  ])("powinien wyświetlić komunikat '%s' dla błędu API o statusie %i", async (status, expectedMessage) => {
    const user = userEvent.setup();
    mockUpdateSprint.mockRejectedValueOnce(new ApiError(status as number, "Error"));

    const { container } = render(<EditProjectSprintModal {...defaultProps} />);

    const nameInput = container.querySelector('[name="name"]') as HTMLInputElement;
    await user.type(nameInput, "x");

    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText(expectedMessage)).toBeInTheDocument();
    expect(defaultProps.onClose).not.toHaveBeenCalled();
  });

  it("powinien wyświetlić ogólny komunikat błędu przy awarii sieci (np. backend leży)", async () => {
    const user = userEvent.setup();
    mockUpdateSprint.mockRejectedValueOnce(new Error("Network Error"));

    render(<EditProjectSprintModal {...defaultProps} />);
    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText("Nie udało się połączyć z serwerem. Spróbuj ponownie.")).toBeInTheDocument();
  });


  it("powinien wyczyścić stan błędu po zamknięciu i ponownym otwarciu modala", async () => {
    const user = userEvent.setup();
    mockUpdateSprint.mockRejectedValueOnce(new ApiError(404, "Not Found"));

    const { rerender, container } = render(<EditProjectSprintModal {...defaultProps} />);
    
    const nameInput = container.querySelector('[name="name"]') as HTMLInputElement;
    await user.type(nameInput, "x");
    await user.click(screen.getByRole("button", { name: /zapisz zmiany/i }));

    expect(await screen.findByText("Sprint nie istnieje lub został usunięty.")).toBeInTheDocument();

    rerender(<EditProjectSprintModal {...defaultProps} isOpen={false} />);

    rerender(<EditProjectSprintModal {...defaultProps} isOpen={true} />);

    expect(screen.queryByText("Sprint nie istnieje lub został usunięty.")).not.toBeInTheDocument();
  });
});