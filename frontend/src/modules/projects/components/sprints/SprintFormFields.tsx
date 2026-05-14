// src/modules/projects/components/SprintFormFields.tsx

import type {
  FieldErrors,
  UseFormRegister,
} from "react-hook-form";

import type { SprintFormInput } from "../../schemas";

import {
  errorClass,
  inputClass,
  statusLabels,
} from "../../constants/sprintForm.constants";

interface Props {
  register: UseFormRegister<SprintFormInput>;

  errors: FieldErrors<SprintFormInput>;

  showStatus?: boolean;
}

export default function SprintFormFields({
  register,
  errors,
  showStatus = false,
}: Props) {
  return (
    <div className="grid gap-5">
      <div>
        <label className="text-sm font-medium text-gray-700">
          Nazwa sprintu
        </label>

        <input
          type="text"
          placeholder="Sprint 1"
          className={inputClass}
          {...register("name")}
        />

        {errors.name && (
          <p className={errorClass}>
            {errors.name.message}
          </p>
        )}
      </div>

      <div className="grid gap-5 lg:grid-cols-2">
        <div>
          <label className="text-sm font-medium text-gray-700">
            Data rozpoczęcia
          </label>

          <input
            type="date"
            className={inputClass}
            {...register("startDate")}
          />

          {errors.startDate && (
            <p className={errorClass}>
              {errors.startDate.message}
            </p>
          )}
        </div>

        <div>
          <label className="text-sm font-medium text-gray-700">
            Data zakończenia
          </label>

          <input
            type="date"
            className={inputClass}
            {...register("endDate")}
          />

          {errors.endDate && (
            <p className={errorClass}>
              {errors.endDate.message}
            </p>
          )}
        </div>
      </div>

      <div>
        <label className="text-sm font-medium text-gray-700">
          Cel sprintu
        </label>

        <textarea
          rows={4}
          className={inputClass}
          placeholder="Opis celów sprintu..."
          {...register("goal")}
        />

        {errors.goal && (
          <p className={errorClass}>
            {errors.goal.message}
          </p>
        )}
      </div>

      {showStatus && (
        <div>
          <label className="text-sm font-medium text-gray-700">
            Status sprintu
          </label>

          <select
            className={inputClass}
            {...register("status")}
          >
            <option value="planned">
              {statusLabels.planned}
            </option>

            <option value="active">
              {statusLabels.active}
            </option>

            <option value="completed">
              {statusLabels.completed}
            </option>
          </select>
        </div>
      )}
    </div>
  );
}