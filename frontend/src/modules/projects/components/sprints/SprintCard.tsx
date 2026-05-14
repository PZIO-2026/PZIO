import type {
  Sprint,
} from "../../types";

import {
  statusLabels,
  statusStyles,
} from "../../constants/sprintForm.constants";

interface Props {
  sprint: Sprint;

  canManageSprints: boolean;

  onEdit: (sprint: Sprint) => void;

  onDelete: (sprintId: number) => void;

  onBurndown: (sprintId: number) => void;
}

export default function SprintCard({
  sprint,
  canManageSprints,
  onEdit,
  onDelete,
  onBurndown,
}: Props) {
  return (
    <div className="rounded-xl border border-gray-200 p-5">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        {/* Left side */}

        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-3">
            <h3 className="text-lg font-semibold text-gray-900">
              {sprint.name}
            </h3>

            <span
              className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${statusStyles[sprint.status]}`}
            >
              {statusLabels[sprint.status]}
            </span>
          </div>

          <p className="mt-2 text-sm text-gray-500">
            {new Date(
              sprint.startDate,
            ).toLocaleDateString("pl-PL")}{" "}
            —{" "}
            {new Date(
              sprint.endDate,
            ).toLocaleDateString("pl-PL")}
          </p>

          {sprint.goal && (
            <p className="mt-3 line-clamp-2 wrap-break-word text-sm text-gray-600">
              {sprint.goal}
            </p>
          )}
        </div>

        {/* Right side */}

        <div className="flex flex-wrap gap-2 self-end">
          <button
            type="button"
            onClick={() =>
              onBurndown(sprint.sprintId)
            }
            className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 cursor-pointer"
          >
            Burndown
          </button>

          {canManageSprints && (
            <>
              <button
                type="button"
                onClick={() => onEdit(sprint)}
                className="rounded-md border border-blue-200 px-4 py-2 text-sm font-medium text-blue-700 hover:bg-blue-50 cursor-pointer"
              >
                Edytuj
              </button>

              <button
                type="button"
                onClick={() =>
                  onDelete(sprint.sprintId)
                }
                className="rounded-md border border-red-200 px-4 py-2 text-sm font-medium text-red-700 hover:bg-red-50 cursor-pointer"
              >
                Usuń
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  );
}