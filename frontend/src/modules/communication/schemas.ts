import { z } from "zod";

export const createCommentSchema = z.object({
  content: z.string().min(1, "Komentarz nie może być pusty"),
});

export type CreateCommentFormInput = z.infer<typeof createCommentSchema>;
