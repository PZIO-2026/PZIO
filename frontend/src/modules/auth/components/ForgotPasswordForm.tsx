import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { requestPasswordReset } from "../api";
import { forgotPasswordSchema } from "../schemas";
import type { ForgotPasswordInput } from "../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

export default function ForgotPasswordForm() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitted, setSubmitted] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordInput>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: "" },
  });

  async function onSubmit(values: ForgotPasswordInput) {
    setSubmitError(null);
    try {
      await requestPasswordReset(values.email);
      setSubmitted(true);
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
        return;
      }
      setSubmitError("Nie udało się połączyć z serwerem. Spróbuj ponownie.");
    }
  }

  if (submitted) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="rounded-md bg-green-50 px-3 py-3 text-sm text-green-700"
      >
        Jeśli konto z tym adresem email istnieje, wysłaliśmy na nie link do resetu hasła.
        Sprawdź swoją skrzynkę odbiorczą.
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div>
        <label htmlFor="forgot-email" className={labelClass}>
          Email
        </label>
        <input
          id="forgot-email"
          type="email"
          autoComplete="email"
          aria-invalid={errors.email !== undefined}
          aria-describedby={errors.email ? "forgot-email-error" : undefined}
          className={inputClass}
          {...register("email")}
        />
        {errors.email && (
          <p id="forgot-email-error" className={errorClass}>
            {errors.email.message}
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
        {isSubmitting ? "Wysyłanie..." : "Wyślij link do resetu"}
      </button>
    </form>
  );
}
