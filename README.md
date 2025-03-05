ScheduleScraper
ScheduleScraper to aplikacja służąca do pobierania harmonogramów zajęć z planów uczelnianych, zapisywania ich do pliku CSV, a następnie wyświetlania ich w interfejsie użytkownika za pomocą backendu Flask i frontendu React.

Struktura projektu
ScheduleScraper/

├── Scraper/ - Folder ze skryptem scrapującym

│   ├── Scraper_Main.py - Główny skrypt scrapujący

│   ├── venv/ - Środowisko wirtualne dla scrapera

│   └── schedule_all.csv - Wyjściowy plik CSV (po scrapowaniu)

├── backend/ - Folder z backendem Flask

│   ├── app.py - Główny plik backendu

│   ├── .venv/ - Środowisko wirtualne dla backendu

│   └── schedule_all.csv - Plik CSV przeniesiony po scrapowaniu

├── frontend/ - Folder z frontendem React

│   ├── src/

│   │   ├── App.js - Główny komponent React

│   │   └── App.css - Style CSS

│   ├── package.json - Konfiguracja npm

│   └── node_modules/ - Biblioteki frontendowe

└── README.md - Ten plik

Wymagania
Python 3.8+ (dla scrapera i backendu)
Node.js i npm (dla frontendu)
Plik schedule_all.csv (generowany przez scraper)
Instalacja i uruchomienie
Scrapowanie harmonogramu
Najpierw pobieramy dane z planu zajęć i zapisujemy je do pliku CSV.

Krok 1: Przejście do folderu Scraper
Otwórz terminal i przejdź do folderu Scraper: cd Scraper

Krok 2: Aktywacja środowiska wirtualnego
Aktywuj środowisko wirtualne (jeśli nie istnieje, utwórz je za pomocą: python -m venv venv): venv\Scripts\activate

Krok 3: Instalacja bibliotek
Zainstaluj wymagane biblioteki (jeśli nie są jeszcze zainstalowane): pip install selenium webdriver-manager pandas

Krok 4: Uruchomienie skryptu scrapującego
Uruchom skrypt scrapujący: python Scraper_Main.py

Proces trwa około 30 minut, w zależności od liczby danych. Po zakończeniu w folderze Scraper pojawi się plik schedule_all.csv.

Krok 5: Przeniesienie pliku CSV
Przenieś plik schedule_all.csv do folderu backend.

Uruchomienie backendu
Backend Flask obsługuje API dla frontendu.

Krok 1: Przejście do folderu backend
Otwórz nowy terminal i przejdź do folderu backend: cd backend

Krok 2: Aktywacja środowiska wirtualnego
Aktywuj środowisko wirtualne (jeśli nie istnieje, utwórz je za pomocą: python -m venv .venv): .venv\Scripts\activate

Krok 3: Instalacja bibliotek
Zainstaluj wymagane biblioteki (jeśli nie są jeszcze zainstalowane): pip install flask flask-cors pandas

Krok 4: Uruchomienie aplikacji Flask
Uruchom aplikację Flask: python app.py

Backend będzie dostępny pod adresem http://127.0.0.1:5000.

Uruchomienie frontendu
Frontend React wyświetla interfejs użytkownika do przeglądania harmonogramu.

Krok 1: Przejście do folderu frontend
Otwórz nowy terminal i przejdź do folderu frontend: cd frontend

Krok 2: Instalacja zależności
Zainstaluj zależności (jeśli nie są jeszcze zainstalowane): npm install

Zainstaluj axios, jeśli nie jest jeszcze zainstalowany: npm install axios

Krok 3: Uruchomienie aplikacji React
Uruchom aplikację React: npm start

Frontend uruchomi się pod adresem http://localhost:3000 i połączy się z backendem.

Użycie
Po uruchomieniu wszystkich komponentów otwórz przeglądarkę na http://localhost:3000.

Wybierz wydział, kierunek, przedmiot i typ studiów w formularzu.

Kliknij "Szukaj", aby wyświetlić harmonogram zajęć.

Wymagania systemowe
Scraper: Python 3.8+, Chrome (dla Selenium WebDriver)
Backend: Python 3.8+, Flask
Frontend: Node.js 16+, npm
Uwagi
Upewnij się, że plik schedule_all.csv jest poprawnie wygenerowany i przeniesiony do folderu backend przed uruchomieniem backendu.

Jeśli scraper działa wolno, sprawdź połączenie internetowe lub dostosuj opóźnienia (time.sleep) w Scraper_Main.py.

Autor
[Twoje imię lub pseudonim]