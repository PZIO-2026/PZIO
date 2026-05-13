import { describe, it, expect } from "vitest";
import { getStoredToken, setStoredToken, clearStoredToken } from "./storage";

const TOKEN_KEY = "pzio_auth_token";

describe("auth storage", () => {
  it("returns null when no token has been stored", () => {
    expect(getStoredToken()).toBeNull();
  });

  it("returns the token that was previously stored", () => {
    setStoredToken("abc");
    expect(getStoredToken()).toBe("abc");
  });

  it("overwrites a previously stored token", () => {
    setStoredToken("first");
    setStoredToken("second");
    expect(getStoredToken()).toBe("second");
  });

  it("clears the stored token", () => {
    setStoredToken("abc");
    clearStoredToken();
    expect(getStoredToken()).toBeNull();
  });

  it("uses the documented localStorage key", () => {
    // The key is a cross-module public contract — AuthProvider and any other
    // reader can pull the token out under this exact name.
    setStoredToken("xyz");
    expect(localStorage.getItem(TOKEN_KEY)).toBe("xyz");
  });
});
