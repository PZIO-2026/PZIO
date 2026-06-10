import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { fetchUsers, updateUserRole } from "./api";

function jsonResponse(body: unknown, init: ResponseInit = {}): Response {
  return new Response(JSON.stringify(body), {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
}

const PAGINATED_PAYLOAD = {
  items: [],
  total: 0,
  page: 1,
  size: 50,
};

describe("admin api", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    fetchMock = vi.fn().mockImplementation(() => Promise.resolve(jsonResponse(PAGINATED_PAYLOAD)));
    vi.stubGlobal("fetch", fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  describe("fetchUsers", () => {
    it("calls GET /api/users without query string when no params are given", async () => {
      await fetchUsers();
      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("http://localhost:8000/api/users");
      expect((init as RequestInit).method ?? "GET").toBe("GET");
    });

    it("appends only the provided query params", async () => {
      await fetchUsers({ search: "ada", page: 2 });
      const [url] = fetchMock.mock.calls[0];
      // URLSearchParams iterates in insertion order, so the relative order of keys matters.
      expect(url).toBe("http://localhost:8000/api/users?search=ada&page=2");
    });

    it("includes size when provided", async () => {
      await fetchUsers({ page: 3, size: 25 });
      const [url] = fetchMock.mock.calls[0];
      expect(url).toBe("http://localhost:8000/api/users?page=3&size=25");
    });

    it("returns the paginated payload as parsed JSON", async () => {
      const payload = {
        items: [
          {
            userId: 1,
            email: "ada@example.com",
            firstName: "Ada",
            lastName: "Lovelace",
            avatar: null,
            role: "TeamMember",
            isActive: true,
            createdAt: "2026-01-01T00:00:00Z",
          },
        ],
        total: 1,
        page: 1,
        size: 50,
      };
      fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse(payload)));
      const result = await fetchUsers();
      expect(result).toEqual(payload);
    });
  });

  describe("updateUserRole", () => {
    it("PATCHes /api/users/{id}/role with a JSON role body", async () => {
      const user = {
        userId: 42,
        email: "alice@example.com",
        firstName: "Alice",
        lastName: "Liddell",
        avatar: null,
        role: "Manager",
        isActive: true,
        createdAt: "2026-01-01T00:00:00Z",
      };
      fetchMock.mockImplementationOnce(() => Promise.resolve(jsonResponse(user)));

      const result = await updateUserRole(42, "Manager");

      const [url, init] = fetchMock.mock.calls[0];
      expect(url).toBe("http://localhost:8000/api/users/42/role");
      expect((init as RequestInit).method).toBe("PATCH");
      expect((init as RequestInit).body).toBe(JSON.stringify({ role: "Manager" }));
      expect(result).toEqual(user);
    });
  });
});
