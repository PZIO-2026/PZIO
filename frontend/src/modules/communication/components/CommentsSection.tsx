import { Loader2, MessageSquare } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { toast } from "react-hot-toast";

import { useConfirm } from "../../../components/ConfirmProvider";
import { useAuth } from "../../auth/hooks";
import { createComment, deleteComment, fetchComments, updateComment, fetchAttachments } from "../api";
import type { Comment, Attachment } from "../types";

import CommentItem from "./CommentItem";
import CommentForm from "./CommentForm";

export default function CommentsSection({ taskId }: { taskId: number }) {
  const { user } = useAuth();
  const confirmDialog = useConfirm();
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [attachments, setAttachments] = useState<Attachment[]>([]);

  const refreshAttachments = useCallback(async () => {
    try {
      const data = await fetchAttachments(taskId);
      setAttachments(data);
    } catch (err) {
      console.error(err);
    }
  }, [taskId]);

  const refreshComments = async () => {
    try {
      const data = await fetchComments(taskId);
      setComments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    refreshComments();
    refreshAttachments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const handleCreateComment = async (content: string) => {
    try {
      const newComment = await createComment(taskId, content);
      if (!newComment.user && user) {
        newComment.user = user;
      }
      setComments((prev) => [...prev, newComment]);
    } catch (err) {
      console.error(err);
      toast.error("Nie udało się dodać komentarza.");
      throw err;
    }
  };

  const handleDeleteComment = async (id: number) => {
    if (!(await confirmDialog("Czy na pewno chcesz usunąć ten komentarz?"))) return;
    try {
      await deleteComment(id);
      setComments((prev) => prev.filter((c) => c.commentId !== id));
      toast.success("Komentarz został usunięty.");
    } catch (err) {
      console.error(err);
      toast.error("Nie udało się usunąć komentarza.");
    }
  };

  const handleUpdateComment = async (id: number, content: string) => {
    try {
      const updated = await updateComment(id, content);
      setComments((prev) => prev.map((c) => (c.commentId === id ? { ...c, content: updated.content } : c)));
    } catch (err) {
      console.error(err);
      toast.error("Nie udało się zaktualizować komentarza.");
      throw err;
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
        <MessageSquare className="w-5 h-5 text-slate-500" />
        Komentarze i aktywność
      </h3>

      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="flex flex-col gap-5">
          {comments.length === 0 ? (
            <p className="text-sm text-slate-500 italic px-2">Brak komentarzy. Bądź pierwszą osobą, która podzieli się wiedzą!</p>
          ) : (
            comments.map((comment) => (
              <CommentItem
                key={comment.commentId}
                comment={comment}
                attachments={attachments}
                currentUser={user}
                onDelete={handleDeleteComment}
                onUpdate={handleUpdateComment}
              />
            ))
          )}
        </div>
      )}

      <CommentForm 
        user={user} 
        attachments={attachments} 
        onSubmitComment={handleCreateComment} 
        onRefreshAttachments={refreshAttachments}
      />
    </div>
  );
}
