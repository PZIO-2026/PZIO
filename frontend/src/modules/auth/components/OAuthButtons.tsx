import { useState } from "react";

export default function OAuthButtons() {
  const [error, setError] = useState<string | null>(null);

  function handleOAuth(provider: string) {
    try {
      localStorage.setItem("oauth_provider", provider);

      const clientId =
        provider === "google"
          ? import.meta.env.VITE_GOOGLE_CLIENT_ID
          : import.meta.env.VITE_GITHUB_CLIENT_ID;

      if (!clientId) {
        setError(`Missing client ID configuration for ${provider}.`);
        return;
      }

      const redirectUri = window.location.origin + "/oauth/callback";

      let oauthUrl = "";
      if (provider === "google") {
        oauthUrl = `https://accounts.google.com/o/oauth2/v2/auth?client_id=${clientId}&response_type=token&redirect_uri=${encodeURIComponent(
          redirectUri
        )}&scope=${encodeURIComponent("email profile")}`;
      } else if (provider === "github") {
        oauthUrl = `https://github.com/login/oauth/authorize?client_id=${clientId}&redirect_uri=${encodeURIComponent(
          redirectUri
        )}&scope=user:email`;
      }

      window.location.href = oauthUrl;
    } catch {
      setError("Failed to start OAuth login.");
    }
  }

  return (
    <div className="mt-6">
      <div className="relative">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-gray-300" />
        </div>
        <div className="relative flex justify-center text-sm">
          <span className="bg-white px-2 text-gray-500">Or continue with</span>
        </div>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-3">
        <button
          type="button"
          onClick={() => handleOAuth("google")}
          className="inline-flex w-full justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 transition-colors"
        >
          Google
        </button>
        <button
          type="button"
          onClick={() => handleOAuth("github")}
          className="inline-flex w-full justify-center rounded-md border border-transparent bg-gray-900 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-gray-800 transition-colors"
        >
          GitHub
        </button>
      </div>
      {error && <p className="mt-2 text-center text-sm text-red-600">{error}</p>}
    </div>
  );
}