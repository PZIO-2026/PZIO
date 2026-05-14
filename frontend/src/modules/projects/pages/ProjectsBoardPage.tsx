import { useEffect, useState } from "react";

import { useNavigate, useOutletContext } from "react-router-dom";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  useDroppable,
  useDraggable,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";

import { ApiError } from "../../../api/client";

import { fetchSprints, fetchTasks, updateTaskStatus } from "../api";

import type { ProjectDetail, Sprint, WorkItem, WorkItemStatus } from "../types";

import {
  statusLabels,
  statusStyles,
} from "../constants/sprintForm.constants";

// ============================================================
// Context
// ============================================================

interface OutletContext {
  project: ProjectDetail;
}

// ============================================================
// Constants
// ============================================================

const COLUMNS: { id: WorkItemStatus; label: string }[] = [
  { id: "ToDo", label: "Do zrobienia" },
  { id: "InProgress", label: "W trakcie" },
  { id: "Done", label: "Ukończone" },
];

const PRIORITY_STYLES: Record<string, string> = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

const PRIORITY_LABELS: Record<string, string> = {
  High: "Wysoki",
  Medium: "Średni",
  Low: "Niski",
};

// ============================================================
// Helpers
// ============================================================

function daysLeft(endDate: string): number {
  const end = new Date(endDate);
  end.setHours(0, 0, 0, 0);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  return Math.ceil((end.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));
}

function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("pl-PL");
}

// ============================================================
// SprintHeader
// ============================================================

interface SprintHeaderProps {
  sprints: Sprint[];
  selected: Sprint | null;
  onSelect: (sprint: Sprint) => void;
}

function SprintHeader({ sprints, selected, onSelect }: SprintHeaderProps) {
  const remaining = selected ? daysLeft(selected.endDate) : null;

  return (
    <div className="mb-6 flex flex-wrap items-center gap-4 rounded-xl border border-blue-100 bg-blue-50 px-5 py-4">
      <div className="flex flex-1 min-w-0 flex-col gap-1">
        <p className="text-xs font-medium uppercase tracking-wide text-blue-500">Sprint</p>
        {sprints.length === 0 ? (
          <p className="text-sm text-blue-700">Brak sprintów</p>
        ) : (
          <select
            value={selected?.sprintId ?? ""}
            onChange={(e) => {
              const sprint = sprints.find((s) => s.sprintId === Number(e.target.value));
              if (sprint) onSelect(sprint);
            }}
            className="w-fit rounded-md border border-blue-200 bg-white px-3 py-1.5 text-sm font-semibold text-blue-900 focus:border-blue-400 focus:outline-none"
          >
            {sprints.map((s) => (
              <option key={s.sprintId} value={s.sprintId}>
                {s.name}
              </option>
            ))}
          </select>
        )}
      </div>

      {selected && (
        <div className="flex flex-wrap items-center gap-4 text-sm text-blue-700">
          <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${statusStyles[selected.status]}`}>
            {statusLabels[selected.status]}
          </span>
          <span>
            {formatDate(selected.startDate)} — {formatDate(selected.endDate)}
          </span>
          {remaining !== null && (
            <span
              className={`font-semibold ${remaining < 0 ? "text-red-600" : remaining <= 3 ? "text-orange-600" : "text-blue-800"}`}
            >
              {remaining < 0
                ? `Przekroczono o ${Math.abs(remaining)} dni`
                : remaining === 0
                  ? "Ostatni dzień"
                  : `${remaining} dni pozostało`}
            </span>
          )}
        </div>
      )}
    </div>
  );
}

// ============================================================
// TaskCard
// ============================================================

interface TaskCardProps {
  task: WorkItem;
  isDragging?: boolean;
}

function TaskCard({ task, isDragging }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: task.id });
  const navigate = useNavigate();

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
      onClick={() => navigate(`/tasks/${task.id}`)}
      className={`cursor-grab rounded-lg border border-gray-200 bg-white p-3 shadow-sm select-none active:cursor-grabbing ${isDragging ? "opacity-40" : ""}`}
    >
      <p className="text-sm font-medium text-gray-900">{task.title}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
          {task.type}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-600"}`}
        >
          {PRIORITY_LABELS[task.priority] ?? task.priority}
        </span>
        {task.storyPoints !== null && (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {task.storyPoints} SP
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================
// TaskCardOverlay (no dnd hooks — used only inside DragOverlay)
// ============================================================

function TaskCardOverlay({ task }: { task: WorkItem }) {
  return (
    <div className="cursor-grabbing rounded-lg border border-gray-200 bg-white p-3 shadow-lg select-none">
      <p className="text-sm font-medium text-gray-900">{task.title}</p>
      <div className="mt-2 flex flex-wrap items-center gap-1.5">
        <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
          {task.type}
        </span>
        <span
          className={`rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_STYLES[task.priority] ?? "bg-gray-100 text-gray-600"}`}
        >
          {PRIORITY_LABELS[task.priority] ?? task.priority}
        </span>
        {task.storyPoints !== null && (
          <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
            {task.storyPoints} SP
          </span>
        )}
      </div>
    </div>
  );
}

// ============================================================
// KanbanColumn
// ============================================================

interface KanbanColumnProps {
  id: WorkItemStatus;
  label: string;
  tasks: WorkItem[];
  activeTaskId: number | null;
}

function KanbanColumn({ id, label, tasks, activeTaskId }: KanbanColumnProps) {
  const { setNodeRef, isOver } = useDroppable({ id });

  return (
    <div className="flex flex-1 flex-col min-w-60">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="font-semibold text-gray-700">{label}</h2>
        <span className="rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-600">
          {tasks.length}
        </span>
      </div>
      <div
        ref={setNodeRef}
        className={`flex flex-1 flex-col gap-2 rounded-xl p-3 transition-colors ${isOver ? "bg-blue-50 ring-2 ring-blue-300" : "bg-gray-100"}`}
        style={{ minHeight: 120 }}
      >
        {tasks.map((task) => (
          <TaskCard key={task.id} task={task} isDragging={task.id === activeTaskId} />
        ))}
      </div>
    </div>
  );
}

// ============================================================
// ProjectsBoardPage
// ============================================================

export default function ProjectsBoardPage() {
  const { project } = useOutletContext<OutletContext>();

  const [sprints, setSprints] = useState<Sprint[]>([]);
  const [selectedSprint, setSelectedSprint] = useState<Sprint | null>(null);
  const [tasks, setTasks] = useState<WorkItem[]>([]);
  const [isLoadingSprints, setIsLoadingSprints] = useState(true);
  const [isLoadingTasks, setIsLoadingTasks] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [activeTaskId, setActiveTaskId] = useState<number | null>(null);

  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 5 } }),
  );

  // ============================================================
  // Effects
  // ============================================================

  useEffect(() => {
    let cancelled = false;

    async function loadSprints() {
      setIsLoadingSprints(true);
      setLoadError(null);

      try {
        const sprintList = await fetchSprints(project.projectId);

        if (cancelled) return;

        setSprints(sprintList);
        const active = sprintList.find((s) => s.status === "active");
        setSelectedSprint(active ?? sprintList[0] ?? null);
      } catch (err) {
        if (cancelled) return;
        setLoadError(err instanceof ApiError ? err.detail : "Nie udało się pobrać sprintów.");
      } finally {
        if (!cancelled) setIsLoadingSprints(false);
      }
    }

    loadSprints();

    return () => {
      cancelled = true;
    };
  }, [project.projectId]);

  useEffect(() => {
    if (!selectedSprint) {
      setTasks([]);
      return;
    }

    const sprint = selectedSprint;
    let cancelled = false;

    async function loadTasks() {
      setIsLoadingTasks(true);
      setLoadError(null);

      try {
        const taskList = await fetchTasks(project.projectId, { sprintId: sprint.sprintId });

        if (cancelled) return;

        setTasks(taskList);
      } catch (err) {
        if (cancelled) return;
        setLoadError(err instanceof ApiError ? err.detail : "Nie udało się pobrać zadań.");
      } finally {
        if (!cancelled) setIsLoadingTasks(false);
      }
    }

    loadTasks();

    return () => {
      cancelled = true;
    };
  }, [selectedSprint?.sprintId, project.projectId]);

  // ============================================================
  // Drag handlers
  // ============================================================

  function handleDragStart(event: DragStartEvent) {
    setActiveTaskId(event.active.id as number);
  }

  async function handleDragEnd(event: DragEndEvent) {
    setActiveTaskId(null);

    const { active, over } = event;
    if (!over) return;

    const taskId = active.id as number;
    const newStatus = over.id as WorkItemStatus;

    const task = tasks.find((t) => t.id === taskId);
    if (!task || task.status === newStatus) return;

    const previousTasks = tasks;
    setTasks((current) =>
      current.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t)),
    );

    try {
      await updateTaskStatus(taskId, newStatus);
    } catch {
      setTasks(previousTasks);
    }
  }

  // ============================================================
  // Derived state
  // ============================================================

  const tasksByStatus = COLUMNS.reduce<Record<WorkItemStatus, WorkItem[]>>(
    (acc, col) => {
      acc[col.id] = tasks.filter((t) => t.status === col.id);
      return acc;
    },
    { ToDo: [], InProgress: [], Done: [] } as Record<WorkItemStatus, WorkItem[]>,
  );

  const activeTask = tasks.find((t) => t.id === activeTaskId) ?? null;

  const isLoading = isLoadingSprints || isLoadingTasks;

  // ============================================================
  // Render
  // ============================================================

  return (
    <div className="rounded-2xl bg-white p-6 shadow">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Tablica Kanban</h1>

      {isLoading ? (
        <div className="py-10 text-center text-sm text-gray-500">Ładowanie tablicy...</div>
      ) : loadError !== null ? (
        <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">{loadError}</div>
      ) : (
        <>
          <SprintHeader
            sprints={sprints}
            selected={selectedSprint}
            onSelect={setSelectedSprint}
          />

          {selectedSprint === null ? (
            <div className="rounded-xl border border-dashed border-gray-300 px-5 py-10 text-center text-sm text-gray-500">
              Brak sprintów w tym projekcie.
            </div>
          ) : (
            <DndContext sensors={sensors} onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
              <div className="flex gap-4 overflow-x-auto pb-2">
                {COLUMNS.map((col) => (
                  <KanbanColumn
                    key={col.id}
                    id={col.id}
                    label={col.label}
                    tasks={tasksByStatus[col.id]}
                    activeTaskId={activeTaskId}
                  />
                ))}
              </div>

              <DragOverlay>
                {activeTask ? <TaskCardOverlay task={activeTask} /> : null}
              </DragOverlay>
            </DndContext>
          )}
        </>
      )}
    </div>
  );
}
