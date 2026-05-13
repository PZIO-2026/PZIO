import { Link, useParams } from "react-router-dom";

import ResetPasswordConfirmForm from "../components/ResetPasswordConfirmForm";

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();

  const hasValidToken = token !== undefined && token.length > 0;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">Ustaw nowe hasło</h1>

        {hasValidToken ? (
          <>
            <p className="mb-6 text-center text-sm text-gray-600">
              Wpisz nowe hasło dla swojego konta.
            </p>
            <ResetPasswordConfirmForm token={token} />
            <p className="mt-6 text-center text-sm text-gray-600">
              <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700">
                Wróć do logowania
              </Link>
            </p>
          </>
        ) : (
          <>
            <p
              role="alert"
              className="rounded-md bg-red-50 px-3 py-3 text-sm text-red-700"
            >
              Nieprawidłowy link do resetu hasła. Poproś o nowy.
            </p>
            <p className="mt-6 text-center text-sm text-gray-600">
              <Link
                to="/forgot-password"
                className="font-medium text-blue-600 hover:text-blue-700"
              >
                Wyślij nowy link
              </Link>
            </p>
          </>
        )}
      </div>
    </div>
  );
}
