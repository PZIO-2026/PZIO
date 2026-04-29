# PZIO Frontend

React 19 SPA for the PZIO Task Management System. TypeScript, Vite, Tailwind CSS.

## Quick start

```bash
npm install
cp .env.example .env   # adjust VITE_API_BASE_URL if your backend runs elsewhere
npm run dev
```

The dev server runs on `http://localhost:5173`. It expects the PZIO backend to be
reachable at `VITE_API_BASE_URL` (default `http://localhost:8000`) — see
`backend/README.md` for how to start it.

## Available scripts

| Command           | Purpose                                  |
| ----------------- | ---------------------------------------- |
| `npm run dev`     | Vite dev server with HMR                 |
| `npm run build`   | Type-check (`tsc -b`) + production build |
| `npm run lint`    | ESLint over the whole project            |
| `npm run preview` | Serve the production build locally       |

## Module structure

The frontend mirrors the backend's modular layout. Each backend module
(`backend/pzio/modules/<name>`) gets a matching `frontend/src/modules/<name>`
slice that owns its types, schemas, API calls, hooks, pages and components.

```
frontend/src/
├── api/
│   └── client.ts                # shared fetch wrapper, ApiError, Bearer token injection,
│                                # global 401 interceptor (pzio:auth-expired event)
├── modules/
│   └── auth/                    # Identity & Authorization (FR01, FR02, FR21)
│       ├── api.ts               # register(), login(), getMe(), updateMe()
│       ├── AuthProvider.tsx     # fetches /me on token change, listens for 401 events
│       ├── components/          # LoginForm, RegisterForm, EditProfileForm
│       ├── context.ts           # AuthContext + types
│       ├── hooks.ts             # useAuth()
│       ├── pages/               # LoginPage, RegisterPage, ProfilePage
│       ├── schemas.ts           # zod validators
│       ├── storage.ts           # access token persistence
│       └── types.ts             # User, TokenResponse, JwtClaims, UserRole
├── pages/
│   └── HomePage.tsx             # landing page after login
├── routes/
│   └── ProtectedRoute.tsx       # redirects unauthenticated users to /login
├── components/
│   ├── App.tsx                  # router + AuthProvider wiring
│   └── AppLayout.tsx            # navbar + Outlet shared by every protected page
└── main.tsx
```

## Auth module — what is implemented

| Route        | Access     | What it does                                                              |
| ------------ | ---------- | ------------------------------------------------------------------------- |
| `/login`     | public     | Email + password → `POST /api/auth/login`                                 |
| `/register`  | public     | Form → `POST /api/auth/register` → redirects to `/login`                  |
| `/`          | protected  | Welcome screen with the logged-in user's name                             |
| `/profile`   | protected  | View and edit the current user's profile (`GET` / `PATCH /api/users/me`)  |
| `*` (other)  | redirect   | Falls back to `/`, which then bounces to `/login` if needed               |

The access token is kept in `localStorage` (`pzio_auth_token`) so the session
survives a page reload. On app start (and after every login) `AuthProvider`
fetches `GET /api/users/me` to populate the `User` in state. If `/me` returns
401 — or any other call to a protected endpoint comes back 401 — the global
interceptor in `api/client.ts` dispatches a `pzio:auth-expired` window event;
`AuthProvider` listens for it, clears the token, and `ProtectedRoute` bounces
the user to `/login`. Public auth paths (`/api/auth/*`) are excluded from the
interceptor so a wrong-password submission doesn't kick a freshly-typing user
out of the form.

## Configuration

Settings come from environment variables (or `.env`, see `.env.example`).

| Variable             | Default                  | Notes                                            |
| -------------------- | ------------------------ | ------------------------------------------------ |
| `VITE_API_BASE_URL`  | `http://localhost:8000`  | Base URL of the PZIO backend.                    |

## Tech stack

- **React** 19 (with React Compiler) + **TypeScript** 6
- **Vite** 8 + **Tailwind CSS** 4
- **react-router-dom** 7 — client-side routing
- **react-hook-form** + **zod** + **@hookform/resolvers** — form state & validation
