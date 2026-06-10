import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import OAuthButtons from "./OAuthButtons";

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("OAuthButtons", () => {
  it("renders both buttons and the separator when both providers are configured", () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "google-client-id");
    vi.stubEnv("VITE_GITHUB_CLIENT_ID", "github-client-id");

    render(<OAuthButtons />);

    expect(screen.getByRole("button", { name: /google/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /github/i })).toBeInTheDocument();
    expect(screen.getByText(/lub zaloguj się przez/i)).toBeInTheDocument();
  });

  it("hides the GitHub button when only Google is configured", () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "google-client-id");
    vi.stubEnv("VITE_GITHUB_CLIENT_ID", "");

    render(<OAuthButtons />);

    expect(screen.getByRole("button", { name: /google/i })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /github/i })).not.toBeInTheDocument();
    expect(screen.getByText(/lub zaloguj się przez/i)).toBeInTheDocument();
  });

  it("hides the Google button when only GitHub is configured", () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "");
    vi.stubEnv("VITE_GITHUB_CLIENT_ID", "github-client-id");

    render(<OAuthButtons />);

    expect(screen.queryByRole("button", { name: /google/i })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /github/i })).toBeInTheDocument();
    expect(screen.getByText(/lub zaloguj się przez/i)).toBeInTheDocument();
  });

  it("renders nothing when no provider is configured", () => {
    vi.stubEnv("VITE_GOOGLE_CLIENT_ID", "");
    vi.stubEnv("VITE_GITHUB_CLIENT_ID", "");

    const { container } = render(<OAuthButtons />);

    expect(container).toBeEmptyDOMElement();
    expect(screen.queryByText(/lub zaloguj się przez/i)).not.toBeInTheDocument();
  });
});
