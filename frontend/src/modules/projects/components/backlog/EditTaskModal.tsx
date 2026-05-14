import { useEffect, useState } from "react";

import { useForm, useWatch, type Resolver } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { fetchTaskTypes } from "../../../admin/api";
import type { TaskType } from "../../../admin/types";

import { fetchTasks, updateTask } from "../../api";

import type { WorkItem } from "../../types";

import { taskFormSchema, type TaskFormInput } from "../../schemas";

import TaskFormFields from "./TaskFormFields";

// ============================================================
// Props
// ============================================================

interface Props {
  isOpen: boolean;
  onClose: () => void;
  task: WorkItem | null;
  projectId: number;
  onTaskUpdated: (task: WorkItem) => void;
}

// ============================================================
// Component
// ============================================================

export default function EditTaskModal({ isOpen, onClose, task, projectId, onTaskUpdated }: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);
  const [allTasks, setAllTasks] = useState<WorkItem[]>([]);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    control,
    formState: { errors, isSubmitting },
  } = useForm<TaskFormInput>({
    resolver: zodResolver(taskFormSchema) as Resolver<TaskFormInput>,
    defaultValues: {
      title: "",
      description: "",
      type: "",
      priority: "Medium",
      storyPoints: undefined,
      parentId: null,
    },
  });

  const parentId = useWatch({ control, name: "parentId" }) ?? null;

  // ============================================================
  // Effects
  // ============================================================

  useEffect(() => {
    if (!isOpen) return;

    fetchTaskTypes().then(setTaskTypes).catch(() => {});
    fetchTasks(projectId).then(setAllTasks).catch(() => {});
  }, [isOpen, projectId]);

  useEffect(() => {
    if (!task) return;

    reset({
      title: task.title,
      description: task.description ?? "",
      type: task.type,
      priority: task.priority as TaskFormInput["priority"],
      storyPoints: task.storyPoints ?? undefined,
      parentId: task.parentId ?? null,
    });
  }, [task, reset]);

  // ============================================================
  // Handlers
  // ============================================================

  async function onSubmit(values: TaskFormInput) {
    if (!task) return;

    setSubmitError(null);

    try {
      const updated = await updateTask(task.id, values);

      onTaskUpdated(updated);
      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError("Nie udało się zaktualizować zadania.");
      }
    }
  }

  // ============================================================
  // Render
  // ============================================================

  return (
    <Modal title="Edytuj zadanie" isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <TaskFormFields
          register={register}
          errors={errors}
          setValue={setValue}
          parentId={parentId}
          taskTypes={taskTypes}
          allTasks={allTasks}
          editingTaskId={task?.id}
        />

        {submitError && (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{submitError}</div>
        )}

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50 cursor-pointer"
          >
            Anuluj
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60 cursor-pointer"
          >
            {isSubmitting ? "Zapisywanie..." : "Zapisz zmiany"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
