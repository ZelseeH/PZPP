# ScheduleScraper

## Table of Contents
* General Info
* Technologies
* Setup

## General Info
ScheduleScraper to aplikacja służąca do pobierania harmonogramów zajęć z planów uczelnianych, zapisywania ich do pliku CSV, a następnie wyświetlania w interfejsie użytkownika. Projekt składa się z trzech głównych komponentów: scrapera napisanego w Pythonie, backendu opartego na Flask oraz frontendu w React, umożliwiając użytkownikom łatwe przeglądanie harmonogramów.

## Technologies
Projekt został stworzony z użyciem następujących technologii:
* Python version: 3.8+
* Flask version: 2.3.2
* React version: 18.2.0
* Selenium version: 4.29.0
* Webdriver Manager version: 4.0.2
* Pandas version: 2.0.0+
* Axios version: 1.6.0+
* Node.js version: 16.0.0+

## Setup
Aby uruchomić ten projekt, postępuj zgodnie z poniższymi krokami:

### Scrapowanie harmonogramu
1. Otwórz terminal i przejdź do folderu Scraper:  
   `cd Scrapper`
2. Aktywuj środowisko wirtualne (jeśli nie istnieje, utwórz je za pomocą: `python -m venv venv`):  
   Windows: `venv\Scripts\activate`  
   Linux/macOS: `source venv/bin/activate`
3. Zainstaluj wymagane biblioteki (jeśli nie są jeszcze zainstalowane):  
   `pip install selenium webdriver-manager pandas`
4. Uruchom skrypt scrapujący:  
   `python Scraper_Main.py`

   Proces trwa około 30 minut, w zależności od liczby danych. Po zakończeniu w folderze Scraper pojawi się plik `schedule_all.csv`.
5. Przenieś plik `schedule_all.csv` do folderu backend.

### Uruchomienie backendu
1. Otwórz nowy terminal i przejdź do folderu backend:  
   `cd backend`
2. Aktywuj środowisko wirtualne (jeśli nie istnieje, utwórz je za pomocą: `python -m venv .venv`):  
   Windows: `.venv\Scripts\activate`  
   Linux/macOS: `source .venv/bin/activate`
3. Zainstaluj wymagane biblioteki (jeśli nie są jeszcze zainstalowane):  
   `pip install flask flask-cors pandas`
4. Uruchom aplikację Flask:  
   `python app.py`

   Backend będzie dostępny pod adresem `http://127.0.0.1:5000`.

### Uruchomienie frontendu
1. Otwórz nowy terminal i przejdź do folderu frontend:  
   `cd frontend`
2. Zainstaluj zależności (jeśli nie są jeszcze zainstalowane):  
   `npm install`
3. Zainstaluj axios, jeśli nie jest jeszcze zainstalowany:  
   `npm install axios`
4. Uruchom aplikację React:  
   `npm start`

   Frontend będzie dostępny pod adresem `http://localhost:3000`.

## Dodatkowe informacje
- Jeśli podczas uruchamiania scrapera Selenium wymaga pobrania sterownika przeglądarki, Webdriver Manager zrobi to automatycznie.
- Plik `schedule_all.csv` jest kluczowy dla działania backendu – upewnij się, że znajduje się w odpowiednim katalogu.
- Jeśli napotkasz problemy z uruchomieniem, sprawdź wersje wymaganych pakietów i upewnij się, że środowisko wirtualne jest aktywne.

