import { Clock3, Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "react-hot-toast";

import { ApiError } from "../../../api/client";
import { createWorklog, fetchWorklogs } from "../api";
import type { Worklog } from "../../projects/types";

const inputClass =
  "block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm text-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const textareaClass =
  "block min-h-24 w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm text-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

interface WorklogsSectionProps {
  taskId: number;
}

export default function WorklogsSection({ taskId }: WorklogsSectionProps) {
  const [worklogs, setWorklogs] = useState<Worklog[]>([]);
  const [hoursSpent, setHoursSpent] = useState("");
  const [note, setNote] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadWorklogs() {
      setIsLoading(true);
      setError(null);
      try {
        const loadedWorklogs = await fetchWorklogs(taskId);
        if (!cancelled) {
          setWorklogs(loadedWorklogs);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.detail : "Nie udało się pobrać czasu pracy.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadWorklogs();
    return () => {
      cancelled = true;
    };
  }, [taskId]);

  const totalHours = worklogs.reduce((sum, worklog) => sum + worklog.hoursSpent, 0);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFormError(null);

    const parsedHours = Number(hoursSpent.replace(",", "."));
    if (!Number.isFinite(parsedHours) || parsedHours <= 0) {
      setFormError("Podaj liczbę godzin większą od 0.");
      return;
    }

    setIsSubmitting(true);
    try {
      const createdWorklog = await createWorklog(taskId, {
        hoursSpent: parsedHours,
        note: note.trim() === "" ? null : note.trim(),
      });
      setWorklogs((prev) => [...prev, createdWorklog]);
      setHoursSpent("");
      setNote("");
      toast.success("Czas pracy został zapisany.");
    } catch (err) {
      const message = err instanceof ApiError ? err.detail : "Nie udało się zapisać czasu pracy.";
      setFormError(message);
      toast.error("Nie udało się zapisać czasu pracy.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between gap-3">
        <h3 className="flex items-center gap-2 text-lg font-semibold text-slate-800">
          <Clock3 className="h-5 w-5 text-slate-500" />
          Czas pracy
        </h3>
        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-600">
          Suma: {totalHours.toLocaleString("pl-PL", { maximumFractionDigits: 2 })} h
        </span>
      </div>

      <form onSubmit={handleSubmit} className="grid gap-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
        <div className="grid gap-4 md:grid-cols-[180px_1fr]">
          <div>
            <label htmlFor="worklog-hours" className="mb-1 block text-sm font-medium text-slate-700">
              Liczba godzin
            </label>
            <input
              id="worklog-hours"
              type="number"
              min="0.1"
              step="0.1"
              value={hoursSpent}
              onChange={(event) => setHoursSpent(event.target.value)}
              className={inputClass}
              placeholder="Np. 2.5"
              disabled={isSubmitting}
            />
          </div>

          <div>
            <label htmlFor="worklog-note" className="mb-1 block text-sm font-medium text-slate-700">
              Notatka
            </label>
            <textarea
              id="worklog-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              className={textareaClass}
              placeholder="Krótki opis wykonanej pracy"
              disabled={isSubmitting}
            />
          </div>
        </div>

        {formError && (
          <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{formError}</p>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Zapisywanie..." : "Dodaj wpis"}
          </button>
        </div>
      </form>

      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
        </div>
      ) : error ? (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{error}</div>
      ) : worklogs.length === 0 ? (
        <div className="rounded-lg border-2 border-dashed border-slate-300 bg-slate-50 px-4 py-6 text-sm text-slate-500">
          Brak zarejestrowanego czasu pracy dla tego zadania.
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {worklogs.map((worklog) => (
            <article key={worklog.id} className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div>
                  <p className="text-sm font-semibold text-slate-800">
                    {worklog.hoursSpent.toLocaleString("pl-PL", { maximumFractionDigits: 2 })} h
                  </p>
                  <p className="text-xs text-slate-500">
                    {new Date(worklog.createdAt).toLocaleString("pl-PL")}
                  </p>
                </div>
                <span className="text-xs text-slate-400">Worklog #{worklog.id}</span>
              </div>
              <p className="mt-3 whitespace-pre-wrap break-words text-sm text-slate-700">
                {worklog.note && worklog.note.trim() !== "" ? worklog.note : "Brak notatki."}
              </p>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
