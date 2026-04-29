import { useAuth } from "../modules/auth/hooks";

export default function HomePage() {
  const { email, role, logout } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 text-center shadow">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Witaj w PZIO</h1>
        <p className="mb-1 text-sm text-gray-600">Zalogowany jako:</p>
        <p className="mb-4 text-lg font-medium text-gray-900">{email}</p>
        <p className="mb-6 text-sm text-gray-500">
          Rola: <span className="font-medium text-gray-700">{role}</span>
        </p>

        <button
          type="button"
          onClick={logout}
          className="w-full rounded-md bg-gray-900 px-4 py-2 font-medium text-white hover:bg-gray-700"
        >
          Wyloguj się
        </button>
      </div>
    </div>
  );
}
