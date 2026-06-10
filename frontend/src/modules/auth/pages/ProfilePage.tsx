import { useState } from "react";
import { useNavigate } from "react-router-dom";

import EditProfileForm from "../components/EditProfileForm";
import ChangeEmailForm from "../components/ChangeEmailForm";
import ChangePasswordForm from "../components/ChangePasswordForm";
import { useAuth } from "../hooks";
import { deleteMe } from "../api";
import type { User } from "../types";

export default function ProfilePage() {
  const { user, updateUser, logout } = useAuth();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);

  if (user === null) return null;

  function handleSaved(updatedUser: User) {
    updateUser(updatedUser);
    setIsEditing(false);
  }

  async function handleDeleteAccount() {
    if (window.confirm("Czy na pewno chcesz bezpowrotnie usunąć swoje konto? Tego działania nie można cofnąć.")) {
      try {
        await deleteMe();
        logout();
        navigate("/login");
      } catch {
        alert("Wystąpił błąd podczas usuwania konta.");
      }
    }
  }

  const hasAvatar = user.avatar !== null && user.avatar !== "";
  const initials = `${user.firstName.charAt(0)}${user.lastName.charAt(0)}`.toUpperCase();

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 space-y-6">
      {/* Informacje o profilu i edycja */}
      <div className="rounded-lg bg-white p-6 shadow">
        <div className="mb-6 flex items-start justify-between">
          <h1 className="text-2xl font-bold text-gray-900">Mój profil</h1>
          {!isEditing && (
            <button
              type="button"
              onClick={() => setIsEditing(true)}
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
            onCancel={() => setIsEditing(false)}
          />
        ) : (
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
            </dl>
          </div>
        )}
      </div>

      {/* Zarządzanie bezpieczeństwem */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-bold text-gray-900">Zmień adres email</h2>
          <ChangeEmailForm user={user} onSuccess={updateUser} />
        </div>

        <div className="rounded-lg bg-white p-6 shadow">
          <h2 className="mb-4 text-lg font-bold text-gray-900">Zmień hasło</h2>
          <ChangePasswordForm />
        </div>
      </div>

      {/* Strefa niebezpieczna */}
      <div className="rounded-lg border border-red-200 bg-red-50 p-6 shadow-sm">
        <h2 className="mb-2 text-lg font-bold text-red-800">Strefa niebezpieczna</h2>
        <p className="mb-4 text-sm text-red-600">
          Trwałe usunięcie konta spowoduje wykasowanie wszystkich Twoich danych z systemu. Tego działania nie można cofnąć.
        </p>
        <button
          onClick={handleDeleteAccount}
          className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700"
        >
          Usuń konto
        </button>
      </div>
    </div>
  );
}