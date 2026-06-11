import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { changePassword } from "../api";
import { changePasswordSchema } from "../schemas";
import type { ChangePasswordInput } from "../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";
const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

export default function ChangePasswordForm() {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ChangePasswordInput>({
    resolver: zodResolver(changePasswordSchema),
  });

  async function onSubmit(values: ChangePasswordInput) {
    setSubmitError(null);
    setSuccessMsg(null);

    try {
      await changePassword({ oldPassword: values.oldPassword, newPassword: values.newPassword });
      setSuccessMsg("Hasło zostało pomyślnie zmienione.");
      reset();
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.detail === "Incorrect current password.") {
          setSubmitError("Podano nieprawidłowe aktualne hasło.");
        } else {
          setSubmitError("Wystąpił błąd podczas zmiany hasła.");
        }
      } else {
        setSubmitError("Wystąpił błąd sieci lub serwera.");
      }
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div>
        <label htmlFor="old-password" className={labelClass}>
          Aktualne hasło
        </label>
        <input
          id="old-password"
          type="password"
          autoComplete="current-password"
          aria-invalid={errors.oldPassword !== undefined}
          className={inputClass}
          {...register("oldPassword")}
        />
        {errors.oldPassword && <p className={errorClass}>{errors.oldPassword.message}</p>}
      </div>

      <div>
        <label htmlFor="new-password" className={labelClass}>
          Nowe hasło
        </label>
        <input
          id="new-password"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.newPassword !== undefined}
          className={inputClass}
          {...register("newPassword")}
        />
        {errors.newPassword && <p className={errorClass}>{errors.newPassword.message}</p>}
      </div>

      <div>
        <label htmlFor="confirm-password" className={labelClass}>
          Powtórz nowe hasło
        </label>
        <input
          id="confirm-password"
          type="password"
          autoComplete="new-password"
          aria-invalid={errors.confirmPassword !== undefined}
          className={inputClass}
          {...register("confirmPassword")}
        />
        {errors.confirmPassword && <p className={errorClass}>{errors.confirmPassword.message}</p>}
      </div>

      {submitError !== null && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
      )}
      {successMsg !== null && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">{successMsg}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gray-800 disabled:opacity-60"
      >
        Zmień hasło
      </button>
    </form>
  );
}