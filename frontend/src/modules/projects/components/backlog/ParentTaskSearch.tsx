import { useEffect, useRef, useState } from "react";

import type { WorkItem } from "../../types";

// ============================================================
// Props
// ============================================================

interface Props {
  allTasks: WorkItem[];
  excludeId?: number;
  value: number | null;
  onChange: (id: number | null) => void;
}

// ============================================================
// Component
// ============================================================

export default function ParentTaskSearch({ allTasks, excludeId, value, onChange }: Props) {
  const [query, setQuery] = useState("");
  const [open, setOpen] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const selectedTask = allTasks.find((t) => t.id === value) ?? null;

  const filtered = allTasks.filter(
    (t) =>
      t.id !== excludeId &&
      t.title.toLowerCase().includes(query.toLowerCase()),
  );

  // Close dropdown on outside click
  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  function handleSelect(task: WorkItem) {
    onChange(task.id);
    setQuery("");
    setOpen(false);
  }

  function handleClear() {
    onChange(null);
    setQuery("");
  }

  return (
    <div ref={containerRef} className="relative">
      {selectedTask ? (
        <div className="flex items-center justify-between rounded-md border border-gray-300 px-3 py-2 text-sm bg-gray-50">
          <span className="text-gray-800 truncate">
            <span className="text-gray-400 mr-1">#{selectedTask.id}</span>
            {selectedTask.title}
          </span>
          <button
            type="button"
            onClick={handleClear}
            className="ml-2 shrink-0 text-gray-400 hover:text-gray-600"
            aria-label="Usuń wybór"
          >
            ✕
          </button>
        </div>
      ) : (
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Szukaj zadania..."
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
        />
      )}

      {open && !selectedTask && (
        <div className="absolute z-10 mt-1 w-full rounded-md border border-gray-200 bg-white shadow-lg max-h-48 overflow-y-auto">
          {filtered.length === 0 ? (
            <p className="px-3 py-2 text-sm text-gray-500">Brak wyników</p>
          ) : (
            filtered.map((task) => (
              <button
                key={task.id}
                type="button"
                onClick={() => handleSelect(task)}
                className="flex w-full items-center gap-2 px-3 py-2 text-left text-sm hover:bg-gray-50"
              >
                <span className="shrink-0 text-gray-400">#{task.id}</span>
                <span className="truncate text-gray-800">{task.title}</span>
                <span className="ml-auto shrink-0 rounded-full bg-blue-50 px-2 py-0.5 text-xs text-blue-700">
                  {task.type}
                </span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}
