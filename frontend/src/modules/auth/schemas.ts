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

export const forgotPasswordSchema = z.object({
  email: z.email("Nieprawidłowy format adresu email"),
});

export const resetPasswordConfirmSchema = z
  .object({
    newPassword: z
      .string()
      .min(8, "Hasło musi mieć co najmniej 8 znaków")
      .max(128, "Hasło nie może przekraczać 128 znaków"),
    confirmPassword: z.string().min(1, "Powtórz nowe hasło"),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Hasła nie są zgodne",
    path: ["confirmPassword"],
  });

export const changeEmailSchema = z.object({
  email: z.email("Nieprawidłowy format adresu email"),
});

export const changePasswordSchema = z
  .object({
    oldPassword: z.string().min(1, "Aktualne hasło jest wymagane"),
    newPassword: z
      .string()
      .min(8, "Hasło musi mieć co najmniej 8 znaków")
      .max(128, "Hasło nie może przekraczać 128 znaków"),
    confirmPassword: z.string().min(1, "Powtórz nowe hasło"),
  })
  .refine((data) => data.newPassword === data.confirmPassword, {
    message: "Hasła nie są zgodne",
    path: ["confirmPassword"],
  });

export type LoginInput = z.infer<typeof loginSchema>;
export type RegisterInput = z.infer<typeof registerSchema>;
export type EditProfileInput = z.infer<typeof editProfileSchema>;
export type ForgotPasswordInput = z.infer<typeof forgotPasswordSchema>;
export type ResetPasswordConfirmInput = z.infer<typeof resetPasswordConfirmSchema>;
export type ChangeEmailInput = z.infer<typeof changeEmailSchema>;
export type ChangePasswordInput = z.infer<typeof changePasswordSchema>;
