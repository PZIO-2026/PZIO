import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { createTaskType, fetchTaskTypes } from "../api";
import { createTaskTypeSchema } from "../schemas";
import type { CreateTaskTypeFormInput } from "../schemas";
import type { TaskType } from "../types";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

export default function TaskTypesPanel() {
  const [taskTypes, setTaskTypes] = useState<TaskType[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<CreateTaskTypeFormInput>({
    resolver: zodResolver(createTaskTypeSchema),
    defaultValues: { name: "" },
  });

  useEffect(() => {
    let cancelled = false;
    fetchTaskTypes()
      .then((items) => {
        if (cancelled) return;
        setTaskTypes(items);
        setLoadError(null);
      })
      .catch((err) => {
        if (cancelled) return;
        setLoadError(
          err instanceof ApiError ? err.detail : "Nie udało się pobrać listy typów zadań.",
        );
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(values: CreateTaskTypeFormInput) {
    setSubmitError(null);
    try {
      const created = await createTaskType({ name: values.name });
      setTaskTypes((current) => [...current, created]);
      setValue("name", "");
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(
          err.status === 409 ? "Typ zadania o tej nazwie już istnieje." : err.detail,
        );
        return;
      }
      setSubmitError("Nie udało się dodać typu zadania. Spróbuj ponownie.");
    }
  }

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-4 text-xl font-bold text-gray-900">Typy zadań</h2>

      <form onSubmit={handleSubmit(onSubmit)} className="mb-6 space-y-3" noValidate>
        <div>
          <label htmlFor="task-type-name" className={labelClass}>
            Nazwa nowego typu
          </label>
          <input
            id="task-type-name"
            type="text"
            autoComplete="off"
            placeholder="np. Spike"
            aria-invalid={errors.name !== undefined}
            aria-describedby={errors.name ? "task-type-name-error" : undefined}
            className={inputClass}
            {...register("name")}
          />
          {errors.name && (
            <p id="task-type-name-error" className={errorClass}>
              {errors.name.message}
            </p>
          )}
        </div>

        {submitError !== null && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Dodawanie..." : "Dodaj typ"}
          </button>
        </div>
      </form>

      <div className="border-t border-gray-200 pt-4">
        <h3 className="mb-3 text-sm font-medium text-gray-700">Aktualny słownik</h3>
        {isLoading ? (
          <p className="text-sm text-gray-500">Ładowanie...</p>
        ) : loadError !== null ? (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{loadError}</p>
        ) : taskTypes.length === 0 ? (
          <p className="text-sm text-gray-500">Brak zdefiniowanych typów zadań.</p>
        ) : (
          <ul className="divide-y divide-gray-200">
            {taskTypes.map((type) => (
              <li key={type.taskTypeId} className="flex items-center justify-between py-2">
                <span className="font-medium text-gray-900">{type.name}</span>
                <span className="text-xs text-gray-500">
                  dodano {new Date(type.createdAt).toLocaleDateString("pl-PL")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
