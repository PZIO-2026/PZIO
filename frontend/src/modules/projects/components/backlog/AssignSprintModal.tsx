import { useState } from "react";

import { ApiError } from "../../../../api/client";
import Modal from "../Modal";
import { updateTask } from "../../api";
import { statusLabels, statusStyles } from "../../constants/sprintForm.constants";
import type { Sprint, WorkItem } from "../../types";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  task: WorkItem | null;
  sprints: Sprint[];
  childCount?: number;
  onAssigned: (task: WorkItem) => void;
}

export default function AssignSprintModal({
  isOpen,
  onClose,
  task,
  sprints,
  childCount = 0,
  onAssigned,
}: Props) {
  const [selectedSprintId, setSelectedSprintId] = useState<number | null>(null);
  const [needsConfirmation, setNeedsConfirmation] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const availableSprints = sprints.filter((sprint) => sprint.status === "planned" || sprint.status === "active");
  const selectedSprint = availableSprints.find((sprint) => sprint.sprintId === selectedSprintId) ?? null;
  const willCascadeSprintChange =
    task !== null && selectedSprint !== null && childCount > 0 && task.sprintId !== selectedSprint.sprintId;

  function handleClose() {
    setSelectedSprintId(null);
    setNeedsConfirmation(false);
    setSubmitError(null);
    onClose();
  }

  function handleSelectSprint(sprintId: number) {
    setSelectedSprintId(sprintId);
    setNeedsConfirmation(false);
    setSubmitError(null);
  }

  async function handleAssign() {
    if (!task || !selectedSprint) return;

    if ((selectedSprint.status === "active" || willCascadeSprintChange) && !needsConfirmation) {
      setNeedsConfirmation(true);
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const updated = await updateTask(task.id, { sprintId: selectedSprint.sprintId });
      onAssigned(updated);
      handleClose();
    } catch (err) {
      setSubmitError(err instanceof ApiError ? err.detail : "Nie udało się przypisać zadania.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <Modal title="Przypisz do sprintu" isOpen={isOpen} onClose={handleClose}>
      <div className="space-y-4">
        {task && (
          <p className="text-sm text-gray-500">
            Zadanie: <span className="font-medium text-gray-800">{task.title}</span>
          </p>
        )}

        {availableSprints.length === 0 ? (
          <div className="rounded-md border border-dashed border-gray-300 px-4 py-6 text-center text-sm text-gray-500">
            Brak dostępnych sprintów (planned lub active).
          </div>
        ) : (
          <div className="space-y-2">
            {availableSprints.map((sprint) => {
              const isSelected = sprint.sprintId === selectedSprintId;
              return (
                <button
                  key={sprint.sprintId}
                  type="button"
                  onClick={() => handleSelectSprint(sprint.sprintId)}
                  className={`w-full rounded-xl border px-4 py-3 text-left transition-colors ${
                    isSelected
                      ? "border-blue-400 bg-blue-50"
                      : "border-gray-200 hover:border-gray-300 hover:bg-gray-50"
                  }`}
                >
                  <div className="flex items-center justify-between gap-3">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-gray-900">{sprint.name}</p>
                      <p className="mt-0.5 text-xs text-gray-500">
                        {new Date(sprint.startDate).toLocaleDateString("pl-PL")} -{" "}
                        {new Date(sprint.endDate).toLocaleDateString("pl-PL")}
                      </p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[sprint.status]}`}
                    >
                      {statusLabels[sprint.status]}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        )}

        {needsConfirmation && (selectedSprint?.status === "active" || willCascadeSprintChange) && (
          <div className="flex gap-3 rounded-lg border border-orange-200 bg-orange-50 px-4 py-3">
            <span className="mt-0.5 shrink-0 text-orange-500">!</span>
            <div className="space-y-2 text-sm text-orange-800">
              {selectedSprint?.status === "active" && (
                <p>
                  Przypisanie zadania do aktywnego sprintu zmienia jego zakres.
                  Kliknij <strong>Potwierdź</strong>, aby kontynuować.
                </p>
              )}
              {willCascadeSprintChange && (
                <p>
                  To zadanie ma {childCount} zadań podrzędnych. Zmiana sprintu obejmie również dzieci.
                </p>
              )}
            </div>
          </div>
        )}

        {submitError && (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{submitError}</div>
        )}

        <div className="flex justify-end gap-3 pt-1">
          <button
            type="button"
            onClick={handleClose}
            className="cursor-pointer rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Anuluj
          </button>
          <button
            type="button"
            onClick={handleAssign}
            disabled={!selectedSprintId || isSubmitting}
            className="cursor-pointer rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {isSubmitting ? "Przypisywanie..." : needsConfirmation ? "Potwierdź" : "Przypisz do sprintu"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
