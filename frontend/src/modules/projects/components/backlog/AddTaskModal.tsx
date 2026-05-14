import { useEffect, useState } from "react";

import { useForm, useWatch, type Resolver } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { fetchTaskTypes } from "../../../admin/api";
import type { TaskType } from "../../../admin/types";

import { createTask, fetchTasks } from "../../api";

import type { WorkItem } from "../../types";

import { taskFormSchema, type TaskFormInput } from "../../schemas";

import TaskFormFields from "./TaskFormFields";

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
  const [taskTypesLoading, setTaskTypesLoading] = useState(false);
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

    setTaskTypesLoading(true);
    fetchTaskTypes().then(setTaskTypes).catch(() => {}).finally(() => setTaskTypesLoading(false));
    fetchTasks(projectId).then(setAllTasks).catch(() => {});
  }, [isOpen, projectId]);

  // ============================================================
  // Handlers
  // ============================================================

  async function onSubmit(values: TaskFormInput) {
    setSubmitError(null);

    try {
      const created = await createTask(projectId, { ...values, status: "ToDo" });

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
        <TaskFormFields
          register={register}
          errors={errors}
          setValue={setValue}
          parentId={parentId}
          taskTypes={taskTypes}
          taskTypesLoading={taskTypesLoading}
          allTasks={allTasks}
        />

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
