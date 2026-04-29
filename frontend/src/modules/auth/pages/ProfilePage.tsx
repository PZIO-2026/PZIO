import { useState } from "react";

import EditProfileForm from "../components/EditProfileForm";
import { useAuth } from "../hooks";
import type { User } from "../types";

export default function ProfilePage() {
  const { user, updateUser } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  if (user === null) return null;

  function handleSaved(updatedUser: User) {
    updateUser(updatedUser);
    setIsEditing(false);
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-6 flex items-start justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Mój profil</h1>
          {!isEditing && (
            <button
              type="button"
              onClick={() => {
                setIsEditing(true);
              }}
              className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700"
            >
              Edytuj
            </button>
          )}
        </div>

        {isEditing ? (
          <EditProfileForm
            user={user}
            onSuccess={handleSaved}
            onCancel={() => {
              setIsEditing(false);
            }}
          />
        ) : (
          <ProfileView user={user} />
        )}
      </div>
    </div>
  );
}

function ProfileView({ user }: { user: User }) {
  const hasAvatar = user.avatar !== null && user.avatar !== "";
  const initials = `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        {hasAvatar ? (
          <img
            src={user.avatar ?? ""}
            alt="Awatar"
            className="h-16 w-16 rounded-full object-cover"
          />
        ) : (
          <div className="flex h-16 w-16 items-center justify-center rounded-full bg-gray-200 text-xl font-medium text-gray-700">
            {initials}
          </div>
        )}
        <div>
          <p className="text-xl font-medium text-gray-900">
            {user.firstName} {user.lastName}
          </p>
          <p className="text-sm text-gray-600">{user.email}</p>
        </div>
      </div>

      <dl className="grid grid-cols-1 gap-4 border-t border-gray-200 pt-6 sm:grid-cols-2">
        <div>
          <dt className="text-sm text-gray-500">Rola</dt>
          <dd className="text-base font-medium text-gray-900">{user.role}</dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Status</dt>
          <dd className="text-base font-medium text-gray-900">
            {user.isActive ? "Aktywne" : "Nieaktywne"}
          </dd>
        </div>
        <div>
          <dt className="text-sm text-gray-500">Data utworzenia</dt>
          <dd className="text-base font-medium text-gray-900">
            {new Date(user.createdAt).toLocaleDateString("pl-PL")}
          </dd>
        </div>
      </dl>
    </div>
  );
}
