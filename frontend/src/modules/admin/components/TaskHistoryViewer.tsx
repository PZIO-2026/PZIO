import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { fetchTaskHistory } from "../api";
import { taskHistorySchema } from "../schemas";
import type { TaskHistoryFormInput } from "../schemas";
import type { ActivityLogEntry } from "../types";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

const entryPluralRules = new Intl.PluralRules("pl");

function formatEntryCount(n: number): string {
  switch (entryPluralRules.select(n)) {
    case "one":
      return "wpis";
    case "few":
      return "wpisy";
    default:
      return "wpisów";
  }
}

interface LoadedHistory {
  taskId: number;
  entries: ActivityLogEntry[];
}

export default function TaskHistoryViewer() {
  const [history, setHistory] = useState<LoadedHistory | null>(null);
  const [error, setError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<TaskHistoryFormInput>({
    resolver: zodResolver(taskHistorySchema),
  });

  async function onSubmit(values: TaskHistoryFormInput) {
    setError(null);
    try {
      const entries = await fetchTaskHistory(values.taskId);
      setHistory({ taskId: values.taskId, entries });
    } catch (err) {
      setHistory(null);
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Nie udało się pobrać historii zadania. Spróbuj ponownie.");
      }
    }
  }

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-2 text-xl font-bold text-gray-900">Historia zmian zadania</h2>
      <p className="mb-4 text-sm text-gray-600">
        Wprowadź identyfikator zadania, aby zobaczyć jego dziennik audytu (ActivityLog).
      </p>

      <form
        onSubmit={handleSubmit(onSubmit)}
        className="mb-6 flex flex-col gap-3 sm:flex-row sm:items-end"
        noValidate
      >
        <div className="flex-1">
          <label htmlFor="history-task-id" className={labelClass}>
            ID zadania
          </label>
          <input
            id="history-task-id"
            type="number"
            min={1}
            inputMode="numeric"
            aria-invalid={errors.taskId !== undefined}
            aria-describedby={errors.taskId ? "history-task-id-error" : undefined}
            className={inputClass}
            {...register("taskId", { valueAsNumber: true })}
          />
          {errors.taskId && (
            <p id="history-task-id-error" className={errorClass}>
              {errors.taskId.message}
            </p>
          )}
        </div>

        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Pobieranie..." : "Pokaż historię"}
        </button>
      </form>

      {error !== null && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      {history !== null && error === null && (
        <div>
          <h3 className="mb-2 text-sm font-medium text-gray-700">
            Zadanie #{history.taskId} — {history.entries.length}{" "}
            {formatEntryCount(history.entries.length)}
          </h3>
          {history.entries.length === 0 ? (
            <p className="text-sm text-gray-500">
              Brak zarejestrowanych zmian dla tego zadania.
            </p>
          ) : (
            <ul className="divide-y divide-gray-200 text-sm">
              {history.entries.map((entry) => (
                <li key={entry.activityLogId} className="py-3">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-900">{entry.action}</span>
                    <span className="text-xs text-gray-500">
                      {new Date(entry.createdAt).toLocaleString("pl-PL")}
                    </span>
                  </div>
                  {entry.fieldName !== null && (
                    <p className="mt-1 text-gray-600">
                      Pole <span className="font-medium">{entry.fieldName}</span>:{" "}
                      <span className="text-red-600 line-through">{entry.oldValue ?? "—"}</span>
                      {" → "}
                      <span className="text-green-700">{entry.newValue ?? "—"}</span>
                    </p>
                  )}
                  <p className="mt-1 text-xs text-gray-500">Autor zmiany: użytkownik #{entry.userId}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </section>
  );
}
