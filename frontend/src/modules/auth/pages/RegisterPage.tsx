import { Link } from "react-router-dom";

import RegisterForm from "../components/RegisterForm";

export default function RegisterPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">Utwórz konto</h1>

        <RegisterForm />

        <p className="mt-6 text-center text-sm text-gray-600">
          Masz już konto?{" "}
          <Link to="/login" className="font-medium text-blue-600 hover:text-blue-700">
            Zaloguj się
          </Link>
        </p>
      </div>
    </div>
  );
}
