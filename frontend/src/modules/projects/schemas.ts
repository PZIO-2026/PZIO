import { z } from "zod";

// ============================================================
// Projekty
// ============================================================

export const createProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Nazwa projektu jest wymagana")
    .max(200, "Nazwa projektu nie może przekraczać 200 znaków"),
  description: z
    .string()
    .max(2000, "Opis nie może przekraczać 2000 znaków")
    .default(""),
});

export type CreateProjectFormInput = z.infer<typeof createProjectSchema>;

export const updateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Nazwa projektu jest wymagana")
    .max(200, "Nazwa projektu nie może przekraczać 200 znaków")
    .optional(),
  description: z
    .string()
    .max(2000, "Opis nie może przekraczać 2000 znaków")
    .optional(),
  status: z
    .enum(["active", "archived"], {
      error: "Nieprawidłowy status projektu",
    })
    .optional(),
});

export type UpdateProjectFormInput = z.infer<typeof updateProjectSchema>;

// ============================================================
// Członkowie projektu
// ============================================================

export const addMemberSchema = z.object({
  email: z
    .email({
      error: "Podaj adres email użytkownika",
    })
    .max(255),

  roles: z
    .array(
      z.enum([
        "project_owner",
        "scrum_master",
        "developer",
        "qa",
      ]),
    )
    .min(1, "Wybierz przynajmniej jedną rolę"),
});

export type AddMemberFormInput = z.infer<typeof addMemberSchema>;

export const sprintFormSchema = z
  .object({
    name: z
      .string()
      .min(3, "Nazwa sprintu musi mieć minimum 3 znaki")
      .max(
        120,
        "Nazwa sprintu może mieć maksymalnie 120 znaków",
      ),

    startDate: z
      .string()
      .regex(
        /^\d{4}-\d{2}-\d{2}$/,
        "Nieprawidłowy format daty",
      )
      .min(1, "Data rozpoczęcia jest wymagana"),

    endDate: z
      .string()
      .regex(
        /^\d{4}-\d{2}-\d{2}$/,
        "Nieprawidłowy format daty",
      )
      .min(1, "Data zakończenia jest wymagana"),

    goal: z
      .string()
      .max(
        1500,
        "Cel sprintu może mieć maksymalnie 1500 znaków",
      ),

    status: z
      .enum([
        "planned",
        "active",
        "completed",
      ])
      .optional(),
  })
  .refine(
    (values) =>
      new Date(values.endDate).getTime() >=
      new Date(values.startDate).getTime(),
    {
      message:
        "Data zakończenia nie może być wcześniejsza niż rozpoczęcie",
      path: ["endDate"],
    },
  );

export type SprintFormInput = z.infer<
  typeof sprintFormSchema
>;

