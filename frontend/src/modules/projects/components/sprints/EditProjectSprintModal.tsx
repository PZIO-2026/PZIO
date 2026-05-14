import { useEffect, useState } from "react";

import { useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { updateSprint } from "../../api";

import type { Sprint } from "../../types";

import SprintFormFields from "./SprintFormFields";

import {
  sprintFormSchema,
  type SprintFormInput,
} from "../../schemas";

interface Props {
  isOpen: boolean;

  onClose: () => void;

  sprint: Sprint | null;

  onSprintUpdated: (sprint: Sprint) => void;
}

export default function EditProjectSprintModal({
  isOpen,
  onClose,
  sprint,
  onSprintUpdated,
}: Props) {
  const [submitError, setSubmitError] = useState<
    string | null
  >(null);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<SprintFormInput>({
    resolver: zodResolver(sprintFormSchema),

    defaultValues: {
      name: "",
      startDate: "",
      endDate: "",
      goal: "",
      status: "planned",
    },
  });

  useEffect(() => {
    if (!sprint) return;

    reset({
      name: sprint.name,
      // for proper formatting
      startDate: sprint.startDate.split("T")[0],
      endDate: sprint.endDate.split("T")[0],
      goal: sprint.goal ?? "",
      status: sprint.status,
    });
  }, [sprint, reset]);

  async function onSubmit(
    values: SprintFormInput,
  ) {
    if (!sprint) return;

    setSubmitError(null);

    try {
      const updated = await updateSprint(
        sprint.sprintId,
        {
          name: values.name,
          startDate: values.startDate,
          endDate: values.endDate,
          goal: values.goal,
          status: values.status,
        },
      );

      onSprintUpdated(updated);

      onClose();
    } catch (err) {
      if (err instanceof ApiError) {
        setSubmitError(err.detail);
      } else {
        setSubmitError(
          "Nie udało się zaktualizować sprintu.",
        );
      }
    }
  }

  return (
    <Modal
      title="Edytuj sprint"
      isOpen={isOpen}
      onClose={onClose}
    >
      <form
        onSubmit={handleSubmit(onSubmit)}
        className="space-y-5"
      >
        <SprintFormFields
          register={register}
          errors={errors}
          showStatus
        />

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
            className="rounded-md bg-blue-600 px-5 py-2.5 font-medium text-white hover:bg-blue-700 disabled:opacity-60"
          >
            {isSubmitting
              ? "Zapisywanie..."
              : "Zapisz zmiany"}
          </button>
        </div>
      </form>
    </Modal>
  );
}