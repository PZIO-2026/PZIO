import { useAuth } from "../modules/auth/hooks";
import AttachmentsSection from "../modules/communication/components/AttachmentsSection";
import CommentsSection from "../modules/communication/components/CommentsSection";

export default function HomePage() {
  const { user } = useAuth();

  if (user === null) return null;

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 space-y-10">
      <div>
        <h1 className="mb-2 text-3xl font-bold text-gray-900">
          Witaj, {user.firstName} {user.lastName}!
        </h1>
        <p className="text-gray-600">
          Zalogowany jako <span className="font-medium text-gray-900">{user.email}</span> (rola:{" "}
          <span className="font-medium text-gray-900">{user.role}</span>).
        </p>
      </div>

      <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
        <h2 className="text-xl font-bold text-gray-900 mb-6">Sekcja Testowa</h2>
        <div className="space-y-8">
          <AttachmentsSection taskId={1} />
          <hr className="border-gray-200" />
          <CommentsSection taskId={1} />
        </div>
      </div>
    </div>
  );
}
