import { useState } from "react";

import { ApiError } from "../../../api/client";
import { createBackup } from "../api";
import type { BackupResponse } from "../types";

export default function BackupsPanel() {
  const [isRunning, setIsRunning] = useState(false);
  const [lastBackup, setLastBackup] = useState<BackupResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setIsRunning(true);
    setError(null);
    try {
      const result = await createBackup();
      setLastBackup(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(err.detail);
      } else {
        setError("Nie udało się wykonać kopii zapasowej. Spróbuj ponownie.");
      }
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <section className="rounded-lg bg-white p-6 shadow">
      <h2 className="mb-2 text-xl font-bold text-gray-900">Kopia zapasowa bazy</h2>
      <p className="mb-4 text-sm text-gray-600">
        Wymusza utworzenie kopii pliku bazy SQLite w katalogu skonfigurowanym po stronie serwera
        ({" "}
        <code className="rounded bg-gray-100 px-1 py-0.5 text-xs">BACKUP_DIR</code>).
      </p>

      <button
        type="button"
        onClick={handleClick}
        disabled={isRunning}
        className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isRunning ? "Tworzenie kopii..." : "Wymuś kopię zapasową"}
      </button>

      {error !== null && (
        <p className="mt-4 rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
      )}

      {lastBackup !== null && (
        <div className="mt-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-800">
          Kopia zapasowa #{lastBackup.backupId} utworzona{" "}
          {new Date(lastBackup.timestamp).toLocaleString("pl-PL")} (status:{" "}
          <span className="font-medium">{lastBackup.status}</span>).
        </div>
      )}
    </section>
  );
}
