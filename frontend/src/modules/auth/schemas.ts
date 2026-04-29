import { z } from "zod";

export const loginSchema = z.object({
  email: z.email("Nieprawidłowy format adresu email"),
  password: z.string().min(1, "Hasło jest wymagane"),
});

export const registerSchema = z.object({
  email: z.email("Nieprawidłowy format adresu email"),
  password: z
    .string()
    .min(8, "Hasło musi mieć co najmniej 8 znaków")
    .max(128, "Hasło nie może przekraczać 128 znaków"),
  firstName: z.string().min(1, "Imię jest wymagane").max(100, "Imię jest za długie"),
  lastName: z.string().min(1, "Nazwisko jest wymagane").max(100, "Nazwisko jest za długie"),
});

export const editProfileSchema = z.object({
  firstName: z.string().min(1, "Imię jest wymagane").max(100, "Imię jest za długie"),
  lastName: z.string().min(1, "Nazwisko jest wymagane").max(100, "Nazwisko jest za długie"),
  avatar: z.string().max(255, "URL awatara jest za długi"),
});

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type EditProfileInput = z.infer<typeof editProfileSchema>;
