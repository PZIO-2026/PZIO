import { describe, it, expect } from "vitest";
import { loginSchema, registerSchema, editProfileSchema } from "./schemas";

describe("loginSchema", () => {
  it("accepts a valid email and password", () => {
    const result = loginSchema.safeParse({ email: "user@example.com", password: "secret" });
    expect(result.success).toBe(true);
  });

  it("rejects a malformed email with the Polish message", () => {
    const result = loginSchema.safeParse({ email: "not-an-email", password: "secret" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "email");
      expect(issue?.message).toBe("Nieprawidłowy format adresu email");
    }
  });

  it("rejects an empty password with the Polish message", () => {
    const result = loginSchema.safeParse({ email: "user@example.com", password: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "password");
      expect(issue?.message).toBe("Hasło jest wymagane");
    }
  });

  it("rejects when required fields are missing", () => {
    const result = loginSchema.safeParse({});
    expect(result.success).toBe(false);
  });
});

describe("registerSchema", () => {
  const valid = {
    email: "user@example.com",
    password: "password1",
    confirmPassword: "password1",
    firstName: "Anna",
    lastName: "Kowalska",
  };

  it("accepts a fully valid input", () => {
    expect(registerSchema.safeParse(valid).success).toBe(true);
  });

  it("rejects a malformed email", () => {
    const result = registerSchema.safeParse({ ...valid, email: "nope" });
    expect(result.success).toBe(false);
  });

  it("accepts a password exactly 8 characters long", () => {
    const password = "a".repeat(8);
    const result = registerSchema.safeParse({ ...valid, password, confirmPassword: password });
    expect(result.success).toBe(true);
  });

  it("rejects a password shorter than 8 characters", () => {
    const result = registerSchema.safeParse({ ...valid, password: "a".repeat(7) });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "password");
      expect(issue?.message).toBe("Hasło musi mieć co najmniej 8 znaków");
    }
  });

  it("accepts a password exactly 128 characters long", () => {
    const password = "a".repeat(128);
    const result = registerSchema.safeParse({ ...valid, password, confirmPassword: password });
    expect(result.success).toBe(true);
  });

  it("rejects a password longer than 128 characters", () => {
    const result = registerSchema.safeParse({ ...valid, password: "a".repeat(129) });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "password");
      expect(issue?.message).toBe("Hasło nie może przekraczać 128 znaków");
    }
  });

  it("rejects an empty firstName", () => {
    const result = registerSchema.safeParse({ ...valid, firstName: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "firstName");
      expect(issue?.message).toBe("Imię jest wymagane");
    }
  });

  it("accepts firstName exactly 100 characters long", () => {
    const result = registerSchema.safeParse({ ...valid, firstName: "a".repeat(100) });
    expect(result.success).toBe(true);
  });

  it("rejects firstName longer than 100 characters", () => {
    const result = registerSchema.safeParse({ ...valid, firstName: "a".repeat(101) });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "firstName");
      expect(issue?.message).toBe("Imię jest za długie");
    }
  });

  it("rejects an empty lastName", () => {
    const result = registerSchema.safeParse({ ...valid, lastName: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "lastName");
      expect(issue?.message).toBe("Nazwisko jest wymagane");
    }
  });

  it("accepts lastName exactly 100 characters long", () => {
    const result = registerSchema.safeParse({ ...valid, lastName: "a".repeat(100) });
    expect(result.success).toBe(true);
  });

  it("rejects lastName longer than 100 characters", () => {
    const result = registerSchema.safeParse({ ...valid, lastName: "a".repeat(101) });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "lastName");
      expect(issue?.message).toBe("Nazwisko jest za długie");
    }
  });

  it("rejects an empty confirmPassword", () => {
    const result = registerSchema.safeParse({ ...valid, confirmPassword: "" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "confirmPassword");
      expect(issue?.message).toBe("Powtórz hasło");
    }
  });

  it("rejects when confirmPassword does not match password", () => {
    const result = registerSchema.safeParse({ ...valid, confirmPassword: "different1" });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "confirmPassword");
      expect(issue?.message).toBe("Hasła nie są zgodne");
    }
  });
});

describe("editProfileSchema", () => {
  const valid = {
    firstName: "Anna",
    lastName: "Kowalska",
    avatar: "https://example.com/avatar.png",
  };

  it("accepts valid input with a non-empty avatar", () => {
    expect(editProfileSchema.safeParse(valid).success).toBe(true);
  });

  it("accepts an empty-string avatar", () => {
    expect(editProfileSchema.safeParse({ ...valid, avatar: "" }).success).toBe(true);
  });

  it("accepts an avatar exactly 255 characters long", () => {
    const result = editProfileSchema.safeParse({ ...valid, avatar: "a".repeat(255) });
    expect(result.success).toBe(true);
  });

  it("rejects an avatar longer than 255 characters", () => {
    const result = editProfileSchema.safeParse({ ...valid, avatar: "a".repeat(256) });
    expect(result.success).toBe(false);
    if (!result.success) {
      const issue = result.error.issues.find((i) => i.path[0] === "avatar");
      expect(issue?.message).toBe("URL awatara jest za długi");
    }
  });

  it("rejects an empty firstName", () => {
    const result = editProfileSchema.safeParse({ ...valid, firstName: "" });
    expect(result.success).toBe(false);
  });

  it("rejects an empty lastName", () => {
    const result = editProfileSchema.safeParse({ ...valid, lastName: "" });
    expect(result.success).toBe(false);
  });
});
