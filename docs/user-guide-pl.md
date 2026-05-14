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

[ TUTAJ UMIEŚĆ ZRZUT EKRANU STRONY GŁÓWNEJ ]

- Ekran powitalny witający zalogowanego użytkownika
- Dostęp nawigacyjny do reszty ekosystemu (Navbar i Outlet)
- [... uzupełnij: inne funkcje dla tego widoku ...]

### Profil Użytkownika (`/profile`)

[ TUTAJ UMIEŚĆ ZRZUT EKRANU EKRANU PROFILU ]

- Wyświetlanie aktualnych informacji na swój temat (GET `me`)
- Formularz edycji i aktualizacji wybranych danych przypisanych do Twojego konta
- [... uzupełnij: inne funkcje dla tego widoku ...]

### Panel Administratora (`/admin`)

[ TUTAJ UMIEŚĆ ZRZUT EKRANU PANELU ZARZĄDZANIA (ADMIN) ]

- Panel dedykowany do zarządzania kontami w przestrzeni (Users) przestrzeni
- Umożliwia zmianę ról innym kontom pomiędzy `TeamMember`, `Manager` oraz `Administrator` (zabezpieczenie uniemożliwiające zmianę ról samemu sobie).
- [... uzupełnij: inne funkcje dla tego widoku ...]
