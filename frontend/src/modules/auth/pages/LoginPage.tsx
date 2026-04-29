import { Link, useLocation } from "react-router-dom";

import LoginForm from "../components/LoginForm";

function readRegisteredEmail(state: unknown): string | null {
  if (typeof state === "object" && state !== null && "registeredEmail" in state) {
    const value = (state as { registeredEmail?: unknown }).registeredEmail;
    if (typeof value === "string" && value.length > 0) return value;
  }
  return null;
}

export default function LoginPage() {
  const location = useLocation();
  const registeredEmail = readRegisteredEmail(location.state);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow">
        <h1 className="mb-6 text-center text-2xl font-bold text-gray-900">Zaloguj się</h1>

        {registeredEmail !== null && (
          <p className="mb-4 rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
            Konto <strong>{registeredEmail}</strong> zostało utworzone. Zaloguj się, aby kontynuować.
          </p>
        )}

        <LoginForm />

        <p className="mt-6 text-center text-sm text-gray-600">
          Nie masz konta?{" "}
          <Link to="/register" className="font-medium text-blue-600 hover:text-blue-700">
            Zarejestruj się
          </Link>
        </p>
      </div>
    </div>
  );
}
