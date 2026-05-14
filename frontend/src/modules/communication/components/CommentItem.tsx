import { Check, Edit2, Loader2, Trash2, X } from "lucide-react";
import { useState } from "react";
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

interface CommentItemProps {
  comment: Comment;
  attachments: Attachment[];
  currentUser: { userId: number } | null;
  onDelete: (id: number) => Promise<void>;
  onUpdate: (id: number, content: string) => Promise<void>;
}

export default function CommentItem({ comment, attachments, currentUser, onDelete, onUpdate }: CommentItemProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState("");
  const [isSubmittingEdit, setIsSubmittingEdit] = useState(false);

  const isOwner = currentUser && comment.authorId === currentUser.userId;

  const authorName = comment.user
    ? `${comment.user.firstName} ${comment.user.lastName}`
    : `Użytkownik #${comment.authorId}`;
  const hasAvatar = comment.user?.avatar !== null && comment.user?.avatar !== "";
  const avatarInitials = comment.user
    ? `${comment.user.firstName[0]}${comment.user.lastName[0]}`.toUpperCase()
    : "?";

  const startEditing = () => {
    setEditContent(comment.content);
    setIsEditing(true);
  };

  const cancelEditing = () => {
    setIsEditing(false);
    setEditContent("");
  };

  const saveEdit = async () => {
    if (!editContent.trim()) return;
    setIsSubmittingEdit(true);
    try {
      await onUpdate(comment.commentId, editContent);
      setIsEditing(false);
    } finally {
      setIsSubmittingEdit(false);
    }
  };

  return (
    <div className="flex gap-4 group">
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
                onClick={startEditing}
                className="p-1.5 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Edytuj"
              >
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              <button
                onClick={() => onDelete(comment.commentId)}
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
                onClick={saveEdit}
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
}
