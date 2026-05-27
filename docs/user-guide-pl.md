# PZIO - Podręcznik Użytkownika

## 1. Instalacja i konfiguracja

Aplikacja PZIO w architekturze backend+frontend tworzy powiązane usługi i bazę danych automatycznie w filozofii _zero configuration_.

Zestawienie środowiska można przeprowadzić na dwa sposoby:

### Sposób 1: Docker (Sposób zalecany)

Dzięki wykorzystaniu Docker Compose całe środowisko wraz z bazą PostgreSQL i serwerami zostaje uruchomione jedną komendą.

1. Skopiuj przykładowy plik konfiguracyjny (zawierający m.in. klucz JWT):
    ```bash
    cp .env.example .env
    ```
2. Zbuduj i uruchom stos kontenerów:
    ```bash
    docker compose up --build
    ```

Aplikacja będzie dostępna pod adresem: **http://localhost:5173**  
Dokumentacja API (Swagger) pod adresem: **http://localhost:8000/docs** lub w podfolderze repozytorium: `/docs/api`

> **Uwaga (Środowisko produkcyjne):** Wartość `JWT_SECRET` w skopiowanym pliku `.env` jest celowo testowa. Przed każdym wejściem na produkcję musisz nadpisać ten klucz długim i losowym ciągiem znaków. Backend odmówi startu, jeśli w ogóle go nie zdefiniujesz.

### Sposób 2: Uruchamianie klasyczne (komendy lokalne)

Aplikację można też uruchomić tradycyjnie, ręcznie instalując niezbędne komponenty oddzielnie dla backendu oraz frontendu.

**Backend:**

```bash
cd backend
cp .env.example .env
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python -m pzio
```

API wystartuje pod: `http://localhost:8000`.

**Frontend:**
Otwórz drugą zakładkę terminala i wykonaj:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

Domyślnie użyje on adresu `http://localhost:8000` dla backendu. Frontend ruszy pod adresem `http://localhost:5173`.

> _Użytkownicy Nix:_ W głównym roocie projektu znajduje się również plik `shell.nix`. Możesz skorzystać po prostu z komendy `nix-shell` z roota, aby szybko ustawić wyizolowane środowisko systemowe.

## 2. Baza danych i zasady środowiskowe

- **Pierwszy zarejestrowany użytkownik** uzyskuje automatycznie najwyższe uprawnienia: **Administrator**.
- **Każdy kolejny** staje się domyślnie **Team Memberem**.

_Uwaga deweloperska:_ Przypominanie haseł póki co używa komponentu `MockEmailService`. Aplikacja nie wysyła fizycznie e-maili, ale zapisuje requesty resetu w bazie danych.

## 3. Sposób użycia - Funkcjonalności

Poniżej znajdziesz zestawienie widoków we frontendzie.

### Logowanie (`/login`)

![Zrzut ekranu logowania](assets/login.png)

- Ta strona jest punktem startowym dla wszystkich użytkowników.
- Umożliwia uwierzytelnienie się za pomocą adresu e-mail i hasła.
- Po pomyślnym zalogowaniu następuje przekierowanie do strony głównej.
- Można też przejść do ekranu rejestracji lub zapomnianego hasła, jeśli nie masz jeszcze konta lub potrzebujesz zresetować hasło.
- Dostępna jest również opcja logowanie przez Google lub GitHub (OAuth2) - po kliknięciu następuje przekierowanie do odpowiedniego dostawcy, a po udanym uwierzytelnieniu następuje powrót do aplikacji z zalogowanym użytkownikiem. Oczywiście, aby skorzystać z tej funkcji, administrator musi wcześniej skonfigurować odpowiednie dane uwierzytelniające za pomocą zmiennych środowiskowych.

### Rejestracja (`/register`)

![Zrzut ekranu rejestracji](assets/register.png)

- Ta strona umożliwia tworzenie nowego konta w systemie.
- Użytkownik musi podać swój adres e-mail, dane osobowe, hasło oraz potwierdzenie hasła.
- Po pomyślnym zarejestrowaniu następuje przekierowanie do strony logowania, gdzie można się zalogować nowo utworzonym kontem.
- Dostępna jest także opcja powrotu do ekranu logowania oraz rejestracji przez OAuth2.

### Zapomniane hasło (`/forgot-password` i `/reset-password`)

![Zrzut ekranu widoku zapomnianego hasła](assets/forgot-password.png)

- Jest to prosty widok umożliwiający użytkownikom zainicjowanie procesu resetowania hasła poprzez podanie swojego adresu e-mail.
- Po wysłaniu formularza, docelowo ma być wysyłany e-mail z linkiem do resetowania hasła. W obecnej implementacji, ze względu na użycie `MockEmailService`, żaden e-mail nie jest faktycznie wysyłany.

### Strona główna (`/`)

![Zrzut ekranu strony głównej](assets/main-page.png)

- Ekran powitalny witający zalogowanego użytkownika.
- Dostęp nawigacyjny do reszty ekosystemu - głównie do listy projektów i zadań, a także do profilu użytkownika i panelu administratora (jeśli użytkownik ma odpowiednie uprawnienia).
- Aktualnie dość pusta, ale docelowo będzie zawierała różne widżety i skróty do najważniejszych funkcji.

### Projekty (`/projects`)

![Zrzut ekranu listy projektów](assets/projects.png)

- Wyświetlanie listy wszystkich projektów, do których użytkownik ma dostęp.
- Możliwość tworzenia nowych projektów przez użytkowników z rolą systemową Administratora lub Managera.
- Możliwość filtrowania i sortowania projektów według różnych kryteriów.

### Szczegóły projektu (`/projects/:id`)

Widok ten jest podzielony na wiele sekcji, które udokumentowano poniżej.

**Sekcja informacji o projekcie**:

![Zrzut ekranu sekcji informacji o projekcie](assets/project-details.png)

- Zawiera podstawowe informacje o projekcie, takie jak jego nazwa, opis i data utworzenia.
- Pozwala na edycję tych informacji przez użytkowników z odpowiednimi uprawnieniami.

**Sekcja członków projektu**:

![Zrzut ekranu sekcji członków projektu](assets/project-members.png)

- Wyświetla listę wszystkich członków projektu wraz z ich rolami.
- Umożliwia dodawanie nowych członków do projektu oraz zarządzanie ich rolami poprzez przycisk "Edytuj" obok każdego członka.
- Umożliwia usuwanie członków z projektu, jeśli użytkownik ma odpowiednie uprawnienia.
- Dostępne jest także wyszukiwanie członków oraz filtrowanie po rolach, a także paginacja.

**Sekcja sprintów**:

![Zrzut ekranu sekcji sprintów](assets/project-sprints.png)

- Pozwala na zarządzanie sprintami w ramach projektu, w tym tworzenie nowych sprintów, edycję istniejących oraz usuwanie sprintów.
- Każdy sprint ma swój opis oraz daty rozpoczęcia i zakończenia.
- Dostępny jest także przycisk "Burndown", służący do wizualizacji postępu sprintu w formie wykresu burndown.

**Sekcja zadań (backlog)**:

![Zrzut ekranu sekcji zadań (backlog)](assets/project-backlog.png)

- Ta sekcja zawiera listę wszystkich zadań w danym projekcie, które nie zostały jeszcze przypisane do sprintu.
- Umożliwia tworzenie nowych zadań, edycję istniejących oraz usuwanie zadań.
- Zadania można przypisywać do sprintów, klikając w przycisk "Przypisz".
- Wyświetlane są podstawowe informacje o zadaniu, takie jak jego tytuł, typ, priorytet oraz story points.

**Tablica zadań (kanban)**:

![Zrzut ekranu tablicy zadań (kanban)](assets/project-kanban.png)

- Tablica zadań w stylu kanban, podzielona na kolumny reprezentujące różne statusy zadań ("Do zrobienia", "W trakcie", "Ukończone").
- Umożliwia przeciąganie i upuszczanie zadań między kolumnami, co automatycznie aktualizuje ich status.
- Wyświetlane są również informacje o sprincie, dla którego widoczna jest aktualnie tablica.
- Kliknięcie na zadanie przenosi do jego szczegółowego widoku, gdzie można zobaczyć więcej informacji oraz edytować zadanie.

### Zadania (`/tasks`)

![Zrzut ekranu listy zadań](assets/tasks.png)

- Jest to widok zbiorczy, który wyświetla wszystkie zadania, do których użytkownik ma dostęp, niezależnie od projektu.
- Umożliwia filtrowanie zadań według statusu i priorytetu oraz wyszukiwanie zadań po tytule.
- Kliknięcie na zadanie przenosi do jego szczegółowego widoku.

### Szczegóły zadania (`/tasks/:id`)

![Zrzut ekranu szczegółów zadania (część 1)](assets/task-details-1.png)
![Zrzut ekranu szczegółów zadania (część 2)](assets/task-details-2.png)

- Wyświetla wszystkie informacje o zadaniu, takie jak: tytuł, opis, typ, priorytet, story points, status, przypisany sprint, identyfikator wewnętrzny oraz zadanie nadrzędne.
- Umożliwia edycję tych informacji przez użytkowników z odpowiednimi uprawnieniami.
- Pozwala na dodawanie komentarzy do zadania, co jest szczególnie przydatne do komunikacji między członkami zespołu.
- Dostępna jest również dedykowana sekcja na załączniki, gdzie można dodawać i przeglądać pliki powiązane z zadaniem. Zdjęcia dodane jako załączniki są wyświetlane bezpośrednio w tej sekcji, co ułatwia ich przeglądanie.

### Profil Użytkownika (`/profile`)

![Zrzut ekranu strony profilu użytkownika](assets/profile.png)

- Wyświetlanie aktualnych informacji na swój temat.
- Możliwość edycji danych osobowych, takich jak imię, nazwisko i adres URL awatara.

### Panel Administratora (`/admin`)

![Zrzut ekranu panelu administratora (część 1)](assets/admin-1.png)
![Zrzut ekranu panelu administratora (część 2)](assets/admin-2.png)

- Panel dedykowany do zarządzania kontami użytkowników, backupami bazy danych i innymi funkcjami administracyjnymi.
- Dostęp do tego panelu mają tylko użytkownicy z rolą Administratora.
- Pierwsza sekcja umożliwia przeglądanie listy wszystkich zarejestrowanych użytkowników, wraz z ich rolami i możliwością edycji tychże ról.
- Druga sekcja pozwala na rozszerzanie dostępnych typów zadań projektowych o nowe definicje, a także usuwanie istniejących typów zadań, o ile nie jest to ostatni pozostały typ.
- Trzecia sekcja służy do wymuszania stworzenia kopii zapasowej bazy danych.
- Czwarta sekcja pozwala na przeglądanie logów powiązanych z konkretnym zadaniem projektowym, co jest szczególnie przydatne do celów debugowania i monitorowania.
