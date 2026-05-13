import { useEffect, useState } from "react";

import { useOutletContext } from "react-router-dom";

import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";

import { useDroppable, useDraggable } from "@dnd-kit/core";

import { ApiError } from "../../../api/client";

import { fetchTasks, updateTaskStatus } from "../api";

import type { ProjectDetail, WorkItem, WorkItemStatus } from "../types";

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
  { id: "ToDo", label: "To Do" },
  { id: "InProgress", label: "In Progress" },
  { id: "Done", label: "Done" },
];

const BOARD_STATUSES = new Set<string>(["ToDo", "InProgress", "Done"]);

const PRIORITY_STYLES: Record<string, string> = {
  High: "bg-red-100 text-red-700",
  Medium: "bg-yellow-100 text-yellow-700",
  Low: "bg-green-100 text-green-700",
};

// ============================================================
// TaskCard
// ============================================================

interface TaskCardProps {
  task: WorkItem;
  isDragging?: boolean;
}

function TaskCard({ task, isDragging }: TaskCardProps) {
  const { attributes, listeners, setNodeRef, transform } = useDraggable({ id: task.id });

  const style = transform
    ? { transform: `translate(${transform.x}px, ${transform.y}px)` }
    : undefined;

  return (
    <div
      ref={setNodeRef}
      style={style}
      {...listeners}
      {...attributes}
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
          {task.priority}
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

  const [tasks, setTasks] = useState<WorkItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
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

    async function load() {
      setIsLoading(true);
      setLoadError(null);

      try {
        const response = await fetchTasks(project.projectId);

        if (cancelled) return;

        setTasks(response.filter((t) => BOARD_STATUSES.has(t.status)));
      } catch (err) {
        if (cancelled) return;

        setLoadError(err instanceof ApiError ? err.detail : "Nie udało się pobrać zadań.");
      } finally {
        if (!cancelled) setIsLoading(false);
      }
    }

    load();

    return () => {
      cancelled = true;
    };
  }, [project.projectId]);

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
    { Backlog: [], ToDo: [], InProgress: [], Done: [] },
  );

  const activeTask = tasks.find((t) => t.id === activeTaskId) ?? null;

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
            {activeTask ? <TaskCard task={activeTask} /> : null}
          </DragOverlay>
        </DndContext>
      )}
    </div>
  );
}
