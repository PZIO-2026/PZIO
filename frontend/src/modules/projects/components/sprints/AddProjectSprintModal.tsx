import { useState } from "react";

import { useForm } from "react-hook-form";

import { zodResolver } from "@hookform/resolvers/zod";

import Modal from "../Modal";

import { ApiError } from "../../../../api/client";

import { createSprint } from "../../api";

import type { Sprint } from "../../types";

import SprintFormFields from "./SprintFormFields";

import {
  createSprintFormSchema,
  todayLocalISO,
  type SprintFormInput,
} from "../../schemas";

interface Props {
  isOpen: boolean;

  onClose: () => void;

  projectId: number;

  onSprintCreated: (sprint: Sprint) => void;
}

export default function AddProjectSprintModal({
  isOpen,
  onClose,
  projectId,
  onSprintCreated,
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
    resolver: zodResolver(createSprintFormSchema),

    defaultValues: {
      name: "",
      startDate: "",
      endDate: "",
      goal: "",
    },
  });

  async function onSubmit(
    values: SprintFormInput,
  ) {
    setSubmitError(null);

    try {
      const created = await createSprint(
        projectId,
        values,
      );

      onSprintCreated(created);

      reset();

      onClose();
    } catch (err) {
      if (err instanceof ApiError && err.status === 400) {
        setSubmitError("Data zakończenia sprintu musi być późniejsza niż data rozpoczęcia.");
        return;
      }
      if (err instanceof ApiError && err.status === 403) {
        setSubmitError("Nie masz uprawnień do tworzenia sprintów w tym projekcie.");
        return;
      }
      if (err instanceof ApiError && err.status === 422) {
        setSubmitError("Podane dane sprintu są nieprawidłowe.");
        return;
      }
      if (err instanceof ApiError) {
        setSubmitError("Nie udało się utworzyć sprintu.");
        return;
      }
      setSubmitError("Nie udało się połączyć z serwerem. Spróbuj ponownie.");
    }
  }

  return (
    <Modal
      title="Dodaj sprint"
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
          minStartDate={todayLocalISO()}
        />

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
              ? "Tworzenie..."
              : "Utwórz sprint"}
          </button>
        </div>
      </form>
    </Modal>
  );
}