# PZIO REST API — przewodnik integracyjny

Dokumentacja API dla **Systemu Zarządzania Zadaniami (PZIO)**. Materiał
adresowany do zewnętrznych zespołów testujących integrację.

- **Maszynowe źródło prawdy:** [`openapi.yaml`](./openapi.yaml) (OpenAPI 3.1).
- **Interaktywne przeglądarki** (gdy backend działa lokalnie):
  - Swagger UI — <http://localhost:8000/docs>
  - ReDoc — <http://localhost:8000/redoc>
  - Surowy JSON — <http://localhost:8000/openapi.json>

Wszystkie żądania i odpowiedzi używają `application/json` z kodowaniem UTF-8.
Pole JSON jest zawsze w **camelCase** (np. `firstName`, `accessToken`). Nigdy
nie zwracamy w odpowiedzi hasła ani jego skrótu.

---

## 1. Uruchomienie środowiska

Pełen stos (Postgres + backend + frontend) startuje jednym poleceniem z głównego
katalogu repozytorium:

```bash
cp .env.example .env          # ustaw JWT_SECRET na własną wartość
docker compose up --build
```

Po starcie:

| Komponent  | URL                            |
|------------|--------------------------------|
| Backend    | <http://localhost:8000>        |
| Swagger UI | <http://localhost:8000/docs>   |
| Frontend   | <http://localhost:5173>        |
| Postgres   | `localhost:5432` (`pzio/pzio`) |

Pierwsze konto zarejestrowane przez `POST /api/auth/register` jest automatycznie
promowane do roli `Administrator` (zob. `backend/pzio/modules/auth/service.create_user`).

---

## 2. Uwierzytelnianie

PZIO używa JWT z nagłówkiem `Authorization: Bearer <token>`.

### Tradycyjny flow (e-mail + hasło)

```bash
# 1) Rejestracja
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "correct-horse-battery-staple",
    "firstName": "Alice",
    "lastName": "Smith"
  }'
# 201 Created → obiekt User (bez password / passwordHash)

# 2) Logowanie — token JWT
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"correct-horse-battery-staple"}' \
  | jq -r .accessToken)

# 3) Wywołanie chronionego endpointu
curl http://localhost:8000/api/users/me -H "Authorization: Bearer $TOKEN"
```

Token zawiera w JWT claims `sub` (`userId`) oraz `role` (`TeamMember`, `Manager`
lub `Administrator`). Domyślny czas życia: **60 minut** (`JWT_EXPIRES_MIN`).

### OAuth (Google / GitHub)

Frontend wymienia kod autoryzacyjny u dostawcy na `oauthToken`, następnie:

```bash
curl -X POST http://localhost:8000/api/auth/oauth \
  -H "Content-Type: application/json" \
  -d '{"provider":"google","oauthToken":"ya29.A0AfH6SMB..."}'
```

W odpowiedzi przychodzi taki sam `TokenResponse` jak w logowaniu klasycznym.

### Reset hasła

1. `POST /api/auth/reset-password` z `{"email": "..."}` — generuje token i
   wysyła link e-mailem (SMTP / w trybie dev: zapisuje w pamięci).
2. `POST /api/auth/reset-password/confirm` z `{"token": "...", "newPassword": "..."}`.

Endpoint resetu **zawsze** zwraca 200 — nie ujawniamy, czy konto istnieje.

---

## 3. Konwencje API

### Format błędów

Każda odpowiedź `4xx` (Pydantic 422, biznesowe 400/401/403/404/409) ma
ujednoliconą postać:

```json
{ "detail": "Invalid email or password" }
```

Walidacja Pydantic jest spłaszczana z listy błędów do jednej linii, np.
`email: value is not a valid email address; password: ensure this value has at least 8 characters`.

### Kody statusu

| Kod   | Znaczenie                                                                |
|-------|--------------------------------------------------------------------------|
| `200` | OK — żądanie odczytu / aktualizacji powiodło się.                        |
| `201` | Created — zasób utworzony, body zawiera utworzony obiekt.                |
| `204` | No Content — operacja kasująca, brak body.                               |
| `400` | Błąd walidacji lub niespójności biznesowej (np. `endDate <= startDate`). |
| `401` | Brak / nieważny / wygasły JWT.                                           |
| `403` | Brak uprawnień (np. nie-admin na endpointzie admina).                    |
| `404` | Zasób nie istnieje (lub caller nie ma do niego dostępu — celowe).        |
| `409` | Konflikt (np. duplikat e-maila przy rejestracji).                        |
| `422` | Walidacja Pydantic typu pola (rzadziej, zwykle dostajesz 400).           |

### Daty i czas

Wszystkie pola czasu używają **ISO 8601 z UTC** (`Z`), np.
`2026-05-14T13:15:00Z`. Daty w ciele żądania też akceptujemy w tym formacie.

### Paginacja

Endpointy listujące używają wspólnej obwoluty:

```json
{
  "items": [ ... ],
  "total": 137,
  "page": 1,
  "size": 20
}
```

Sterowanie:

- `page` (domyślnie `1`, ≥ 1)
- `size` (domyślnie `20`, zakres `1..100`)
- gdzie dostępne: `search`, `sortBy`, `sortDirection` (`asc`/`desc`).

---

## 4. Przegląd endpointów

Pełne szczegóły każdego endpointu znajdują się w `openapi.yaml` i Swagger UI.
Poniższa tabela jest mapą orientacyjną.

### Auth & użytkownicy

| Metoda | Ścieżka                              | Rola wywołującego          |
|--------|--------------------------------------|----------------------------|
| POST   | `/api/auth/register`                 | publiczna                  |
| POST   | `/api/auth/login`                    | publiczna                  |
| POST   | `/api/auth/oauth`                    | publiczna                  |
| POST   | `/api/auth/reset-password`           | publiczna                  |
| POST   | `/api/auth/reset-password/confirm`   | publiczna                  |
| GET    | `/api/users/me`                      | zalogowany użytkownik      |
| PATCH  | `/api/users/me`                      | zalogowany użytkownik      |
| PATCH  | `/api/users/me/email`                | zalogowany użytkownik      |
| POST   | `/api/users/me/change-password`      | zalogowany użytkownik      |
| DELETE | `/api/users/me`                      | zalogowany użytkownik      |
| GET    | `/api/users`                         | `Administrator`            |
| PATCH  | `/api/users/{id}/status`             | `Administrator`            |
| PATCH  | `/api/users/{id}/role`               | `Administrator`            |

### Projekty i członkowie

| Metoda | Ścieżka                                              | Rola wymagana                         |
|--------|------------------------------------------------------|---------------------------------------|
| POST   | `/api/projects`                                      | zalogowany                            |
| GET    | `/api/projects`                                      | zalogowany                            |
| GET    | `/api/projects/{id}`                                 | członek projektu                      |
| PATCH  | `/api/projects/{id}`                                 | członek projektu                      |
| DELETE | `/api/projects/{id}`                                 | członek projektu                      |
| POST   | `/api/projects/{id}/members`                         | `project_owner` lub `scrum_master`    |
| GET    | `/api/projects/{id}/members`                         | członek projektu                      |
| PATCH  | `/api/projects/{id}/members/{user_id}`               | `project_owner` lub `scrum_master`    |
| DELETE | `/api/projects/{id}/members/{user_id}`               | `project_owner` lub `scrum_master`    |

### Sprinty i burndown

| Metoda | Ścieżka                              | Rola wymagana       |
|--------|--------------------------------------|---------------------|
| POST   | `/api/projects/{id}/sprints`         | członek projektu    |
| GET    | `/api/projects/{id}/sprints`         | członek projektu    |
| PATCH  | `/api/sprints/{id}`                  | członek projektu    |
| DELETE | `/api/sprints/{id}`                  | członek projektu    |
| GET    | `/api/sprints/{id}/burndown`         | członek projektu    |

### Zadania (Backlog & Kanban)

| Metoda | Ścieżka                              | Rola wymagana       |
|--------|--------------------------------------|---------------------|
| POST   | `/api/projects/{id}/tasks`           | członek projektu    |
| GET    | `/api/projects/{id}/tasks`           | członek projektu    |
| GET    | `/api/tasks/{id}`                    | członek projektu    |
| PATCH  | `/api/tasks/{id}`                    | członek projektu    |
| DELETE | `/api/tasks/{id}`                    | członek projektu    |
| PATCH  | `/api/tasks/{id}/status`             | członek projektu    |
| POST   | `/api/tasks/{id}/worklogs`           | członek projektu    |
| GET    | `/api/tasks/{id}/worklogs`           | członek projektu    |
| GET    | `/api/tasks/{id}/history`            | członek projektu    |

### Komunikacja (komentarze + załączniki)

| Metoda | Ścieżka                                              | Rola wymagana            |
|--------|------------------------------------------------------|--------------------------|
| POST   | `/api/tasks/{task_id}/comments`                      | członek projektu         |
| GET    | `/api/tasks/{task_id}/comments`                      | członek projektu         |
| PATCH  | `/api/comments/{comment_id}`                         | autor komentarza         |
| DELETE | `/api/comments/{comment_id}`                         | autor lub admin          |
| POST   | `/api/tasks/{task_id}/attachments`                   | członek projektu         |
| GET    | `/api/tasks/{task_id}/attachments`                   | członek projektu         |
| GET    | `/api/attachments/{attachment_id}/download`          | członek projektu         |
| DELETE | `/api/attachments/{attachment_id}`                   | uploader lub admin       |

### Administracja

| Metoda | Ścieżka                       | Rola wymagana    |
|--------|-------------------------------|------------------|
| GET    | `/api/task-types`             | zalogowany       |
| POST   | `/api/admin/task-types`       | `Administrator`  |
| DELETE | `/api/admin/task-types/{id}`  | `Administrator`  |
| POST   | `/api/admin/backups`          | `Administrator`  |

---

## 5. Przykłady end-to-end

### Utworzenie projektu i sprintu

```bash
# Załóż, że TOKEN trzymasz w zmiennej środowiskowej (patrz §2).

# 1) Stwórz projekt
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Apollo Migration","description":"Migrate legacy billing."}'

# 2) Stwórz sprint
curl -X POST http://localhost:8000/api/projects/7/sprints \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name":"Sprint 1",
    "startDate":"2026-05-15T00:00:00Z",
    "endDate":"2026-05-29T00:00:00Z",
    "goal":"Ship auth flow"
  }'

# 3) Rozpocznij sprint
curl -X PATCH http://localhost:8000/api/sprints/21 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"active"}'
```

### Utworzenie zadania i ruch po tablicy Kanban

```bash
# 1) Dodaj typ zadania (jeżeli słownik jest pusty)
curl -X POST http://localhost:8000/api/admin/task-types \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Task"}'

# 2) Utwórz zadanie
curl -X POST http://localhost:8000/api/projects/7/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title":"Implement OAuth callback handler",
    "type":"Task",
    "priority":"High",
    "status":"ToDo",
    "storyPoints":5,
    "assigneeId":42,
    "sprintId":21
  }'

# 3) Przesuń zadanie na tablicy Kanban
curl -X PATCH http://localhost:8000/api/tasks/123/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"InProgress"}'

# 4) Sprawdź historię zmian (activity log)
curl http://localhost:8000/api/tasks/123/history \
  -H "Authorization: Bearer $TOKEN"
```

### Komentarz pod zadaniem

```bash
curl -X POST http://localhost:8000/api/tasks/123/comments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content":"Pushed the fix to the feature branch — please review."}'
```

Backend wysyła e-mail do przypisanego wykonawcy (w trybie dev: mock z pamięcią,
patrz `pzio/modules/communication/email_service.py`).

### Admin: blokada konta

```bash
# 1) Wyszukaj konto
curl "http://localhost:8000/api/users?search=alice" \
  -H "Authorization: Bearer $TOKEN"

# 2) Dezaktywuj
curl -X PATCH http://localhost:8000/api/users/42/status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"isActive":false}'
```

Zablokowany użytkownik dostaje `401 Unauthorized` z komunikatem `Invalid email
or password` przy próbie logowania.

Administrator nie może zmienić statusu własnego konta — każda taka próba
(dowolne `isActive` na własnym `id`) kończy się `403 Forbidden`. Chroni to
przede wszystkim przed zablokowaniem sobie dostępu do systemu, a blokada
obejmuje też aktywację jako dodatkowa linia obrony.

---

## 6. Słowniki wartości enum

### `UserRole` (auth)

`TeamMember`, `Manager`, `Administrator`

### `ProjectRole` (przypisanie do projektu)

`project_owner`, `scrum_master`, `developer`, `qa_engineer`

### `ProjectStatus`

`active`, `archived`

### `SprintStatus`

`planned`, `active`, `completed`

### `TaskStatus` (Kanban)

`ToDo`, `InProgress`, `Done`

### `TaskPriority`

`Low`, `Medium`, `High`

### `TaskType`

Słownik konfigurowalny przez admina. Domyślnie zawiera `Bug`; typowo dodaje się
`Task` i `Epic` przez `POST /api/admin/task-types`.

---

## 7. Regeneracja `openapi.yaml`

Plik [`openapi.yaml`](./openapi.yaml) jest generowany przez skrypt
`backend/scripts/dump_openapi.py`. Aby odświeżyć go po zmianach w API:

```bash
# Wariant dockerowy (zalecany)
docker compose exec backend python -m scripts.dump_openapi \
  > docs/api/openapi.yaml

# Wariant lokalny (wymaga zainstalowanych zależności backendu)
python backend/scripts/dump_openapi.py --out docs/api/openapi.yaml
```

---

## 8. Kontakt

Repozytorium: [`PZIO-2026`](https://github.com/PZIO-2026). W razie pytań do
kontraktu API stworzyć issue z labelem `api` albo zapytać Tech Leada modułu, do
którego należy endpoint (mapowanie modułów: `backend/pzio/modules/<name>/`).
