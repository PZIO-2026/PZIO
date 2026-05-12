// src/modules/projects/pages/ProjectsSprintsPage.tsx

import { useEffect, useMemo, useState } from "react";

import { useOutletContext } from "react-router-dom";

import { ApiError } from "../../../api/client";

import {
  deleteSprint,
  fetchBurndown,
  fetchSprints,
} from "../api";

import type {
  BurndownData,
  ProjectDetail,
  Sprint,
} from "../types";

import { hasProjectRole } from "../helpers/permissions";

import AddProjectSprintModal from "../components/sprints/AddProjectSprintModal";

import EditProjectSprintModal from "../components/sprints/EditProjectSprintModal";

import SprintCard from "../components/sprints/SprintCard";

import SprintBurndownModal from "../components/sprints/SprintBurndownModal";

// ============================================================
// Context
// ============================================================

interface OutletContext {
  project: ProjectDetail;
}

// ============================================================
// Component
// ============================================================

export default function ProjectsSprintsPage() {
  const { project } = useOutletContext<OutletContext>();

  const canManageSprints = hasProjectRole(
    project.currentUserRoles,
    ["project_owner", "scrum_master"],
  );

  const [sprints, setSprints] = useState<Sprint[]>([]);

  const [selectedSprintId, setSelectedSprintId] =
    useState<number | null>(null);

  const [selectedEditSprint, setSelectedEditSprint] =
    useState<Sprint | null>(null);

  const [burndown, setBurndown] =
    useState<BurndownData | null>(null);

  const [isLoading, setIsLoading] = useState(true);

  const [burndownLoading, setBurndownLoading] =
    useState(false);

  const [loadError, setLoadError] = useState<
    string | null
  >(null);

  const [isAddModalOpen, setIsAddModalOpen] =
    useState(false);

  const [isEditModalOpen, setIsEditModalOpen] =
    useState(false);

  const [isBurndownModalOpen, setIsBurndownModalOpen] =
    useState(false);

  // ============================================================
  // Handlers
  // ============================================================

  async function loadSprints() {
    setIsLoading(true);

    setLoadError(null);

    try {
      const response = await fetchSprints(
        project.projectId,
      );

      setSprints(response);
    } catch (err) {
      if (err instanceof ApiError) {
        setLoadError(err.detail);
      } else {
        setLoadError(
          "Nie udało się pobrać sprintów.",
        );
      }
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(sprintId: number) {
    const confirmed = window.confirm(
      "Czy na pewno chcesz usunąć sprint?",
    );

    if (!confirmed) return;

    try {
      await deleteSprint(sprintId);

      setSprints((current) =>
        current.filter(
          (sprint) => sprint.sprintId !== sprintId,
        ),
      );

      if (selectedSprintId === sprintId) {
        setSelectedSprintId(null);
        setBurndown(null);
        setIsBurndownModalOpen(false);
      }
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.detail);
      } else {
        alert("Nie udało się usunąć sprintu.");
      }
    }
  }

  async function handleLoadBurndown(
    sprintId: number,
  ) {
    setSelectedSprintId(sprintId);
    setIsBurndownModalOpen(true);
    setBurndownLoading(true);

    try {
      const data = await fetchBurndown(sprintId);

      setBurndown(data);
    } catch (err) {
      if (err instanceof ApiError) {
        alert(err.detail);
      } else {
        alert(
          "Nie udało się pobrać danych burndown.",
        );
      }
    } finally {
      setBurndownLoading(false);
    }
  }

  function handleOpenEditModal(sprint: Sprint) {
    setSelectedEditSprint(sprint);

    setIsEditModalOpen(true);
  }

  // ============================================================
  // Effects
  // ============================================================

  useEffect(() => {
    loadSprints();
  }, [project.projectId]);

  // ============================================================
  // Memo
  // ============================================================

  const selectedSprint = useMemo(
    () =>
      sprints.find(
        (sprint) =>
          sprint.sprintId === selectedSprintId,
      ) ?? null,
    [sprints, selectedSprintId],
  );

  // ============================================================
  // Render
  // ============================================================

  return (
    <>
      <div className="space-y-6">
        {/* Header */}

        {/* <section className="rounded-2xl bg-white p-6 shadow">
          
        </section> */}

        {/* Sprint list */}

        <section className="rounded-2xl bg-white p-6 shadow">

          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
              <h1 className="text-2xl font-bold text-gray-900">
                Sprinty
              </h1>
              {canManageSprints && (
                <button
                  type="button"
                  onClick={() =>
                    setIsAddModalOpen(true)
                  }
                  className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 cursor-pointer"
                >
                  Dodaj sprint
                </button>
              )}
          </div>

          <span className="text-sm text-gray-500">
            Łącznie: {sprints.length}
          </span>

          {isLoading ? (
            <div className="py-10 text-center text-sm text-gray-500">
              Ładowanie sprintów...
            </div>
          ) : loadError !== null ? (
            <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
              {loadError}
            </div>
          ) : sprints.length === 0 ? (
            <div className="rounded-md border border-dashed border-gray-300 px-6 py-10 text-center">
              <p className="text-sm text-gray-500">
                Brak sprintów w projekcie.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {sprints.map((sprint) => (
                <SprintCard
                  key={sprint.sprintId}
                  sprint={sprint}
                  canManageSprints={
                    canManageSprints
                  }
                  onEdit={handleOpenEditModal}
                  onDelete={handleDelete}
                  onBurndown={
                    handleLoadBurndown
                  }
                />
              ))}
            </div>
          )}
        </section>

      </div>

      {/* Burndown modal */}
      <SprintBurndownModal
        isOpen={isBurndownModalOpen}
        onClose={() =>
          setIsBurndownModalOpen(false)
        }
        sprint={selectedSprint}
        burndown={burndown}
        isLoading={burndownLoading}
      />

      {/* Add modal */}      

      <AddProjectSprintModal
        isOpen={isAddModalOpen}
        onClose={() =>
          setIsAddModalOpen(false)
        }
        projectId={project.projectId}
        onSprintCreated={(sprint) => {
          setSprints((current) => [
            sprint,
            ...current,
          ]);
        }}
      />

      {/* Edit modal */}

      <EditProjectSprintModal
        isOpen={isEditModalOpen}
        onClose={() =>
          setIsEditModalOpen(false)
        }
        sprint={selectedEditSprint}
        onSprintUpdated={(updatedSprint) => {
          setSprints((current) =>
            current.map((sprint) =>
              sprint.sprintId ===
              updatedSprint.sprintId
                ? updatedSprint
                : sprint,
            ),
          );

          setSelectedEditSprint(
            updatedSprint,
          );

          setIsEditModalOpen(false);
        }}
      />
    </>
  );
}