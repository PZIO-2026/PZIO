import { z } from "zod";

// ============================================================
// Projekty
// ============================================================

export const createProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Nazwa projektu jest wymagana")
    .max(255, "Nazwa projektu nie może przekraczać 255 znaków"),
  description: z
    .string()
    .max(5000, "Opis nie może przekraczać 5000 znaków")
    .default(""),
});

export type CreateProjectFormInput = z.input<typeof createProjectSchema>;

export const updateProjectSchema = z.object({
  name: z
    .string()
    .min(1, "Nazwa projektu jest wymagana")
    .max(255, "Nazwa projektu nie może przekraczać 255 znaków")
    .optional(),
  description: z
    .string()
    .max(5000, "Opis nie może przekraczać 5000 znaków")
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
        "maintainer",
      ]),
    )
    .min(1, "Wybierz przynajmniej jedną rolę"),
});

export type AddMemberFormInput = z.infer<typeof addMemberSchema>;

export const projectMemberUpdateSchema = z.object({
  roles: z.array(
    z.enum(["developer", "qa", "scrum_master", "project_owner", "maintainer"]),
  ).min(1, "Wybierz przynajmniej jedną rolę"),
});

export type ProjectMemberUpdateFormValues = z.infer<typeof projectMemberUpdateSchema>;

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
      new Date(values.endDate).getTime() > new Date(values.startDate).getTime(),
    {
      message: "Data zakończenia musi być późniejsza niż data rozpoczęcia",
      path: ["endDate"],
    }
  );

export type SprintFormInput = z.infer<
  typeof sprintFormSchema
>;

// ============================================================
// Zadania (Work Items)
// ============================================================

export const taskFormSchema = z.object({
  title: z.string().min(1, "Tytuł jest wymagany").max(500, "Tytuł może mieć maksymalnie 500 znaków"),
  description: z.string().max(5000, "Opis może mieć maksymalnie 5000 znaków").optional(),
  type: z.string().min(1, "Typ jest wymagany"),
  priority: z.enum(["Low", "Medium", "High"], { error: "Wybierz priorytet" }),
  storyPoints: z.coerce.number().int().nonnegative().optional(),
  parentId: z.number().nullable().optional(),
  sprintId: z.number().nullable().optional(),
});

export type TaskFormInput = z.infer<typeof taskFormSchema>;
// Returns today's local date as an ISO-style yyyy-mm-dd string. Local time is
// used on purpose so the comparison matches what the user sees in the native
// date picker (which is also local).
export function todayLocalISO(): string {
  const now = new Date();
  const yyyy = now.getFullYear();
  const mm = String(now.getMonth() + 1).padStart(2, "0");
  const dd = String(now.getDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

// Used when creating a new sprint. Editing an existing sprint stays on the
// looser `sprintFormSchema`, since an already-started sprint legitimately has
// a startDate in the past and we don't want to block edits of its name/goal.
export const createSprintFormSchema = sprintFormSchema.refine(
  (values) => values.startDate >= todayLocalISO(),
  {
    message: "Sprint nie może rozpocząć się w przeszłości",
    path: ["startDate"],
  },
);

