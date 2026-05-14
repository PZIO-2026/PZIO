import { useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../../../api/client";
import { oauthLogin } from "../api";
import { useAuth } from "../hooks";

export default function OAuthCallbackPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const auth = useAuth();
  const hasAttempted = useRef(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (hasAttempted.current) return;
    hasAttempted.current = true;

    const queryParams = new URLSearchParams(location.search);
    const hashParams = new URLSearchParams(location.hash.substring(1));

    const token = hashParams.get("access_token") || queryParams.get("access_token") || queryParams.get("code");
    const provider = queryParams.get("provider") || localStorage.getItem("oauth_provider");
    
    const returnedState = queryParams.get("state") || hashParams.get("state");
    const expectedState = localStorage.getItem("oauth_state");

    localStorage.removeItem("oauth_provider");
    localStorage.removeItem("oauth_state");

    if (!returnedState || !expectedState || returnedState !== expectedState) {
      setError("Weryfikacja bezpieczeństwa nie powiodła się (niezgodność stanu). Spróbuj ponownie.");
      return;
    }

    if (!token || !provider) {
      setError("Brak tokenu lub dostawcy OAuth.");
      return;
    }

    oauthLogin({ provider, oauthToken: token })
      .then((response) => {
        auth.login(response.accessToken);
        navigate("/", { replace: true });
      })
      .catch((err) => {
        if (err instanceof ApiError) {
          setError(err.detail || "Błąd autoryzacji OAuth.");
        } else {
          setError("Wystąpił błąd podczas autoryzacji serwera.");
        }
      });
  }, [location, navigate, auth]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4 py-12">
      <div className="w-full max-w-md rounded-lg bg-white p-8 shadow text-center">
        <h1 className="mb-6 text-2xl font-bold text-gray-900">Autoryzacja OAuth</h1>
        {error ? (
          <div className="rounded-md bg-red-50 p-4 text-red-700">
            <p className="mb-4">{error}</p>
            <button
              onClick={() => navigate("/login")}
              className="mt-2 inline-flex justify-center rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
            >
              Wróć do logowania
            </button>
          </div>
        ) : (
          <p className="text-gray-600">Przetwarzanie logowania, proszę czekać...</p>
        )}
      </div>
    </div>
  );
}