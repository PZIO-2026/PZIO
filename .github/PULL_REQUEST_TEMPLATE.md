## Zakres

<!-- Tutaj podaj skrótowy opis zmian w punktach -->

- 
- 
- 



## Zgodność

<!-- Dla SRS podaj, których Functional Requirements dotyczy ten PR -->
<!-- Dla SAD podaj, jakich modułów/endpointów dotyczy ten PR -->

- zgodne z SRS:
    - ...
- zgodne z SAD:
    - ...



## API

<!-- Tutaj podaj przykłady użycia dodanych/zmodyfikowanych endpointów -->



## Dodatkowe informacje

<!-- Tutaj umieść np. mniej ważne zmiany, dodane testy, wyjaśnienia decyzji implementacyjnych -->



## Checklista

<!-- Umieść x wewnątrz [ ], aby zaznaczyć: [x] -->

<details>
<summary>Kliknij, aby rozwinąć checklistę</summary>

---

1.  [ ] Zgodność z architekturą
    - Czy kod jest zgodny z architekturą (SAD)?
    - Czy moduł robi tylko to, za co odpowiada?
    - Czy nie ma "skrótów/obejść" omijających architekturę?
2.  [ ] Interfejsy
    - Czy API jest zgodne z ustalonym kontraktem?
    - Czy endpointy mają poprawne nazwy?
    - Czy dane wejściowe/wyjściowe są zgodne z dokumentacją?
    - Czy nie zmieniono API?
3.  [ ] Logika biznesowa
    - Czy kod robi to, co powinien?
    - Czy przypadki brzegowe są obsłużone?
    - Czy nie ma oczywistych błędów logicznych?
4.  [ ] Struktura kodu
    - Czy kod jest czytelny?
    - Czy funkcje nie są za długie?
    - Czy nie ma duplikacji kodu?
    - Czy podział na pliki/klasy ma sens?
5.  [ ] Nazewnictwo
    - Czy nazwy są zrozumiałe?
    - Czy są spójne w całym projekcie?
    - Czy uniknięto nazw typu `a`, `b`, `data`, `tmp`, `test123`?
6.  [ ] Testy
    - Czy są testy jednostkowe?
    - Czy testy pokrywają najważniejsze przypadki?
    - Czy testy są czytelne?
7.  [ ] Obsługa błędów
    - Czy błędy są obsługiwane?
    - Czy komunikaty błędów mają sens?
    - Czy system nie "pada" bez informacji?
8.  [ ] Bezpieczeństwo
    - Czy dane wejściowe są walidowane?
    - Czy nie ma oczywistych podatności (np. brak auth)?
    - Czy wrażliwe dane nie są hardcode'owane?
9.  [ ] Jakość techniczna
    - Czy kod się kompiluje / uruchamia?
    - Czy nie ma zbędnego kodu (dead code)?
    - Czy nie ma debug printów / `console.log`?
10. [ ] Dokumentacja
    - Czy API jest udokumentowane?
    - Czy trudne fragmenty mają komentarze?
    - Czy README jest aktualne?

</details>
