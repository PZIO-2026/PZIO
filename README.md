# PZIO

Jira-like project task management system - an assignment for the *Software Engineering Group Project* course at AGH University of Krakow.

Main repository: [GitHub - PZIO](https://github.com/PZIO-2026/PZIO)

## Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS
- **Database**: SQLite (for development), PostgreSQL (for production)

For more details on one of the components, check out the respective README file in the `backend` and `frontend` directories.

## First run

The application follows a *zero configuration* approach — once the backend
and frontend are running, the database is created automatically with no
manual SQL scripts. The first user registered through
`POST /api/auth/register` receives the **Administrator** role. Every
subsequent account defaults to **TeamMember**.

After logging in, an admin manages the other accounts from the `/admin`
panel — the *Users* section lets them change the role (`TeamMember`,
`Manager`, `Administrator`) of any user except themselves.
Under the hood this calls `PATCH /api/users/{id}/role`.

### Running with Docker

The full stack (PostgreSQL + backend + frontend) starts with a single
command, but you first need to provide a JWT secret. Copy the example
environment file and start the stack:

```bash
cp .env.example .env
docker compose up --build
```

Once all containers are up:

- frontend — http://localhost:5173
- backend (Swagger) — http://localhost:8000/docs

The `JWT_SECRET` in `.env.example` is a development value — before any
production deployment, override it with a long, random secret (the
backend container refuses to start without `JWT_SECRET` being set).

## Authors

- [Kevin Stuka](https://github.com/kevooo49)
- [Emanuel Sujeta](https://github.com/kiteniszhat)
- [Adam Szlósarczyk](https://github.com/AdamSzL)
- [Maciej Szymański](https://github.com/Macszym)
- [Igor Wadas](https://github.com/iwadas)
- [Emil Wajda](https://github.com/EmilWajda)
- [Kacper Wojciuch](https://github.com/Kacper0510)
- [Stanisław Wojtas](https://github.com/stanislawWojtas)
- [Marcin Wolder](https://github.com/marcinwolder)
- [Bartłomiej Wolny](https://github.com/BarWol)
