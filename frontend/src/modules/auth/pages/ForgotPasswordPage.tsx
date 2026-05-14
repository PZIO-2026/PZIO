import { Link } from "react-router-dom";

import ForgotPasswordForm from "../components/ForgotPasswordForm";

export default function ForgotPasswordPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-2 text-center text-2xl font-bold text-gray-900">Zapomniane hasło</h1>
        <p className="mb-6 text-center text-sm text-gray-600">
          Podaj adres email, na który wyślemy link do zresetowania hasła.
        </p>

        <ForgotPasswordForm />

        <p className="mt-6 text-center text-sm text-gray-600">
          Pamiętasz hasło?{" "}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700">
            Wróć do logowania
          </Link>
        </p>
      </div>
    </div>
  );
}
