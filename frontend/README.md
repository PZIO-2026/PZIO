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

| Command         | Purpose                                  |
| --------------- | ---------------------------------------- |
| `npm run dev`   | Vite dev server with HMR                 |
| `npm run build` | Type-check (`tsc -b`) + production build |
| `npm run lint`  | ESLint over the whole project            |
| `npm run preview` | Serve the production build locally     |

## Module structure

The frontend mirrors the backend's modular layout. Each backend module
(`backend/pzio/modules/<name>`) gets a matching `frontend/src/modules/<name>`
slice that owns its types, schemas, API calls, hooks, pages and components.

```
frontend/src/
├── api/
│   └── client.ts             # shared fetch wrapper, ApiError, Bearer token injection
├── modules/
│   └── auth/                 # Identity & Authorization (FR01, FR02, FR21)
│       ├── api.ts            # register(), login()
│       ├── AuthProvider.tsx  # context provider with localStorage persistence
│       ├── components/       # LoginForm, RegisterForm
│       ├── context.ts        # AuthContext + types
│       ├── hooks.ts          # useAuth()
│       ├── pages/            # LoginPage, RegisterPage
│       ├── schemas.ts        # zod validators
│       ├── storage.ts        # token + email persistence
│       └── types.ts          # User, TokenResponse, JwtClaims, UserRole
├── pages/
│   └── HomePage.tsx          # landing page after login
├── routes/
│   └── ProtectedRoute.tsx    # redirects unauthenticated users to /login
├── components/
│   └── App.tsx               # router + AuthProvider wiring
└── main.tsx
```

## Auth module — what is implemented

| Route        | Access     | What it does                                              |
| ------------ | ---------- | --------------------------------------------------------- |
| `/login`     | public     | Email + password → `POST /api/auth/login`                 |
| `/register`  | public     | Form → `POST /api/auth/register` → redirects to `/login`  |
| `/`          | protected  | Shows the logged-in user's email, role, and a logout button |
| `*` (other)  | redirect   | Falls back to `/`, which then bounces to `/login` if needed |

The access token is kept in `localStorage` (`pzio_auth_token`) along with the email
used for login (`pzio_auth_email`) so the session survives a page reload. The
provider validates `exp` on every load and clears storage if the token has expired.

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
