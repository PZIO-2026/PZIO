import AttachmentsSection from "./AttachmentsSection";
import CommentsSection from "./CommentsSection";

interface TaskCommunicationPanelProps {
  taskId: number;
}

export default function TaskCommunicationPanel({ taskId }: TaskCommunicationPanelProps) {
  return (
    <div className="flex flex-col gap-6 py-4 w-full">
      {/* Sekcja załączników */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <AttachmentsSection taskId={taskId} />
      </div>

      {/* Sekcja aktywności (Komentarze) */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm">
        <CommentsSection taskId={taskId} />
      </div>
    </div>
  );
}
