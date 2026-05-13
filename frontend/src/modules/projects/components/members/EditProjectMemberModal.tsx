import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { projectMemberUpdateSchema } from "../../schemas";
import { updateProjectMemberRoles } from "../../api";
import { ApiError } from "../../../../api/client";

interface EditProjectMemberModalProps {
  projectId: number;
  userId: number;
  email: string;
  currentRoles: string[];
  onClose: () => void;
  onSuccess: () => void;
}

interface FormValues {
  roles: string[];
}

const AVAILABLE_ROLES = [
  { value: "developer", label: "Developer" },
  { value: "qa", label: "QA / Tester" },
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
    formState: { errors, isSubmitting },
  } = useForm<FormValues>({
    resolver: zodResolver(projectMemberUpdateSchema) as any,
    defaultValues: {
      roles: currentRoles, 
    },
  });

  const onSubmit = async (data: FormValues) => {
    try {
      await updateProjectMemberRoles(projectId, userId, data.roles);
      onSuccess();
      onClose();
    } catch (error) {
      console.error("Błąd edycji ról:", error);
      if (error instanceof ApiError) {
        alert(error.detail);
      } else {
        alert("Nie udało się zaktualizować ról użytkownika.");
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
        <h2 className="text-xl font-bold mb-4">Edytuj role użytkownika: {email}</h2>
        
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
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
      </div>
    </div>
  );
}