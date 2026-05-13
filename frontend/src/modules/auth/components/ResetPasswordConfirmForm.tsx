import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { confirmPasswordReset } from "../api";
import { resetPasswordConfirmSchema } from "../schemas";
import type { ResetPasswordConfirmInput } from "../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";
const hintClass = "mt-1 text-xs text-gray-500";

interface ResetPasswordConfirmFormProps {
  token: string;
}

export default function ResetPasswordConfirmForm({ token }: ResetPasswordConfirmFormProps) {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ResetPasswordConfirmInput>({
    resolver: zodResolver(resetPasswordConfirmSchema),
    defaultValues: { newPassword: "", confirmPassword: "" },
  });

  async function onSubmit(values: ResetPasswordConfirmInput) {
    setSubmitError(null);
    try {
      await confirmPasswordReset({ token, newPassword: values.newPassword });
      navigate("/login", { state: { passwordResetSuccess: true }, replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setSubmitError("Link do resetu hasła jest nieprawidłowy lub wygasł. Poproś o nowy link.");
        return;
      }
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
        return;
      }
      setSubmitError("Nie udało się połączyć z serwerem. Spróbuj ponownie.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div>
        <label htmlFor="reset-new-password" className={labelClass}>
          Nowe hasło
        </label>
        <input
          id="reset-new-password"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.newPassword !== undefined}
          aria-describedby={
            errors.newPassword ? "reset-new-password-error" : "reset-new-password-hint"
          }
          className={inputClass}
          {...register("newPassword")}
        />
        {errors.newPassword && (
          <p id="reset-new-password-error" className={errorClass}>
            {errors.newPassword.message}
          </p>
        )}
        <p id="reset-new-password-hint" className={hintClass}>
          Co najmniej 8 znaków.
        </p>
      </div>

      <div>
        <label htmlFor="reset-confirm-password" className={labelClass}>
          Powtórz nowe hasło
        </label>
        <input
          id="reset-confirm-password"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.confirmPassword !== undefined}
          aria-describedby={errors.confirmPassword ? "reset-confirm-password-error" : undefined}
          className={inputClass}
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && (
          <p id="reset-confirm-password-error" className={errorClass}>
            {errors.confirmPassword.message}
          </p>
        )}
      </div>

      {submitError !== null && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Resetowanie..." : "Ustaw nowe hasło"}
      </button>
    </form>
  );
}
