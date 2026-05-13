import { useForm } from "react-hook-form";
// import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";
import { addProjectMember } from "../../api";

import { useState } from "react";

import type {
  ProjectMember,
  ProjectRole,
} from "../../types";

import { addMemberSchema, type AddMemberFormInput  } from "../../schemas";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const errorClass = "mt-1 text-sm text-red-600";

const roleLabels: Record<ProjectRole, string> = {
  project_owner: "Project Owner",
  scrum_master: "Scrum Master",
  developer: "Developer",
  qa: "QA Engineer",
  maintainer: "Maintainer",
};

interface Props {
  isOpen: boolean;
  onClose: () => void;
  projectId: number;

  onMemberAdded: (member: ProjectMember) => void;
}

export default function AddProjectMemberModal({
  isOpen,
  onClose,
  projectId,
  onMemberAdded,
}: Props) {
  const [submitError, setSubmitError] = useState<string | null>(
    null,
  );

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<AddMemberFormInput>({
    resolver: zodResolver(addMemberSchema),
    defaultValues: {
      email: "",
      roles: ["developer"],
    },
  });

  async function onSubmit(values: AddMemberFormInput) {
    setSubmitError(null);

    try {
      const created = await addProjectMember(
        projectId,
        values,
      );

      onMemberAdded(created);

      reset();

      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
        return;
      }

      setSubmitError(
        "Nie udało się dodać użytkownika do projektu.",
      );
    }
  }

  return (
    <Modal
      title="Dodaj użytkownika"
      isOpen={isOpen}
      onClose={onClose}
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-5"
      >
        <div>
          <label className="block text-sm font-medium text-gray-700">
            E-mail użytkownika
          </label>

          <input
            type="email"
            className={inputClass}
            {...register("email")}
          />

          {errors.email && (
            <p className={errorClass}>
              {errors.email.message}
            </p>
          )}
        </div>

        <div>
          <p className="mb-2 text-sm font-medium text-gray-700">
            Role użytkownika
          </p>

          <div className="flex flex-wrap gap-3">
            {(
              [
                "project_owner",
                "scrum_master",
                "developer",
                "qa",
              ] as const
            ).map((roleValue) => (
              <label
                key={roleValue}
                className="flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm"
              >
                <input
                  type="checkbox"
                  value={roleValue}
                  {...register("roles")}
                />

                <span>{roleLabels[roleValue]}</span>
              </label>
            ))}
          </div>

          {errors.roles && (
            <p className={errorClass}>
              {errors.roles.message}
            </p>
          )}
        </div>

        {submitError && (
          <div className="rounded-md bg-red-50 px-4 py-3 text-sm text-red-700">
            {submitError}
          </div>
        )}

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {isSubmitting
              ? "Dodawanie..."
              : "Dodaj użytkownika"}
          </button>
        </div>
      </form>
    </Modal>
  );
}