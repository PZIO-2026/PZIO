import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { projectMemberUpdateSchema, type ProjectMemberUpdateFormValues } from "../../schemas";
import { updateProjectMemberRoles } from "../../api";
import { ApiError } from "../../../../api/client";

import Modal from "../Modal";

interface EditProjectMemberModalProps {
  projectId: number;
  userId: number;
  email: string;
  currentRoles: string[];
  onClose: () => void;
  onSuccess: () => void;
}

const AVAILABLE_ROLES = [
  { value: "developer", label: "Developer" },
  { value: "qa", label: "QA / Tester" },
  { value: "maintainer", label: "Maintainer" },
  { value: "scrum_master", label: "Scrum Master" },
  { value: "project_owner", label: "Właściciel Projektu (Owner)" },
];

export default function EditProjectMemberModal({
  projectId,
  userId,
  email,
  currentRoles,
  onClose,
  onSuccess,
}: EditProjectMemberModalProps) {
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<ProjectMemberUpdateFormValues>({
    resolver: zodResolver(projectMemberUpdateSchema),
    defaultValues: {
      roles: currentRoles as ProjectMemberUpdateFormValues["roles"], 
    },
  });

  const onSubmit = async (data: ProjectMemberUpdateFormValues) => {
    try {
      await updateProjectMemberRoles(projectId, userId, data.roles);
      onSuccess();
      onClose();
    } catch (error) {
      if (error instanceof ApiError && error.status === 403) {
        setError("roles", {
          message: "Tylko Project Owner może edytować role innego Ownera lub nadawać tę rolę.",
        });
        return;
      }
      if (error instanceof ApiError && error.status === 400) {
        setError("roles", {
          message: "Projekt musi mieć co najmniej jednego Project Ownera — nie można usunąć tej roli ostatniemu właścicielowi.",
        });
        return;
      }
      if (error instanceof ApiError && error.status === 404) {
        setError("roles", {
          message: "Użytkownik nie jest już członkiem tego projektu.",
        });
        return;
      }
      if (error instanceof ApiError) {
        setError("roles", {
          message: "Nie udało się zaktualizować ról członka.",
        });
        return;
      }
      setError("root", {
        type: "manual",
        message: "Nie udało się połączyć z serwerem. Spróbuj ponownie.",
      });
    }
  };

  return (
    <Modal
      title={`Edytuj role użytkownika: ${email}`}
      isOpen={true}
      onClose={onClose}
    >
      <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
        
        {errors.root && (
          <div className="rounded-md bg-red-50 p-3 text-sm text-red-600 border border-red-200">
            {errors.root.message}
          </div>
        )}

        <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Role w projekcie *</label>
            <div className="space-y-2 bg-gray-50 p-3 rounded border border-gray-200">
              {AVAILABLE_ROLES.map((role) => (
                <label key={role.value} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="checkbox"
                    value={role.value}
                    {...register("roles")}
                    className="rounded text-blue-600 focus:ring-blue-500"
                  />
                  <span className="text-sm text-gray-800">{role.label}</span>
                </label>
              ))}
            </div>
            {errors.roles && <p className="text-red-500 text-sm mt-1">{errors.roles.message}</p>}
          </div>

          <div className="flex justify-end space-x-3 pt-4 border-t mt-6">
            <button
              type="button"
              onClick={onClose}
              disabled={isSubmitting}
              className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-md transition-colors"
            >
              Anuluj
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md disabled:opacity-50 transition-colors"
            >
              {isSubmitting ? "Zapisywanie..." : "Zapisz zmiany"}
            </button>
          </div>
        </form>
    </Modal>
  );
}