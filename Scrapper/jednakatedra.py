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
results_set = set()  # Zbiór do przechowywania unikalnych wpisów jako krotki
results = []  # Lista do przechowywania wyników w formacie słowników
processed_dept_ids = set()

# Funkcja do ustawienia konkretnego tygodnia
def set_week(week_id):
    try:
        week_select = driver.find_element(By.ID, "wBWeek")
        week_option = week_select.find_element(By.CSS_SELECTOR, f"option[value='{week_id}']")
        driver.execute_script("arguments[0].selected = true;", week_option)
        
        show_button = driver.find_element(By.ID, "wBButton")
        show_button.click()
        time.sleep(0.5)
        print(f"    Ustawiono tydzień: {week_id}")
    except Exception as e:
        print(f"    Nie udało się ustawić tygodnia {week_id}: {e}")

# Funkcja do normalizacji skrótów (usuwanie myślników)
def normalize_abbr(abbr):
    return abbr.replace("-", "")

# Funkcja do pobierania planu zajęć dla nauczyciela
def get_schedule(url, faculty_name):
    global results_set, results
    driver.get(url)
    time.sleep(0.5)
    
    lecturer = "Nie znaleziono prowadzącego"
    schedule = {}
    
    weeks = ["706", "707", "708"]
    
    try:
        for week_id in weeks:
            set_week(week_id)
            
            title_divs = driver.find_elements(By.CLASS_NAME, "title")
            full_title = title_divs[-1].text if title_divs else "Nie znaleziono prowadzącego"
            
            lecturer_match = re.search(r'Plan zajęć - (.*?), tydzień', full_title)
            lecturer = lecturer_match.group(1) if lecturer_match else "Nie znaleziono prowadzącego"
            
            legend_exists = driver.find_elements(By.ID, "legend")
            if not legend_exists:
                print(f"    Brak legendy w planie dla {lecturer} (tydzień {week_id}). Pomijam tydzień.")
                continue
            
            legend_data = driver.find_element(By.ID, "legend").get_attribute("innerHTML")
            legend_matches = re.findall(r'<strong>([\w\s()/]+)</strong>\s*(?:\([^)]*\))?\s*-\s*(.*?),', legend_data)
            # Normalizujemy klucze w legend_dict, usuwając myślniki
            legend_dict = {normalize_abbr(abbr.strip()): full_name.strip() for abbr, full_name in legend_matches}
            print(f"    Legenda dla {lecturer} (tydzień {week_id}): {legend_dict}")  # Debugowanie
            
            courses = driver.find_elements(By.CSS_SELECTOR, "div[id^='course_']")
            
            for course in courses:
                course_text = course.get_attribute("innerHTML")
                
                subject_match = re.search(r'>([\w()/|-]+),\s*(\w+)<br>', course_text)
                subject_abbr = subject_match.group(1).strip() if subject_match else "Brak danych"
                course_type = subject_match.group(2).strip() if subject_match else "Brak danych"
                
                # Normalizujemy skrót przed wyszukaniem w legendzie
                normalized_abbr = normalize_abbr(subject_abbr)
                full_subject_name = legend_dict.get(normalized_abbr, subject_abbr)
                print(f"    Skrót: {subject_abbr} -> Znormalizowany: {normalized_abbr} -> Pełna nazwa: {full_subject_name}")  # Debugowanie
                
                kierunek_match = re.search(r'<a href=.*?>([\w\sŚśŻżŹźĆćŃńÓóŁłĄąĘę]+?)/', course_text)
                kierunek = kierunek_match.group(1).strip() if kierunek_match else "Brak danych"
                
                study_mode_match = re.search(r'<a href=.*?>[\w\sŚśŻżŹźĆćŃńÓóŁłĄąĘę]+?/([\w]+)/', course_text)
                study_mode = study_mode_match.group(1).strip() if study_mode_match else "Brak danych"

                if kierunek not in schedule:
                    schedule[kierunek] = set()
                schedule[kierunek].add((full_subject_name, course_type, study_mode))
            
            for kierunek, subjects in schedule.items():
                for full_subject_name, course_type, study_mode in subjects:
                    entry_tuple = (faculty_name, lecturer, full_subject_name, course_type, kierunek, study_mode)
                    entry_dict = {
                        "Wydział": faculty_name,
                        "Prowadzący": lecturer,
                        "Nazwa przedmiotu": full_subject_name,
                        "Typ zajęć": course_type,
                        "Kierunek": kierunek,
                        "Studia": study_mode
                    }
                    if "Brak danych" not in entry_dict.values():
                        if entry_tuple not in results_set:
                            print(f"    Zapisuję unikalny wpis (tydzień {week_id}): {entry_dict}")
                            results_set.add(entry_tuple)
                            results.append(entry_dict)
                        else:
                            print(f"    Pomijam duplikat (tydzień {week_id}): {entry_dict}")
                    else:
                        print(f"    Pomijam wpis z 'Brak danych' (tydzień {week_id}): {entry_dict}")
    
    except Exception as e:
        print(f"    Błąd podczas przetwarzania planu dla {lecturer}: {e}")
    
    return lecturer, schedule

# Funkcja do przetwarzania katedry
def process_department(dept_id, faculty_name, faculty_id, branch_param):
    try:
        print(f"  Próba lokalizacji katedry: {dept_id}")
        plusik = wait.until(EC.presence_of_element_located((By.ID, f"img_{dept_id}")))
        driver.execute_script("arguments[0].scrollIntoView(true);", plusik)
        time.sleep(0.5)

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

        if "plus.gif" in plusik.get_attribute("src"):
            print(f"  Rozwijam katedrę {dept_id}...")
            try:
                if faculty_id in ["6168", "6171", "6170", "6178", "6169"]:
                    ActionChains(driver).move_to_element(plusik).click(plusik).perform()
                else:
                    plusik.click()
                time.sleep(0.5)
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
            try:
                lecturer, schedule = get_schedule(coordinator_url, faculty_name)
            except Exception as e:
                print(f"    Błąd przy przetwarzaniu nauczyciela {coordinator_name}: {e}")
                continue
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

# Lista wydziałów do przetworzenia - tylko Wydział Budowy Maszyn i Informatyki, Katedra Informatyki i Automatyki
faculties = [
    ("6168", "Wydział Budowy Maszyn i Informatyki", "0", ["30847"])
]

# Przetwarzaj wydział
for faculty_id, faculty_name, branch_param, dept_ids in faculties:
    process_faculty(faculty_id, faculty_name, branch_param, dept_ids)

# Zapisz do CSV
with open("schedule_informatyka_automatyka.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Wydział", "Prowadzący", "Nazwa przedmiotu", "Typ zajęć", "Kierunek", "Studia"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

driver.quit()
print("Dane zapisane do schedule_informatyka_automatyka.csv!")