import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { useOutletContext } from "react-router-dom";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { updateProject } from "../api";
import {
  updateProjectSchema,
  type UpdateProjectFormInput,
} from "../schemas";
import type { Project, ProjectDetail, ProjectStatus } from "../types";

interface OutletContext {
  project: ProjectDetail;
  onProjectUpdated: (project: Project) => void;
}

const inputClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "mb-1 block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

const statusLabels: Record<ProjectStatus, string> = {
  active: "Aktywny",
  archived: "Zarchiwizowany",
};

const statusStyles: Record<ProjectStatus, string> = {
  active:
    "inline-flex rounded-full bg-green-100 px-2.5 py-1 text-xs font-medium text-green-700",
  archived:
    "inline-flex rounded-full bg-gray-100 px-2.5 py-1 text-xs font-medium text-gray-700",
};

export default function ProjectOverviewPage() {
  const { project, onProjectUpdated } =
    useOutletContext<OutletContext>();

  const [isEditing, setIsEditing] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const canEditProject = project.currentUserRoles.includes("project_owner");

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<UpdateProjectFormInput>({
    resolver: zodResolver(updateProjectSchema),
    defaultValues: {
      name: project.name,
      description: project.description ?? "",
      status: project.status,
    },
  });

  useEffect(() => {
    reset({
      name: project.name,
      description: project.description ?? "",
      status: project.status,
    });
  }, [project, reset]);

  function handleCancelEdit() {
    setSubmitError(null);
    reset({
      name: project.name,
      description: project.description ?? "",
      status: project.status,
    });
    setIsEditing(false);
  }

  async function onSubmit(values: UpdateProjectFormInput) {
    setSubmitError(null);

    try {
      const updatedProject = await updateProject(project.projectId, {
        name: values.name,
        description: values.description ?? "",
        status: values.status,
      });

      onProjectUpdated(updatedProject);
      setIsEditing(false);
    } catch (err) {
      setSubmitError(
        err instanceof ApiError
          ? err.detail
          : "Nie udało się zaktualizować projektu.",
      );
    }
  }

  return (
    <div className="space-y-6">
      <section className="rounded-2xl bg-white p-6 shadow">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div className="min-w-0 flex-1">
            {isEditing ? (
              <form
                onSubmit={handleSubmit(onSubmit)}
                className="max-w-full space-y-5"
              >
                <div>
                  <label htmlFor="project-name" className={labelClass}>
                    Nazwa projektu
                  </label>

                  <input
                    id="project-name"
                    type="text"
                    className={inputClass}
                    aria-invalid={errors.name !== undefined}
                    {...register("name")}
                  />

                  {errors.name && (
                    <p className={errorClass}>{errors.name.message}</p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="project-status"
                    className={labelClass}
                  >
                    Status
                  </label>

                  <select
                    id="project-status"
                    className={inputClass}
                    aria-invalid={errors.status !== undefined}
                    {...register("status")}
                  >
                    <option value="active">Aktywny</option>
                    <option value="archived">Zarchiwizowany</option>
                  </select>

                  {errors.status && (
                    <p className={errorClass}>
                      {errors.status.message}
                    </p>
                  )}
                </div>

                <div>
                  <label
                    htmlFor="project-description"
                    className={labelClass}
                  >
                    Opis
                  </label>

                  <textarea
                    id="project-description"
                    rows={5}
                    className={inputClass}
                    aria-invalid={errors.description !== undefined}
                    {...register("description")}
                  />

                  {errors.description && (
                    <p className={errorClass}>
                      {errors.description.message}
                    </p>
                  )}
                </div>

                {submitError && (
                  <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
                    {submitError}
                  </div>
                )}

                <div className="flex flex-wrap justify-end gap-3">
                  <button
                    type="button"
                    onClick={handleCancelEdit}
                    className="rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
                  >
                    Anuluj
                  </button>

                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="rounded-md bg-blue-600 px-5 py-2.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {isSubmitting ? "Zapisywanie..." : "Zapisz zmiany"}
                  </button>
                </div>
              </form>
            ) : (
              <>
                

                <div className="flex justify-between items-start gap-2 flex-wrap">
                  <div>
                    <h1 className="break-words text-3xl font-bold text-gray-900 mb-2">
                      {project.name}
                    </h1>
                    <div className="mb-3 flex items-center gap-2">
                      <span className={statusStyles[project.status]}>
                        {statusLabels[project.status]}
                      </span>
                    </div>
                  </div>
                  <div className="flex flex-col gap-3 lg:items-end">
                    <div className="rounded-xl border border-gray-200 bg-gray-50 px-4 py-3 text-sm text-gray-600">
                      Utworzono{" "}
                      <span className="font-medium text-gray-900">
                        {new Date(project.createdAt).toLocaleDateString("pl-PL")}
                      </span>
                    </div>
                  </div>
                </div>


                <p className="mt-3 w-full whitespace-pre-wrap break-words text-sm leading-6 text-gray-600">
                  {project.description || "Brak opisu projektu."}
                </p>
              </>
            )}
          </div>

        </div>

        {canEditProject && !isEditing && (
          <div className="flex justify-end mt-2">
            <button
              type="button"
              onClick={() => setIsEditing(true)}
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
            >
              Edytuj projekt
            </button>
          </div>
        )}

      </section>

      <section className="grid gap-6 md:grid-cols-2">
        <div className="rounded-2xl bg-white p-6 shadow">
          <p className="text-sm font-medium text-gray-500">
            Członkowie projektu
          </p>

          <p className="mt-3 text-4xl font-bold text-gray-900">
            {project.stats.memberCount}
          </p>
        </div>

        <div className="rounded-2xl bg-white p-6 shadow">
          <p className="text-sm font-medium text-gray-500">
            Sprinty
          </p>

          <p className="mt-3 text-4xl font-bold text-gray-900">
            {project.stats.sprintCount}
          </p>
        </div>
      </section>
    </div>
  );
}