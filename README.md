# PZIO

Jira-like project task management system - an assignment for the *Software Engineering Group Project* course at AGH University of Krakow.

Main repository: [GitHub - PZIO](https://github.com/PZIO-2026/PZIO)

## Tech stack

- **Backend**: Python, FastAPI, SQLAlchemy
- **Frontend**: React, TypeScript, Tailwind CSS
- **Database**: SQLite (for development), PostgreSQL (for production)

For more details on one of the components, check out the respective README file in the `backend` and `frontend` directories.

## Pierwsze uruchomienie

Aplikacja działa według zasady *zero configuration* — po uruchomieniu backendu
i frontendu baza jest tworzona automatycznie, bez ręcznych skryptów SQL.
Pierwszy użytkownik zarejestrowany przez `POST /api/auth/register` otrzymuje
rolę **Administrator**. Każde kolejne konto domyślnie dostaje rolę
**TeamMember**.

Po zalogowaniu admin zarządza pozostałymi kontami z panelu `/admin` —
sekcja *Użytkownicy* pozwala zmienić rolę (`Guest`, `TeamMember`, `Manager`,
`Administrator`) dowolnego użytkownika poza sobą. Pod spodem wywoływany jest
endpoint `PATCH /api/users/{id}/role`.

### Uruchomienie z Dockerem

Cały stos (PostgreSQL + backend + frontend) startuje jednym poleceniem:

```bash
docker compose up --build
```

Po wystartowaniu wszystkich kontenerów:

- frontend — http://localhost:5173
- backend (Swagger) — http://localhost:8000/docs

`JWT_SECRET` zdefiniowany w `docker-compose.yml` to wartość deweloperska — przed
wdrożeniem produkcyjnym należy ją nadpisać własnym, losowym sekretem.

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
