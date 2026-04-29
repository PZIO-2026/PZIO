import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { register as registerApi } from "../api";
import { registerSchema } from "../schemas";
import type { RegisterInput } from "../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

export default function RegisterForm() {
  const navigate = useNavigate();
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register: registerField,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterInput>({
    resolver: zodResolver(registerSchema),
    defaultValues: { email: "", password: "", firstName: "", lastName: "" },
  });

  async function onSubmit(values: RegisterInput) {
    setSubmitError(null);
    try {
      await registerApi(values);
      navigate("/login", { state: { registeredEmail: values.email }, replace: true });
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setSubmitError("Konto z tym adresem email już istnieje.");
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
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="register-first-name" className={labelClass}>
            Imię
          </label>
          <input
            id="register-first-name"
            type="text"
            autoComplete="given-name"
            className={inputClass}
            {...registerField("firstName")}
          />
          {errors.firstName && <p className={errorClass}>{errors.firstName.message}</p>}
        </div>

        <div>
          <label htmlFor="register-last-name" className={labelClass}>
            Nazwisko
          </label>
          <input
            id="register-last-name"
            type="text"
            autoComplete="family-name"
            className={inputClass}
            {...registerField("lastName")}
          />
          {errors.lastName && <p className={errorClass}>{errors.lastName.message}</p>}
        </div>
      </div>

      <div>
        <label htmlFor="register-email" className={labelClass}>
          Email
        </label>
        <input
          id="register-email"
          type="email"
          autoComplete="email"
          className={inputClass}
          {...registerField("email")}
        />
        {errors.email && <p className={errorClass}>{errors.email.message}</p>}
      </div>

      <div>
        <label htmlFor="register-password" className={labelClass}>
          Hasło
        </label>
        <input
          id="register-password"
          type="password"
          autoComplete="new-password"
          className={inputClass}
          {...registerField("password")}
        />
        {errors.password && <p className={errorClass}>{errors.password.message}</p>}
        <p className="mt-1 text-xs text-gray-500">Co najmniej 8 znaków.</p>
      </div>

      {submitError !== null && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
      )}

      <button
        type="submit"
        disabled={isSubmitting}
        className="w-full rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isSubmitting ? "Tworzenie konta..." : "Utwórz konto"}
      </button>
    </form>
  );
}
