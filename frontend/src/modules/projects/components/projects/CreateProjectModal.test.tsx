import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import CreateProjectModal from "./CreateProjectModal";

import * as api from "../../api";
import { ApiError } from "../../../../api/client";

vi.mock("../../api", () => ({
  createProject: vi.fn(),
}));

describe("CreateProjectModal", () => {
  const mockOnCreated = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("powinien wyrenderować formularz tworzenia projektu z odpowiednimi polami", () => {
    render(<CreateProjectModal onCreated={mockOnCreated} variant="panel" />);
    
    expect(screen.getByLabelText(/Nazwa projektu/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Opis projektu/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Utwórz projekt/i })).toBeInTheDocument();
  });

  it("powinien zablokować wysyłkę, gdy nie podano wymaganej nazwy projektu", async () => {
    const user = userEvent.setup();
    render(<CreateProjectModal onCreated={mockOnCreated} />);

    const submitButton = screen.getByRole("button", { name: /Utwórz projekt/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.createProject).not.toHaveBeenCalled();
    });
  });

  it("powinien pomyślnie utworzyć projekt, wywołać callback i pokazać sukces", async () => {
    const user = userEvent.setup();

    const fakeProject = { projectId: 1, name: "Super Projekt", description: "Mój opis" };
    vi.mocked(api.createProject).mockResolvedValueOnce(fakeProject as any);

    render(<CreateProjectModal onCreated={mockOnCreated} variant="panel" />);

    await user.type(screen.getByLabelText(/Nazwa projektu/i), "Super Projekt");
    await user.type(screen.getByLabelText(/Opis projektu/i), "Mój opis");

    const submitButton = screen.getByRole("button", { name: /Utwórz projekt/i });
    await user.click(submitButton);

    await waitFor(() => {
      expect(api.createProject).toHaveBeenCalledWith({
        name: "Super Projekt",
        description: "Mój opis",
      });
    });

    expect(mockOnCreated).toHaveBeenCalledWith(fakeProject);
    expect(await screen.findByText("Projekt został utworzony.")).toBeInTheDocument();
  });

  it("powinien wyświetlić błąd z backendu (ApiError), gdy utworzenie się nie powiedzie", async () => {
    const user = userEvent.setup();
    
    vi.mocked(api.createProject).mockRejectedValueOnce(
      new ApiError(400, "Taka nazwa projektu już istnieje.")
    );

    render(<CreateProjectModal onCreated={mockOnCreated} />);

    await user.type(screen.getByLabelText(/Nazwa projektu/i), "Duplikat");
    
    const submitButton = screen.getByRole("button", { name: /Utwórz projekt/i });
    await user.click(submitButton);

    expect(await screen.findByText("Taka nazwa projektu już istnieje.")).toBeInTheDocument();

    expect(mockOnCreated).not.toHaveBeenCalled();
  });

  it("powinien zablokować przycisk podczas wysyłania (ochrona przed double-clickiem/spamowaniem)", async () => {
    const user = userEvent.setup();

    let resolveApi: any;
    vi.mocked(api.createProject).mockImplementationOnce(() => new Promise(resolve => {
      resolveApi = resolve;
    }));

    render(<CreateProjectModal onCreated={mockOnCreated} />);

    await user.type(screen.getByLabelText(/Nazwa projektu/i), "Projekt z opóźnieniem");
    
    const submitButton = screen.getByRole("button", { name: /Utwórz projekt/i });

    await user.click(submitButton);

    expect(submitButton).toBeDisabled();
    expect(submitButton).toHaveTextContent("Tworzenie projektu...");

    await user.click(submitButton);
    await user.click(submitButton);
    await user.click(submitButton);

    resolveApi({ projectId: 99, name: "Projekt z opóźnieniem", description: "" });

    await waitFor(() => {
      expect(api.createProject).toHaveBeenCalledTimes(1);
    });
  });

  it("nie powinien renderować pełnej sekcji (tylko sam formularz), gdy wariant to 'modal'", () => {
    const { container } = render(<CreateProjectModal onCreated={mockOnCreated} variant="modal" />);

    expect(screen.queryByText("Utwórz nowy projekt")).not.toBeInTheDocument();
    expect(screen.queryByText("Dodaj nowy projekt do systemu i rozpocznij planowanie sprintów.")).not.toBeInTheDocument();
    
    expect(screen.getByLabelText(/Nazwa projektu/i)).toBeInTheDocument();
    
    expect(container.querySelector("section")).not.toBeInTheDocument();
  });

});