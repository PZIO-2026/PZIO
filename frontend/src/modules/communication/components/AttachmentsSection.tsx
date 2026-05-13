import { Download, File as FileIcon, Loader2, Paperclip, Plus, Trash2, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { deleteAttachment, downloadAttachment, fetchAttachments, uploadAttachment } from "../api";
import type { Attachment } from "../types";
import AttachmentPreview from "./AttachmentPreview";
export default function AttachmentsSection({ taskId }: { taskId: number }) {
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refreshAttachments = async () => {
    try {
      const data = await fetchAttachments(taskId);
      setAttachments(data);
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    refreshAttachments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [taskId]);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsUploading(true);
    try {
      await uploadAttachment(taskId, file);
      await refreshAttachments();
    } catch (err) {
      console.error(err);
      alert("Nie udało się wgrać pliku.");
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Czy na pewno chcesz usunąć ten załącznik?")) return;
    try {
      await deleteAttachment(id);
      setAttachments((prev) => prev.filter((a) => a.attachmentId !== id));
    } catch (err) {
      console.error(err);
      alert("Nie udało się usunąć załącznika.");
    }
  };

  const handleDownload = async (id: number, filename: string) => {
    try {
      await downloadAttachment(id, filename);
    } catch (err) {
      console.error(err);
      alert("Błąd podczas pobierania pliku.");
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
          <Paperclip className="w-5 h-5 text-slate-500" />
          Załączniki
        </h3>
        {/* Hidden file input */}
        <input type="file" className="hidden" ref={fileInputRef} onChange={handleFileChange} />
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center py-6">
          <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
        </div>
      ) : (
        <div className="flex flex-wrap gap-4 mt-2">
          {attachments.map((attachment) => (
            <div
              key={attachment.attachmentId}
              className="relative flex flex-col items-center w-60 group"
            >
              <div className="relative w-60 h-60 bg-slate-50 rounded-lg overflow-hidden border border-slate-200 flex items-center justify-center shadow-sm">
                <AttachmentPreview attachment={attachment} />

                {/* Hover overlay actions */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                  <button
                    onClick={() => handleDownload(attachment.attachmentId, attachment.filename)}
                    className="p-2 text-white hover:bg-white/20 rounded-full transition-colors"
                    title="Pobierz"
                  >
                    <Download className="w-6 h-6" />
                  </button>
                </div>

                {/* Delete button (X in top right) */}
                <button
                  onClick={() => handleDelete(attachment.attachmentId)}
                  className="absolute top-1 right-1 p-1 bg-slate-900/50 text-white rounded-full opacity-0 group-hover:opacity-100 hover:bg-red-600 transition-all"
                  title="Usuń"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              </div>

              <div className="w-full mt-2 text-center px-1">
                <p className="text-sm font-medium text-slate-700 truncate" title={attachment.filename}>
                  {attachment.filename}
                </p>
              </div>
            </div>
          ))}

          {/* Jira style upload placeholder */}
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex flex-col items-center justify-center w-60 h-60 border-2 border-dashed border-slate-300 rounded-lg bg-slate-50 hover:bg-slate-100 hover:border-slate-400 transition-colors disabled:opacity-50 shadow-sm"
          >
            {isUploading ? (
              <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
            ) : (
              <>
                <Plus className="w-10 h-10 text-slate-400 mb-3" />
                <span className="text-sm text-center px-4 text-slate-500 leading-tight">
                  Przeciągnij pliki lub kliknij aby wgrać
                </span>
              </>
            )}
          </button>
        </div>
      )}
    </div>
  );
}
