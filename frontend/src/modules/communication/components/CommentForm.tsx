import { zodResolver } from "@hookform/resolvers/zod";
import { Loader2, X, Paperclip } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import type { Attachment } from "../types";
import { type CreateCommentFormInput, createCommentSchema } from "../schemas";
import AttachmentPreview from "./AttachmentPreview";

interface CommentFormProps {
  user: { firstName: string; lastName: string } | null;
  attachments: Attachment[];
  onSubmitComment: (content: string) => Promise<void>;
  onRefreshAttachments: () => void;
}

export default function CommentForm({ user, attachments, onSubmitComment, onRefreshAttachments }: CommentFormProps) {
  const [showPicker, setShowPicker] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    if (showPicker) {
      onRefreshAttachments();
    }
  }, [showPicker, onRefreshAttachments]);

  const {
    register,
    handleSubmit,
    reset,
    setValue,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<CreateCommentFormInput>({
    resolver: zodResolver(createCommentSchema),
    defaultValues: { content: "" },
  });

  const contentValue = watch("content");

  // Merge register ref with our local ref so we can read cursor position
  const { ref: registerRef, ...registerRest } = register("content");

  const handleInsertAttachment = (attachment: Attachment) => {
    const tag = `[attachment:${attachment.attachmentId}]`;
    const current = contentValue || "";

    // Insert at cursor position if textarea is available, otherwise append
    const cursorPos = textareaRef.current?.selectionStart ?? current.length;
    const before = current.slice(0, cursorPos);
    const after = current.slice(cursorPos);

    // Add spacing around the tag
    const spaceBefore = before.length > 0 && !before.endsWith(" ") && !before.endsWith("\n") ? " " : "";
    const spaceAfter = after.length > 0 && !after.startsWith(" ") && !after.startsWith("\n") ? " " : " ";

    const newContent = before + spaceBefore + tag + spaceAfter + after;
    setValue("content", newContent, { shouldValidate: true, shouldDirty: true });
    setShowPicker(false);
  };

  const onSubmit = async (data: CreateCommentFormInput) => {
    try {
      await onSubmitComment(data.content);
      reset({ content: "" });
    } catch {
      // errors are handled in the parent
    }
  };

  return (
    <div className="mt-2 flex gap-4 pt-4 border-t border-slate-100">
      <div className="flex-shrink-0 w-10 h-10 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 font-bold text-sm shadow-sm">
        {user ? `${user.firstName[0]}${user.lastName[0]}`.toUpperCase() : "ME"}
      </div>
      <div className="flex-1">
        <form onSubmit={handleSubmit(onSubmit)} className="relative bg-white rounded-xl shadow-sm border border-slate-200 focus-within:ring-2 focus-within:ring-blue-500/20 focus-within:border-blue-500 transition-all overflow-visible">
          <textarea
            {...registerRest}
            ref={(el) => {
              registerRef(el);
              textareaRef.current = el;
            }}
            value={contentValue}
            placeholder="Dodaj komentarz do zadania..."
            className="w-full px-4 py-3 bg-transparent focus:outline-none text-base resize-y min-h-[100px]"
          />

          <div className="flex justify-between items-center px-3 py-2 bg-slate-50 border-t border-slate-100 relative">
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setShowPicker(!showPicker)}
                className="p-1.5 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-md transition-colors"
                title="Wstaw załącznik"
              >
                <Paperclip className="w-5 h-5" />
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
                      <p className="text-sm text-slate-400">Brak załączników.</p>
                    ) : (
                      [...attachments].sort((a, b) => {
                        const aImg = a.contentType?.startsWith("image/") ? 0 : 1;
                        const bImg = b.contentType?.startsWith("image/") ? 0 : 1;
                        return aImg - bImg;
                      }).map(att => {
                        const isImage = att.contentType?.startsWith("image/");
                        return isImage ? (
                          <button
                            key={att.attachmentId}
                            type="button"
                            onClick={() => handleInsertAttachment(att)}
                            className="w-16 h-16 rounded-md border border-slate-200 overflow-hidden hover:border-blue-500 hover:ring-2 hover:ring-blue-200 transition-all flex-shrink-0"
                            title={att.filename}
                          >
                            <AttachmentPreview attachment={att} />
                          </button>
                        ) : (
                          <button
                            key={att.attachmentId}
                            type="button"
                            onClick={() => handleInsertAttachment(att)}
                            className="w-full flex items-center gap-2.5 px-2.5 py-2 rounded-md border border-slate-200 hover:border-blue-500 hover:bg-blue-50/50 transition-all text-left"
                            title={att.filename}
                          >
                            <div className="flex-shrink-0 w-8 h-8 rounded bg-slate-100 border border-slate-200 flex items-center justify-center">
                              <AttachmentPreview attachment={att} iconClassName="w-4 h-4 text-slate-400" />
                            </div>
                            <span className="text-sm text-slate-700 truncate">{att.filename}</span>
                          </button>
                        );
                      })
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
  );
}
