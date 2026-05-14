import type { SprintStatus } from "../types";

export const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

export const errorClass =
  "mt-1 text-sm text-red-600";

export const statusLabels: Record<
  SprintStatus,
  string
> = {
  planned: "Zaplanowany",
  active: "Aktywny",
  completed: "Ukończony",
};

export const statusStyles: Record<
  SprintStatus,
  string
> = {
  planned: "bg-gray-100 text-gray-700",
  active: "bg-green-100 text-green-700",
  completed: "bg-blue-100 text-blue-700",
};