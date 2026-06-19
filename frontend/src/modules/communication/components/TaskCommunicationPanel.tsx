import WorklogsSection from "../../tasks/components/WorklogsSection";
import AttachmentsSection from "./AttachmentsSection";
import CommentsSection from "./CommentsSection";

interface TaskCommunicationPanelProps {
  taskId: number;
}

export default function TaskCommunicationPanel({ taskId }: TaskCommunicationPanelProps) {
  return (
    <div className="w-full py-4">
      <div className="grid gap-6">
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <WorklogsSection taskId={taskId} />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <AttachmentsSection taskId={taskId} />
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <CommentsSection taskId={taskId} />
        </div>
      </div>
    </div>
  );
}
