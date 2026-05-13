import { ApiError, apiFetch } from "../../api/client";
import { getStoredToken } from "../auth/storage";
import type { Attachment, Comment } from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

// --- Comments ---

export function fetchComments(taskId: number): Promise<Comment[]> {
  return apiFetch<Comment[]>(`/api/tasks/${taskId}/comments`);
}

export function createComment(taskId: number, content: string): Promise<Comment> {
  return apiFetch<Comment>(`/api/tasks/${taskId}/comments`, {
    method: "POST",
    body: { content },
  });
}

export function updateComment(commentId: number, content: string): Promise<Comment> {
  return apiFetch<Comment>(`/api/comments/${commentId}`, {
    method: "PATCH",
    body: { content },
  });
}

export function deleteComment(commentId: number): Promise<void> {
  return apiFetch<void>(`/api/comments/${commentId}`, {
    method: "DELETE",
  });
}

// --- Attachments ---

export function fetchAttachments(taskId: number): Promise<Attachment[]> {
  return apiFetch<Attachment[]>(`/api/tasks/${taskId}/attachments`);
}

export async function uploadAttachment(taskId: number, file: File): Promise<Attachment> {
  const token = getStoredToken();
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}/attachments`, {
    method: "POST",
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: formData,
  });

  if (!response.ok) {
    let detail = response.statusText;
    try {
      const errorBody = await response.json();
      if (typeof errorBody?.detail === "string") {
        detail = errorBody.detail;
      }
    } catch {
      // Ignore
    }
    throw new ApiError(response.status, detail);
  }

  return response.json();
}

export function deleteAttachment(attachmentId: number): Promise<void> {
  return apiFetch<void>(`/api/attachments/${attachmentId}`, {
    method: "DELETE",
  });
}

export async function downloadAttachment(attachmentId: number, fileName: string): Promise<void> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}/api/attachments/${attachmentId}/download`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Nie udało się pobrać pliku");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fileName;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

export async function getAttachmentObjectUrl(attachmentId: number): Promise<string> {
  const token = getStoredToken();
  const response = await fetch(`${API_BASE_URL}/api/attachments/${attachmentId}/download`, {
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error("Nie udało się pobrać pliku");
  }

  const blob = await response.blob();
  return window.URL.createObjectURL(blob);
}
