import { useAuth } from "../modules/auth/hooks";

export default function HomePage() {
  const { user } = useAuth();

  if (user === null) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <h1 className="mb-2 text-3xl font-bold text-gray-900">
        Witaj, {user.firstName} {user.lastName}!
      </h1>
      <p className="text-gray-600">
        Zalogowany jako <span className="font-medium text-gray-900">{user.email}</span> (rola:{" "}
        <span className="font-medium text-gray-900">{user.role}</span>).
      </p>
    </div>
  );
}
