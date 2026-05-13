import { useEffect, useState } from "react";

import { useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { fetchTaskTypes } from "../../../admin/api";
import type { TaskType } from "../../../admin/types";

import { createTask } from "../../api";

import type { WorkItem } from "../../types";

import { createTaskSchema, type CreateTaskFormInput } from "../../schemas";

// ============================================================
// Props
// ============================================================

interface Props {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;
  onTaskCreated: (task: WorkItem) => void;
}

// ============================================================
// Component
// ============================================================

export default function AddTaskModal({ isOpen, onClose, projectId, onTaskCreated }: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateTaskFormInput>({
    resolver: zodResolver(createTaskSchema),
    defaultValues: {
      title: "",
      description: "",
      type: "",
      priority: "Medium",
      storyPoints: undefined,
    },
  });

  // ============================================================
  // Effects
  // ============================================================

  useEffect(() => {
    if (!isOpen) return;

    fetchTaskTypes()
      .then(setTaskTypes)
      .catch(() => {});
  }, [isOpen]);

  // ============================================================
  // Handlers
  // ============================================================

  async function onSubmit(values: CreateTaskFormInput) {
    setSubmitError(null);

    try {
      const created = await createTask(projectId, { ...values, status: "Backlog" });

      onTaskCreated(created);
      reset();
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError("Nie udało się utworzyć zadania.");
      }
    }
  }

  // ============================================================
  // Render
  // ============================================================

  return (
    <Modal title="Dodaj element do backlogu" isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">

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
          {taskTypes.length > 0 ? (
            <select
              {...register("type")}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            >
              <option value="">Wybierz typ</option>
              {taskTypes.map((t) => (
                <option key={t.taskTypeId} value={t.name}>
                  {t.name}
                </option>
              ))}
            </select>
          ) : (
            <input
              type="text"
              {...register("type")}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
              placeholder="Np. Task, Bug, Story"
            />
          )}
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
              <option value="Low">Low</option>
              <option value="Medium">Medium</option>
              <option value="High">High</option>
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

        {submitError && (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{submitError}</div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60 cursor-pointer"
          >
            {isSubmitting ? "Zapisywanie..." : "Zapisz"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
