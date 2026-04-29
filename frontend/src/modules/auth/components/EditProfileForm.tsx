import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { ApiError } from "../../../api/client";
import { updateMe } from "../api";
import { editProfileSchema } from "../schemas";
import type { EditProfileInput } from "../schemas";
import type { User } from "../types";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const labelClass = "block text-sm font-medium text-gray-700";
const errorClass = "mt-1 text-sm text-red-600";

interface EditProfileFormProps {
  user: User;
  onSuccess: (updatedUser: User) => void;
  onCancel: () => void;
}

export default function EditProfileForm({ user, onSuccess, onCancel }: EditProfileFormProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<EditProfileInput>({
    resolver: zodResolver(editProfileSchema),
    defaultValues: {
      firstName: user.firstName,
      lastName: user.lastName,
      avatar: user.avatar ?? "",
    },
  });

  async function onSubmit(values: EditProfileInput) {
    setSubmitError(null);
    try {
      const trimmedAvatar = values.avatar.trim();
      const updated = await updateMe({
        firstName: values.firstName,
        lastName: values.lastName,
        avatar: trimmedAvatar === "" ? null : trimmedAvatar,
      });
      onSuccess(updated);
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
        return;
      }
      setSubmitError("Nie udało się zapisać zmian. Spróbuj ponownie.");
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="profile-first-name" className={labelClass}>
            Imię
          </label>
          <input
            id="profile-first-name"
            type="text"
            autoComplete="given-name"
            aria-invalid={errors.firstName !== undefined}
            aria-describedby={errors.firstName ? "profile-first-name-error" : undefined}
            className={inputClass}
            {...register("firstName")}
          />
          {errors.firstName && (
            <p id="profile-first-name-error" className={errorClass}>
              {errors.firstName.message}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="profile-last-name" className={labelClass}>
            Nazwisko
          </label>
          <input
            id="profile-last-name"
            type="text"
            autoComplete="family-name"
            aria-invalid={errors.lastName !== undefined}
            aria-describedby={errors.lastName ? "profile-last-name-error" : undefined}
            className={inputClass}
            {...register("lastName")}
          />
          {errors.lastName && (
            <p id="profile-last-name-error" className={errorClass}>
              {errors.lastName.message}
            </p>
          )}
        </div>
      </div>

      <div>
        <label htmlFor="profile-avatar" className={labelClass}>
          Awatar (URL)
        </label>
        <input
          id="profile-avatar"
          type="url"
          autoComplete="off"
          aria-invalid={errors.avatar !== undefined}
          aria-describedby={errors.avatar ? "profile-avatar-error" : "profile-avatar-hint"}
          className={inputClass}
          {...register("avatar")}
        />
        {errors.avatar && (
          <p id="profile-avatar-error" className={errorClass}>
            {errors.avatar.message}
          </p>
        )}
        <p id="profile-avatar-hint" className="mt-1 text-xs text-gray-500">
          Pozostaw puste, aby usunąć awatar.
        </p>
      </div>

      {submitError !== null && (
        <p className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{submitError}</p>
      )}

      <div className="flex justify-end gap-2">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-md border border-gray-300 px-4 py-2 font-medium text-gray-700 hover:bg-gray-50"
        >
          Anuluj
        </button>
        <button
          type="submit"
          disabled={isSubmitting}
          className="rounded-md bg-blue-600 px-4 py-2 font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? "Zapisywanie..." : "Zapisz zmiany"}
        </button>
      </div>
    </form>
  );
}
