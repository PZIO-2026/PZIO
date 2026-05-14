import type { FieldErrors, UseFormRegister, UseFormSetValue } from "react-hook-form";

import type { TaskType } from "../../../admin/types";

import type { TaskFormInput } from "../../schemas";
import type { WorkItem } from "../../types";

import ParentTaskSearch from "./ParentTaskSearch";

// ============================================================
// Props
// ============================================================

interface Props {
  register: UseFormRegister<TaskFormInput>;
  errors: FieldErrors<TaskFormInput>;
  setValue: UseFormSetValue<TaskFormInput>;
  parentId: number | null;
  taskTypes: TaskType[];
  taskTypesLoading: boolean;
  allTasks: WorkItem[];
  editingTaskId?: number;
}

// ============================================================
// Component
// ============================================================

export default function TaskFormFields({
  register,
  errors,
  setValue,
  parentId,
  taskTypes,
  taskTypesLoading,
  allTasks,
  editingTaskId,
}: Props) {
  return (
    <>
      {/* Title */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Tytuł <span className="text-red-500">*</span>
        </label>
        <input
          type="text"
          {...register("title")}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          placeholder="Tytuł zadania"
        />
        {errors.title && (
          <p className="mt-1 text-xs text-red-600">{errors.title.message}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Opis</label>
        <textarea
          {...register("description")}
          rows={3}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          placeholder="Opcjonalny opis"
        />
        {errors.description && (
          <p className="mt-1 text-xs text-red-600">{errors.description.message}</p>
        )}
      </div>

      {/* Type */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">
          Typ <span className="text-red-500">*</span>
        </label>
        <select
          {...register("type")}
          disabled={taskTypesLoading}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
        >
          <option value="">{taskTypesLoading ? "Ładowanie..." : "Wybierz typ"}</option>
          {taskTypes.map((t) => (
            <option key={t.taskTypeId} value={t.name}>
              {t.name}
            </option>
          ))}
        </select>
        {errors.type && (
          <p className="mt-1 text-xs text-red-600">{errors.type.message}</p>
        )}
      </div>

      {/* Priority + Story Points */}
      <div className="flex gap-4">
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-gray-700">
            Priorytet <span className="text-red-500">*</span>
          </label>
          <select
            {...register("priority")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          >
            <option value="Low">Niski</option>
            <option value="Medium">Średni</option>
            <option value="High">Wysoki</option>
          </select>
          {errors.priority && (
            <p className="mt-1 text-xs text-red-600">{errors.priority.message}</p>
          )}
        </div>

        <div className="w-32">
          <label className="mb-1 block text-sm font-medium text-gray-700">Story Points</label>
          <input
            type="number"
            min={0}
            {...register("storyPoints")}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            placeholder="0"
          />
          {errors.storyPoints && (
            <p className="mt-1 text-xs text-red-600">{errors.storyPoints.message}</p>
          )}
        </div>
      </div>

      {/* Parent Task */}
      <div>
        <label className="mb-1 block text-sm font-medium text-gray-700">Zadanie nadrzędne</label>
        <ParentTaskSearch
          allTasks={allTasks}
          excludeId={editingTaskId}
          value={parentId}
          onChange={(id) => setValue("parentId", id, { shouldDirty: true })}
        />
      </div>
    </>
  );
}
