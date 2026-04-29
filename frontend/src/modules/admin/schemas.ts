import { z } from "zod";

export const createTaskTypeSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Nazwa typu jest wymagana")
    .max(100, "Nazwa typu nie może przekraczać 100 znaków"),
});

export const taskHistorySchema = z.object({
  taskId: z
    .number({ error: "Podaj numer ID zadania" })
    .int("ID zadania musi być liczbą całkowitą")
    .positive("ID zadania musi być dodatnie"),
});

export type CreateTaskTypeFormInput = z.infer<typeof createTaskTypeSchema>;
export type TaskHistoryFormInput = z.infer<typeof taskHistorySchema>;
