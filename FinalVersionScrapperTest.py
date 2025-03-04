from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import csv
import re
import time

# Ustawienie przeglądarki
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)

# Przygotuj dane globalne
results = []
processed_dept_ids = set()

# Funkcja do pobierania harmonogramu dla nauczyciela
def get_schedule(url, faculty_name):
    driver.get(url)
    time.sleep(0.5)  # Poczekaj na załadowanie strony
    
    # Pobranie wszystkich divów z klasą 'title'
    title_divs = driver.find_elements(By.CLASS_NAME, "title")
    full_title = title_divs[-1].text if title_divs else "Nie znaleziono prowadzącego"
    
    # Ekstrakcja imienia i nazwiska prowadzącego
    lecturer_match = re.search(r'Plan zajęć - (.*?), tydzień', full_title)
    lecturer = lecturer_match.group(1) if lecturer_match else "Nie znaleziono prowadzącego"
    
    # Sprawdź, czy istnieje legenda
    legend_exists = driver.find_elements(By.ID, "legend")
    if not legend_exists:
        print(f"    Brak legendy w planie dla {lecturer}. Pomijam.")
        return lecturer, {}
    
    # Pobranie legendy
    legend_data = driver.find_element(By.ID, "legend").get_attribute("innerHTML")
    legend_matches = re.findall(r'<strong>([\w\s()/]+)</strong>\s*(?:\([^)]*\))?\s*-\s*(.*?),', legend_data)
    legend_dict = {abbr.strip(): full_name.strip() for abbr, full_name in legend_matches}
    
    # Pobranie zajęć
    courses = driver.find_elements(By.CSS_SELECTOR, "div[id^='course_']")
    schedule = {}
    
    for course in courses:
        course_text = course.get_attribute("innerHTML")
        
        # Pobranie nazwy przedmiotu (skrótu)
        subject_match = re.search(r'>([\w()\/]+),\s*(\w+)<br>', course_text)
        subject_abbr = subject_match.group(1).strip() if subject_match else "Brak danych"
        course_type = subject_match.group(2).strip() if subject_match else "Brak danych"
        
        # Pobranie pełnej nazwy przedmiotu z legendy
        full_subject_name = legend_dict.get(subject_abbr, subject_abbr)
        
        # Pobranie kierunku
        kierunek_match = re.search(r'<a href=.*?>([\w\sŚśŻżŹźĆćŃńÓóŁłĄąĘę]+?)/', course_text)
        kierunek = kierunek_match.group(1).strip() if kierunek_match else "Brak danych"
        
        if kierunek not in schedule:
            schedule[kierunek] = set()
        schedule[kierunek].add((full_subject_name, course_type))
    
    # Dodaj dane do globalnych wyników z wydziałem jako pierwsza kolumna, pomijając "Brak danych"
    for kierunek, subjects in schedule.items():
        for full_subject_name, course_type in subjects:
            entry = {
                "Wydział": faculty_name,
                "Prowadzący": lecturer,
                "Nazwa przedmiotu": full_subject_name,
                "Typ zajęć": course_type,
                "Kierunek": kierunek
            }
            # Sprawdź, czy w którymkolwiek polu jest "Brak danych"
            if "Brak danych" not in entry.values():
                print(f"    Zapisuję wpis: {entry}")
                results.append(entry)
            else:
                print(f"    Pomijam wpis z 'Brak danych': {entry}")
    
    return lecturer, schedule

# Funkcja do przetwarzania katedry
def process_department(dept_id, faculty_name, faculty_id, branch_param):
    try:
        print(f"  Próba lokalizacji katedry: {dept_id}")
        plusik = wait.until(EC.presence_of_element_located((By.ID, f"img_{dept_id}")))
        driver.execute_script("arguments[0].scrollIntoView(true);", plusik)
        time.sleep(0.5)

        # Pobierz nazwę katedry (tylko dla logów)
        dept_name = f"Katedra {dept_id}"
        try:
            if faculty_id == "6179":
                dept_elem = plusik.find_element(By.XPATH, "./following-sibling::a")
                dept_name = dept_elem.text.strip()
                print(f"  Nazwa katedry (6179): {dept_name}")
            else:
                script = """
                var img = arguments[0];
                var li = img.parentNode;
                var div = li.querySelector('div[id="div_{0}"]');
                var text = '';
                for (var node of li.childNodes) {{
                    if (node.nodeType === 3 && node.textContent.trim() !== '' && 
                        node.previousSibling === img && (div === null || node.nextSibling === div)) {{
                        text = node.textContent.trim();
                        break;
                    }}
                }}
                return text;
                """.format(dept_id)
                dept_name = driver.execute_script(script, plusik) or dept_name
                print(f"  Nazwa katedry (pozostałe): {dept_name}")
        except Exception as e:
            print(f"  Nie udało się znaleźć nazwy katedry: {e}")

        # Rozwiń katedrę, jeśli nie jest rozwinięta
        if "plus.gif" in plusik.get_attribute("src"):
            print(f"  Rozwijam katedrę {dept_id}...")
            try:
                if faculty_id in ["6168", "6171", "6170", "6178", "6169"]:
                    ActionChains(driver).move_to_element(plusik).click(plusik).perform()
                else:
                    plusik.click()
                time.sleep(1)
            except Exception as e:
                print(f"  Kliknięcie nie powiodło się: {e}. Próbuję execute_script...")
                driver.execute_script(f"get_left_tree_branch('{dept_id}', 'img_{dept_id}', 'div_{dept_id}', '2', '{branch_param}');")
                time.sleep(0.5)

        div_dept = wait.until(EC.visibility_of_element_located((By.ID, f"div_{dept_id}")))
        coordinator_links = div_dept.find_elements(By.XPATH, ".//a[@href[contains(., 'type=10')]]")
        coordinators = [(link.text.strip(), link.get_attribute("href")) for link in coordinator_links]
        print(f"  Znaleziono {len(coordinators)} nauczycieli w {dept_name}.")

        for coordinator_name, coordinator_url in coordinators:
            print(f"    Przechodzę do nauczyciela: {coordinator_name}")
            get_schedule(coordinator_url, faculty_name)
            driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
            wait.until(EC.presence_of_element_located((By.ID, faculty_id)))
            driver.execute_script(f"branch(2,{faculty_id},0,'{faculty_name}');")
            time.sleep(0.5)

        processed_dept_ids.add(dept_id)
        print(f"  Katedra {dept_name} zakończona.")

    except Exception as e:
        print(f"  Błąd przy przetwarzaniu katedry (ID: {dept_id}): {e}")
        processed_dept_ids.add(dept_id)

# Funkcja do przetwarzania wydziału
def process_faculty(faculty_id, faculty_name, branch_param, dept_ids):
    print(f"Przetwarzam wydział: {faculty_name}")
    try:
        driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
        wait.until(EC.presence_of_element_located((By.ID, faculty_id)))
        driver.execute_script(f"branch(2,{faculty_id},0,'{faculty_name}');")
        print(f"Rozwinięto {faculty_name}!")
        time.sleep(0.5)

        for dept_id in dept_ids:
            if dept_id not in processed_dept_ids:
                print(f"Rozpoczynam przetwarzanie katedry {dept_id}...")
                process_department(dept_id, faculty_name, faculty_id, branch_param)
                print(f"Zakończono przetwarzanie katedry {dept_id}.")
                driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
                wait.until(EC.presence_of_element_located((By.ID, faculty_id)))
                driver.execute_script(f"branch(2,{faculty_id},0,'{faculty_name}');")
                time.sleep(0.5)

    except Exception as e:
        print(f"Błąd przy przetwarzaniu wydziału {faculty_name}: {e}")

# 1. Przejście do strony "Nauczyciele"
driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
print("Weszliśmy na stronę Nauczycieli!")

# Lista wydziałów do przetworzenia
faculties = [
    ("6179", "Jednostki Międzywydziałowe", "0", ["6196", "6197"]),
    ("6168", "Wydział Budowy Maszyn i Informatyki", "0", ["6180", "6174", "6175", "6176", "6181", "30847"]),
    ("6171", "Wydział Humanistyczno-Społeczny", "0", ["6193", "76335", "6192", "150120"]),
    ("6170", "Wydział Inżynierii Materiałów, Budownictwa i Środowiska", "0", ["150424"]),
    ("6178", "Wydział Nauk o Zdrowiu", "0", ["76336", "76337", "76338", "76339"]),
    ("6169", "Wydział Zarządzania i Transportu", "0", ["6184", "6185", "6188", "52698", "52699"])
]

# Przetwarzaj każdy wydział
for faculty_id, faculty_name, branch_param, dept_ids in faculties:
    process_faculty(faculty_id, faculty_name, branch_param, dept_ids)

# Zapisz do CSV
with open("scheduleDwa.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Wydział", "Prowadzący", "Nazwa przedmiotu", "Typ zajęć", "Kierunek"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

driver.quit()
print("Dane zapisane do schedule.csv!")