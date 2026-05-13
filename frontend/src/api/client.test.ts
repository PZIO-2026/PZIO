import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError, AUTH_EXPIRED_EVENT, apiFetch } from "./client";
import { setStoredToken } from "../modules/auth/storage";

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

describe("apiFetch", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    // mockImplementation (not mockResolvedValue) so each call gets a fresh
    // Response — Response bodies are streams and can only be consumed once.
    fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse({ ok: true })));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("URL construction", () => {
    it("prefixes the path with the default base URL", async () => {
      await apiFetch("/api/users/me");
      expect(fetchMock).toHaveBeenCalledWith("http://localhost:8000/api/users/me", expect.anything());
    });
    // TODO: cover the VITE_API_BASE_URL override path. The env var is read at
    // module load time in client.ts, so vi.stubEnv after import has no effect.
    // Follow-up: refactor client.ts to read the env lazily, then test it here.
  });

  describe("headers", () => {
    it("always sends Accept: application/json", async () => {
      await apiFetch("/api/users/me");
      const init = fetchMock.mock.calls[0][1] as RequestInit;
      const headers = new Headers(init.headers);
      expect(headers.get("Accept")).toBe("application/json");
    });

    it("omits Content-Type when no body is provided", async () => {
      await apiFetch("/api/users/me");
      const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
      expect(headers.get("Content-Type")).toBeNull();
    });

    it("sets Content-Type: application/json when a body is provided", async () => {
      await apiFetch("/api/users/me", { method: "PATCH", body: { firstName: "A" } });
      const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
      expect(headers.get("Content-Type")).toBe("application/json");
    });

    it("adds Authorization when a token is stored", async () => {
      setStoredToken("the-token");
      await apiFetch("/api/users/me");
      const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
      expect(headers.get("Authorization")).toBe("Bearer the-token");
    });

    it("omits Authorization when no token is stored", async () => {
      await apiFetch("/api/users/me");
      const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
      expect(headers.get("Authorization")).toBeNull();
    });

    it("preserves caller-supplied headers", async () => {
      await apiFetch("/api/users/me", { headers: { "X-Trace-Id": "abc" } });
      const headers = new Headers((fetchMock.mock.calls[0][1] as RequestInit).headers);
      expect(headers.get("X-Trace-Id")).toBe("abc");
    });
  });

  describe("request body", () => {
    it("serializes the body as JSON", async () => {
      await apiFetch("/api/auth/login", { method: "POST", body: { email: "a@b" } });
      const init = fetchMock.mock.calls[0][1] as RequestInit;
      expect(init.body).toBe(JSON.stringify({ email: "a@b" }));
    });

    it("sends body: undefined when no body is given", async () => {
      await apiFetch("/api/users/me");
      const init = fetchMock.mock.calls[0][1] as RequestInit;
      expect(init.body).toBeUndefined();
    });
  });

  describe("response handling", () => {
    it("returns parsed JSON for 200 responses", async () => {
      fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ id: 1, email: "a@b" }, { status: 200 })));
      const result = await apiFetch<{ id: number; email: string }>("/api/users/me");
      expect(result).toEqual({ id: 1, email: "a@b" });
    });

    it("returns undefined for 204 responses", async () => {
      fetchMock.mockImplementationOnce(() => Promise.resolve(new Response(null, { status: 204 })));
      const result = await apiFetch("/api/something");
      expect(result).toBeUndefined();
    });

    it("throws ApiError on non-OK responses", async () => {
      fetchMock.mockImplementationOnce(() =>
        Promise.resolve(jsonResponse({ detail: "Boom" }, { status: 400, statusText: "Bad Request" })),
      );
      await expect(apiFetch("/api/x")).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("ApiError shape", () => {
    it("exposes the response status", async () => {
      fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ detail: "Boom" }, { status: 409 })));
      await expect(apiFetch("/api/x")).rejects.toMatchObject({ status: 409 });
    });

    it("takes detail from a JSON body's detail field", async () => {
      fetchMock.mockImplementationOnce(() =>
        Promise.resolve(jsonResponse({ detail: "Email already in use" }, { status: 409 })),
      );
      await expect(apiFetch("/api/auth/register", { method: "POST", body: {} })).rejects.toMatchObject({
        detail: "Email already in use",
        message: "Email already in use",
        name: "ApiError",
      });
    });

    it("falls back to statusText when the body is not JSON", async () => {
      fetchMock.mockImplementationOnce(() =>
        Promise.resolve(new Response("oops", { status: 500, statusText: "Internal Server Error" })),
      );
      await expect(apiFetch("/api/x")).rejects.toMatchObject({
        detail: "Internal Server Error",
        status: 500,
      });
    });

    it("falls back to statusText when the JSON body has no detail string", async () => {
      fetchMock.mockImplementationOnce(() =>
        Promise.resolve(jsonResponse({ other: "x" }, { status: 500, statusText: "Internal Server Error" })),
      );
      await expect(apiFetch("/api/x")).rejects.toMatchObject({
        detail: "Internal Server Error",
      });
    });
  });

  describe("AUTH_EXPIRED_EVENT dispatch", () => {
    function withListener(run: (listener: ReturnType<typeof vi.fn>) => Promise<void>) {
      return async () => {
        const listener = vi.fn();
        window.addEventListener(AUTH_EXPIRED_EVENT, listener);
        try {
          await run(listener);
        } finally {
          window.removeEventListener(AUTH_EXPIRED_EVENT, listener);
        }
      };
    }

    it(
      "dispatches on 401 for /api/users/me",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ detail: "Expired" }, { status: 401 })));
        await expect(apiFetch("/api/users/me")).rejects.toBeInstanceOf(ApiError);
        expect(listener).toHaveBeenCalledTimes(1);
      }),
    );

    it(
      "dispatches on 401 for non-auth paths (/api/projects)",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ detail: "Expired" }, { status: 401 })));
        await expect(apiFetch("/api/projects")).rejects.toBeInstanceOf(ApiError);
        expect(listener).toHaveBeenCalledTimes(1);
      }),
    );

    it(
      "does NOT dispatch on 401 for /api/auth/login",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() =>
          Promise.resolve(jsonResponse({ detail: "Bad credentials" }, { status: 401 })),
        );
        await expect(apiFetch("/api/auth/login", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
        expect(listener).not.toHaveBeenCalled();
      }),
    );

    it(
      "does NOT dispatch on 401 for /api/auth/register",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() =>
          Promise.resolve(jsonResponse({ detail: "Bad credentials" }, { status: 401 })),
        );
        await expect(apiFetch("/api/auth/register", { method: "POST", body: {} })).rejects.toBeInstanceOf(ApiError);
        expect(listener).not.toHaveBeenCalled();
      }),
    );

    it(
      "does NOT dispatch on 401 for /api/auth/reset-password",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ detail: "Nope" }, { status: 401 })));
        await expect(apiFetch("/api/auth/reset-password", { method: "POST", body: {} })).rejects.toBeInstanceOf(
          ApiError,
        );
        expect(listener).not.toHaveBeenCalled();
      }),
    );

    it(
      "does NOT dispatch on 403 for a protected path",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse({ detail: "Forbidden" }, { status: 403 })));
        await expect(apiFetch("/api/users")).rejects.toBeInstanceOf(ApiError);
        expect(listener).not.toHaveBeenCalled();
      }),
    );

    it(
      "does NOT dispatch on 500 for a protected path",
      withListener(async (listener) => {
        fetchMock.mockImplementationOnce(() =>
          Promise.resolve(jsonResponse({ detail: "Server error" }, { status: 500 })),
        );
        await expect(apiFetch("/api/users")).rejects.toBeInstanceOf(ApiError);
        expect(listener).not.toHaveBeenCalled();
      }),
    );
  });
});
