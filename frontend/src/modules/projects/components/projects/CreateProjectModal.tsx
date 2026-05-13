// src/modules/projects/components/CreateProjectPanel.tsx

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../../api/client";
import { createProject } from "../../api";
import type { Project } from "../../types";
import { createProjectSchema } from "../../schemas";
import type { CreateProjectFormInput } from "../../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const textareaClass =
  "mt-1 block min-h-[120px] w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

interface CreateProjectPanelProps {
  onCreated?: (project: Project) => void;
  variant?: "panel" | "modal";
}

export default function CreateProjectModal({
  onCreated,
  variant = "panel",
}: CreateProjectPanelProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateProjectFormInput>({
    resolver: zodResolver(createProjectSchema),
    defaultValues: {
      name: "",
      description: "",
    },
  });

  async function onSubmit(values: CreateProjectFormInput) {
    setSubmitError(null);
    setSuccessMessage(null);

    try {
      const createdProject = await createProject({
        name: values.name,
        description: values.description ?? "", 
      });

      onCreated?.(createdProject);
      setSuccessMessage("Projekt został utworzony.");
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
        return;
      }

      setSubmitError("Nie udało się utworzyć projektu. Spróbuj ponownie.");
    }
  }

  const form = (
    <form
      onSubmit={handleSubmit(onSubmit)}
      className="space-y-5"
      noValidate
    >
      <div>
        <label htmlFor="project-name" className={labelClass}>
          Nazwa projektu
        </label>

        <input
          id="project-name"
          type="text"
          autoComplete="off"
          placeholder="np. Platforma CRM"
          aria-invalid={errors.name !== undefined}
          aria-describedby={errors.name ? "project-name-error" : undefined}
          className={inputClass}
          {...register("name")}
        />

        {errors.name && (
          <p id="project-name-error" className={errorClass}>
            {errors.name.message}
          </p>
        )}
      </div>

      <div>
        <label htmlFor="project-description" className={labelClass}>
          Opis projektu
        </label>

        <textarea
          id="project-description"
          placeholder="Krótki opis celu projektu, zakresu oraz kontekstu biznesowego..."
          aria-invalid={errors.description !== undefined}
          aria-describedby={
            errors.description ? "project-description-error" : undefined
          }
          className={textareaClass}
          {...register("description")}
        />

        {errors.description && (
          <p id="project-description-error" className={errorClass}>
            {errors.description.message}
          </p>
        )}
      </div>

      {submitError !== null && (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
          {submitError}
        </div>
      )}

      {successMessage !== null && variant === "panel" && (
        <div className="rounded-md bg-green-50 px-4 py-3 text-sm text-green-700">
          {successMessage}
        </div>
      )}

      <div className="flex justify-end">
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Tworzenie projektu..." : "Utwórz projekt"}
        </button>
      </div>
    </form>
  );

  if (variant === "modal") {
    return form;
  }

  return (
    <section className="rounded-xl bg-white p-6 shadow">
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900">
          Utwórz nowy projekt
        </h2>

        <p className="mt-1 text-sm text-gray-600">
          Dodaj nowy projekt do systemu i rozpocznij planowanie sprintów.
        </p>
      </div>

      {form}
    </section>
  );
}