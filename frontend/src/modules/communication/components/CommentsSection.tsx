import { zodResolver } from "@hookform/resolvers/zod";
import { Check, Edit2, Loader2, MessageSquare, Trash2, X, Image as ImageIcon } from "lucide-react";
import { useEffect, useState } from "react";
import { useForm } from "react-hook-form";

import { useAuth } from "../../auth/hooks";
import { createComment, deleteComment, fetchComments, updateComment, fetchAttachments } from "../api";
import { type CreateCommentFormInput, createCommentSchema } from "../schemas";
import type { Comment, Attachment } from "../types";
import AttachmentPreview from "./AttachmentPreview";

function renderCommentContent(content: string, attachments: Attachment[]) {
  const regex = /\[attachment:(\d+)\]/g;
  const parts = [];
  let lastIndex = 0;
  let match;

  while ((match = regex.exec(content)) !== null) {
    if (match.index > lastIndex) {
      parts.push(content.substring(lastIndex, match.index));
    }
    const id = parseInt(match[1], 10);
    const attachment = attachments.find((a) => a.attachmentId === id);
    if (attachment) {
      parts.push(
        <span key={`att-${id}-${match.index}`} className="block my-2">
          <AttachmentPreview attachment={attachment} className="max-w-sm max-h-64 object-contain rounded-lg border border-slate-200 shadow-sm" />
        </span>
      );
    } else {
      parts.push(`[attachment:${id}]`);
    }
    lastIndex = regex.lastIndex;
  }
  if (lastIndex < content.length) {
    parts.push(content.substring(lastIndex));
  }

  return parts;
}

export default function CommentsSection({ taskId }: { taskId: number }) {
  const { user } = useAuth();
  const [comments, setComments] = useState<Comment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editContent, setEditContent] = useState("");
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showPicker, setShowPicker] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    getValues,
    formState: { errors, isSubmitting },
  } = useForm<CreateCommentFormInput>({
    resolver: zodResolver(createCommentSchema),
  });

  const refreshAttachments = async () => {
    try {
      const data = await fetchAttachments(taskId);
      setAttachments(data.filter((a) => a.contentType?.startsWith("image/")));
    } catch (err) {
      console.error(err);
    }
  };

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
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshComments();
    refreshAttachments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  useEffect(() => {
    if (!showPicker) return;

    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshAttachments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showPicker]);

  const handleInsertAttachment = (attachment: Attachment) => {
    const current = getValues("content") || "";
    const newContent = current + (current.endsWith(" ") || current === "" ? "" : " ") + `[attachment:${attachment.attachmentId}] `;
    setValue("content", newContent, { shouldValidate: true });
    setShowPicker(false);
  };

  const onSubmit = async (data: CreateCommentFormInput) => {
    try {
      const newComment = await createComment(taskId, data.content);
      // Przypisujemy uzytkownika do zwrotki jezeli API tego nie robi od razu
      if (!newComment.user && user) {
        newComment.user = user;
      }
      setComments((prev) => [...prev, newComment]);
      reset();
    } catch (err) {
      console.error(err);
      alert("Nie udało się dodać komentarza.");
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Czy na pewno chcesz usunąć ten komentarz?")) return;
    try {
      await deleteComment(id);
      setComments((prev) => prev.filter((c) => c.commentId !== id));
    } catch (err) {
      console.error(err);
      alert("Nie udało się usunąć komentarza.");
    }
  };

  const startEditing = (comment: Comment) => {
    setEditingId(comment.commentId);
    setEditContent(comment.content);
  };

  const cancelEditing = () => {
    setEditingId(null);
    setEditContent("");
  };

  const saveEdit = async (id: number) => {
    if (!editContent.trim()) return;
    setIsSubmittingEdit(true);
    try {
      const updated = await updateComment(id, editContent);
      setComments((prev) => prev.map((c) => (c.commentId === id ? { ...c, content: updated.content } : c)));
      setEditingId(null);
    } catch (err) {
      console.error(err);
      alert("Nie udało się zaktualizować komentarza.");
    } finally {
      setIsSubmittingEdit(false);
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
            comments.map((comment) => {
              const isOwner = user && comment.authorId === user.userId;
              const isEditing = editingId === comment.commentId;

              const authorName = comment.user
                ? `${comment.user.firstName} ${comment.user.lastName}`
                : `Użytkownik #${comment.authorId}`;
              const hasAvatar = comment.user?.avatar !== null && comment.user?.avatar !== "";
              const avatarInitials = comment.user
                ? `${comment.user.firstName[0]}${comment.user.lastName[0]}`.toUpperCase()
                : "?";

              return (
                <div key={comment.commentId} className="flex gap-4 group">
                  {hasAvatar ? (
                    <img
                      src={comment.user?.avatar ?? ""}
                      alt="Awatar autora komentarza"
                      className="flex-shrink-0 w-10 h-10 rounded-full object-cover border border-indigo-100 shadow-sm"
                    />
                  ) : (
                    <div className="flex-shrink-0 w-10 h-10 rounded-full bg-gradient-to-br from-indigo-100 to-indigo-50 border border-indigo-100 flex items-center justify-center text-indigo-700 font-bold text-sm shadow-sm">
                      {avatarInitials}
                    </div>
                  )}
                  <div className="flex-1 min-w-0 bg-slate-50 p-4 rounded-2xl rounded-tl-sm border border-slate-100">
                    <div className="flex items-baseline justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-slate-800 text-base">{authorName}</span>
                        <span className="text-sm font-medium text-slate-400">
                          {new Date(comment.createdAt).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' })}
                        </span>
                      </div>
                      
                      {!isEditing && isOwner && (
                        <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={() => startEditing(comment)}
                            className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                            title="Edytuj"
                          >
                            <Edit2 className="w-3.5 h-3.5" />
                          </button>
                          <button
                            onClick={() => handleDelete(comment.commentId)}
                            className="p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-md transition-colors"
                            title="Usuń"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      )}
                    </div>

                    {isEditing ? (
                      <div className="mt-2">
                        <textarea
                          value={editContent}
                          onChange={(e) => setEditContent(e.target.value)}
                          className="w-full px-3 py-2 border border-blue-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-base resize-y shadow-sm bg-white"
                          rows={3}
                          autoFocus
                        />
                        <div className="flex items-center gap-2 mt-3">
                          <button
                            onClick={() => saveEdit(comment.commentId)}
                            disabled={isSubmittingEdit || !editContent.trim()}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 transition-colors shadow-sm disabled:opacity-50"
                          >
                            {isSubmittingEdit ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Check className="w-3.5 h-3.5" />}
                            Zapisz
                          </button>
                          <button
                            onClick={cancelEditing}
                            disabled={isSubmittingEdit}
                            className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors shadow-sm"
                          >
                            <X className="w-3.5 h-3.5" />
                            Anuluj
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="text-base text-slate-700 whitespace-pre-wrap break-words leading-relaxed">
                        {renderCommentContent(comment.content, attachments)}
                      </div>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>
      )}

      {/* Komponent formularza nowego komentarza */}
      <div className="mt-2 flex gap-4 pt-4 border-t border-slate-100">
        <div className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 font-bold text-sm shadow-sm">
          {user ? `${user.firstName[0]}${user.lastName[0]}`.toUpperCase() : "ME"}
        </div>
        <div className="flex-1">
          <form onSubmit={handleSubmit(onSubmit)} className="relative bg-white rounded-xl shadow-sm border border-slate-200 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all overflow-visible">
            <textarea
              {...register("content")}
              placeholder="Dodaj komentarz do zadania..."
              className="w-full px-4 py-3 bg-transparent focus:outline-none text-base resize-y min-h-[100px]"
            />
            
            <div className="flex justify-between items-center px-3 py-2 bg-slate-50 border-t border-slate-100 relative">
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowPicker(!showPicker)}
                  className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                  title="Wstaw obrazek z załączników"
                >
                  <ImageIcon className="w-5 h-5" />
                </button>
                
                {showPicker && (
                  <div className="absolute bottom-full left-0 mb-3 w-[26rem] bg-white border border-slate-200 rounded-xl shadow-2xl p-4 z-50">
                    <div className="flex justify-between items-center mb-3">
                      <p className="text-sm font-semibold text-slate-500 px-1">Wybierz załącznik</p>
                      <button type="button" onClick={() => setShowPicker(false)} className="text-slate-400 hover:text-slate-600">
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                    <div className="flex flex-wrap gap-3 max-h-56 overflow-y-auto p-1">
                      {attachments.length === 0 ? (
                        <p className="text-sm text-slate-400">Brak obrazków w załącznikach.</p>
                      ) : (
                        attachments.map(att => (
                          <button
                            key={att.attachmentId}
                            type="button"
                            onClick={() => handleInsertAttachment(att)}
                            className="w-16 h-16 rounded-md border border-slate-200 overflow-hidden hover:border-blue-500 hover:ring-2 hover:ring-blue-200 transition-all flex-shrink-0"
                            title={att.filename}
                          >
                            <AttachmentPreview attachment={att} />
                          </button>
                        ))
                      )}
                    </div>
                  </div>
                )}
                
                <div className="text-xs text-red-500 font-medium px-1">
                  {errors.content?.message}
                </div>
              </div>
              <button
                type="submit"
                disabled={isSubmitting}
                className="inline-flex items-center justify-center px-4 py-1.5 text-sm font-semibold text-white bg-blue-600 rounded-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 transition-all shadow-sm"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Wysyłanie
                  </>
                ) : (
                  "Skomentuj"
                )}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
