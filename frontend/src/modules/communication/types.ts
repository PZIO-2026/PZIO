import type { User } from "../auth/types";

export interface Comment {
  commentId: number;
  taskId: number;
  authorId: number;
  content: string;
  createdAt: string;
  user?: User; // Opcjonalnie dołączone dane autora
}

export interface Attachment {
  attachmentId: number;
  taskId: number;
  uploaderId: number;
  filename: string;
  contentType: string;
  createdAt: string;
  user?: User; // Opcjonalnie dołączone dane autora
}
