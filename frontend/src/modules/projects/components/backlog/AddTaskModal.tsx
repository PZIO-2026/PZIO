import { useEffect, useMemo, useState } from "react";

import { useForm, useWatch, type Resolver } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { fetchTaskTypes } from "../../../admin/api";
import type { TaskType } from "../../../admin/types";

import { createTask, fetchTasks } from "../../api";

import type { Project, WorkItem } from "../../types";

import { taskFormSchema, type TaskFormInput } from "../../schemas";

import TaskFormFields from "./TaskFormFields";

interface Props {
  isOpen: boolean;
  onClose: () => void;
  projectId?: number;
  projectOptions?: Project[];
  onTaskCreated: (task: WorkItem) => void;
  title?: string;
}

export default function AddTaskModal({
  isOpen,
  onClose,
  projectId,
  projectOptions,
  onTaskCreated,
  title = "Dodaj element do backlogu",
}: Props) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);
  const [taskTypesLoading, setTaskTypesLoading] = useState(false);
  const [allTasks, setAllTasks] = useState<WorkItem[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<number | null>(projectId ?? null);

  const availableProjects = useMemo(() => projectOptions ?? [], [projectOptions]);
  const requiresProjectSelection = projectId === undefined;

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

  function resetModalState(nextProjectId: number | null) {
    setSubmitError(null);
    reset();
    setSelectedProjectId(nextProjectId);
  }

  async function loadTaskTypeOptions() {
    setTaskTypesLoading(true);
    try {
      setTaskTypes(await fetchTaskTypes());
    } catch {
      setTaskTypes([]);
    } finally {
      setTaskTypesLoading(false);
    }
  }

  async function loadProjectTasks(nextProjectId: number) {
    try {
      const tasks = await fetchTasks(nextProjectId);
      setAllTasks((current) => (selectedProjectId === nextProjectId ? tasks : current));
    } catch {
      setAllTasks((current) => (selectedProjectId === nextProjectId ? [] : current));
    }
  }

  function clearProjectTasks() {
    setAllTasks([]);
  }

  useEffect(() => {
    if (!isOpen) return;

    resetModalState(projectId ?? availableProjects[0]?.projectId ?? null);
  }, [isOpen, projectId, availableProjects, reset]);

  useEffect(() => {
    if (!isOpen) return;

    void loadTaskTypeOptions();
  }, [isOpen]);

  useEffect(() => {
    if (!isOpen || selectedProjectId === null) {
      clearProjectTasks();
      return;
    }

    void loadProjectTasks(selectedProjectId);
  }, [isOpen, selectedProjectId]);

  async function onSubmit(values: TaskFormInput) {
    setSubmitError(null);

    if (selectedProjectId === null) {
      setSubmitError("Wybierz projekt.");
      return;
    }

    try {
      const created = await createTask(selectedProjectId, { ...values, status: "ToDo" });

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

  return (
    <Modal title={title} isOpen={isOpen} onClose={onClose}>
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        {requiresProjectSelection && (
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">
              Projekt <span className="text-red-500">*</span>
            </label>
            <select
              value={selectedProjectId ?? ""}
              onChange={(e) => setSelectedProjectId(e.target.value ? Number(e.target.value) : null)}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none disabled:bg-gray-50 disabled:text-gray-400"
            >
              {availableProjects.length === 0 ? (
                <option value="">Brak dostępnych projektów</option>
              ) : (
                availableProjects.map((project) => (
                  <option key={project.projectId} value={project.projectId}>
                    {project.name}
                  </option>
                ))
              )}
            </select>
          </div>
        )}

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
            disabled={isSubmitting || selectedProjectId === null}
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60 cursor-pointer"
          >
            {isSubmitting ? "Zapisywanie..." : "Zapisz"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
