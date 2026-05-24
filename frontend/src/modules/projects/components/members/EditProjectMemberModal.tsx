import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { projectMemberUpdateSchema, type ProjectMemberUpdateFormValues } from "../../schemas";
import { updateProjectMemberRoles } from "../../api";
import { ApiError } from "../../../../api/client";
import { useAuth } from "../../../auth/hooks";
import Modal from "../Modal";

const inputClass =
  "mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm " +
  "focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500";

const errorClass = "mt-1 text-sm text-red-600";

const roleLabels: Record<string, string> = {
  project_owner: "Project Owner",
  scrum_master: "Scrum Master",
  developer: "Developer",
  qa: "QA Engineer",
  maintainer: "Maintainer",
};

interface EditProjectMemberModalProps {
  projectId: number;
  userId: number;
  email: string;
  currentRoles: string[];
  onClose: () => void;
  onSuccess: () => void;
}

export default function EditProjectMemberModal({
  projectId,
  userId,
  email,
  currentRoles,
  onClose,
  onSuccess,
}: EditProjectMemberModalProps) {
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { user: currentUser } = useAuth();
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ProjectMemberUpdateFormValues>({
    resolver: zodResolver(projectMemberUpdateSchema),
    defaultValues: {
      roles: currentRoles as ProjectMemberUpdateFormValues["roles"], 
    },
  });

  const onSubmit = async (data: ProjectMemberUpdateFormValues) => {
    setSubmitError(null);
    const isEditingSelf = currentUser !== null && currentUser.userId === userId;

    const wasOwner = currentRoles.includes("project_owner");
    const willBeOwner = data.roles.includes("project_owner");

    const wasScrumMaster = currentRoles.includes("scrum_master");
    const willBeScrumMaster = data.roles.includes("scrum_master");

    const isLosingOwner = wasOwner && !willBeOwner;
    const isLosingScrumMaster = wasScrumMaster && !willBeScrumMaster && !willBeOwner;

    if (isEditingSelf && (isLosingOwner || isLosingScrumMaster)) {
      const confirmed = window.confirm(
        "OSTRZEŻENIE:\n\nPróbujesz odebrać sobie uprawnienia zarządcze (Project Owner lub Scrum Master). " +
        "Jeśli zatwierdzisz tę zmianę, stracisz możliwość zarządzania członkami projektu i nie będziesz mógł " +
        "samodzielnie przywrócić sobie tej roli.\n\nCzy na pewno chcesz kontynuować?"
      );
      if (!confirmed) return;
    }
    try {
      await updateProjectMemberRoles(projectId, userId, data.roles);
      onSuccess();
      onClose();
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) {
        setSubmitError("Tylko Project Owner może edytować role innego Ownera lub nadawać tę rolę.");
        return;
      }
      if (error instanceof ApiError && error.status === 400) {
        setSubmitError("Projekt musi mieć co najmniej jednego Project Ownera — nie można usunąć tej roli ostatniemu właścicielowi.");
        return;
      }
      if (error instanceof ApiError && error.status === 404) {
        setSubmitError("Użytkownik nie jest już członkiem tego projektu.");
        return;
      }
      if (error instanceof ApiError) {
        setSubmitError("Nie udało się zaktualizować ról członka.");
        return;
      }
      setSubmitError("Nie udało się połączyć z serwerem. Spróbuj ponownie.");
    }
  };

  return (
    <Modal
      title="Edytuj użytkownika"
      isOpen={true}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        
        <div>
          <label className="block text-sm font-medium text-gray-700">
            E-mail użytkownika
          </label>
          <input
            type="email"
            disabled
            value={email}
            className={`${inputClass} cursor-not-allowed bg-gray-100 text-gray-500 opacity-70`}
          />
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
                "maintainer",
              ] as const
            ).map((roleValue) => (
              <label
                key={roleValue}
                className="flex cursor-pointer items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm transition-colors hover:bg-gray-50"
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

        <div className="flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="rounded-md border border-gray-300 px-5 py-2.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
          >
            Anuluj
          </button>
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-60"
          >
            {isSubmitting ? "Zapisywanie..." : "Zapisz zmiany"}
          </button>
        </div>
      </form>
    </Modal>
  );
}