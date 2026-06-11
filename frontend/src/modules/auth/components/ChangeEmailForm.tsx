import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { changeEmail } from "../api";
import { changeEmailSchema } from "../schemas";
import type { ChangeEmailInput } from "../schemas";
import type { User } from "../types";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";
const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

interface ChangeEmailFormProps {
  user: User;
  onSuccess: (updatedUser: User) => void;
}

export default function ChangeEmailForm({ user, onSuccess }: ChangeEmailFormProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ChangeEmailInput>({
    resolver: zodResolver(changeEmailSchema),
    defaultValues: { email: user.email },
  });

  async function onSubmit(values: ChangeEmailInput) {
    setSubmitError(null);
    setSuccessMsg(null);
    if (values.email === user.email) return;

    try {
      const updated = await changeEmail({ email: values.email });
      onSuccess(updated);
      setSuccessMsg("Adres email został pomyślnie zmieniony.");
    } catch (err) {
      if (err instanceof ApiError) {
        if (err.detail === "Email already in use.") {
          setSubmitError("Konto z tym adresem email już istnieje.");
        } else {
          setSubmitError("Wystąpił błąd podczas zmiany adresu email.");
        }
      } else {
        setSubmitError("Wystąpił błąd sieci lub serwera.");
      }
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div>
        <label htmlFor="change-email" className={labelClass}>
          Nowy adres email
        </label>
        <input
          id="change-email"
          type="email"
          autoComplete="email"
          aria-invalid={errors.email !== undefined}
          className={inputClass}
          {...register("email")}
        />
        {errors.email && <p className={errorClass}>{errors.email.message}</p>}
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
        Zapisz email
      </button>
    </form>
  );
}