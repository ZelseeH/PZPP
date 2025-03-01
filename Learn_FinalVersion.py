from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
import json
import re
import time

# Ustawienie przeglądarki
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)

# 1. Przejście do strony "Nauczyciele"
driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
print("Weszliśmy na stronę Nauczycieli!")

# 2. Przygotuj dane
results = []
processed_dept_ids = set()

# Mapowanie typu przedmiotu
type_mapping = {
    "lek": "lektorat",
    "wyk": "wykład",
    "ćw": "ćwiczenia",
    "proj": "projektowanie",
    "lab": "laboratorium",
    "wf": "ćwiczenia",
    "wr": "warsztaty",
    "konw": "konwersatorium",
    "sem": "seminarium",
    "pnj": "Praktyczna Nauka Języka"
}

# Funkcja do określenia typu przedmiotu z tekstu diva
def get_subject_type(div_text):
    match = re.search(r'<img[^>]*id="arrow_course_\d+"[^>]*>(.*?)<br>', div_text, re.DOTALL)
    if match:
        text = match.group(1).strip()
        print(f"    Wyodrębniony tekst typu: {text}")
        for key, value in type_mapping.items():
            if key in text.lower():
                return value
    return "nieznany"

# Funkcja do sprawdzania, czy wpis już istnieje
def entry_exists(faculty, dept, coord, subj, subj_type):
    return any(
        entry["Wydział"] == faculty and
        entry["Katedra"] == dept and
        entry["Koordynator"] == coord and
        entry["Przedmiot"] == subj and
        entry["Typ"] == subj_type
        for entry in results
    )

# Funkcja do przetwarzania katedry
def process_department(dept_id, faculty_name, faculty_id, branch_param):
    try:
        print(f"  Próba lokalizacji katedry: {dept_id}")
        plusik = wait.until(EC.presence_of_element_located((By.ID, f"img_{dept_id}")))
        print(f"  Znaleziono element img_{dept_id} w DOM-ie.")
        driver.execute_script("arguments[0].scrollIntoView(true);", plusik)
        time.sleep(0.5)
        print(f"  Stan plusika: src={plusik.get_attribute('src')}, visible={plusik.is_displayed()}")

        # Pobierz nazwę katedry
        dept_name = f"Katedra {dept_id}"  # Domyślna wartość
        try:
            if faculty_id == "6179":
                parent_html = plusik.find_element(By.XPATH, "./parent::*").get_attribute("innerHTML")
                print(f"  HTML rodzica plusika (6179): {parent_html}")
                dept_elem = plusik.find_element(By.XPATH, "./following-sibling::a")
                dept_name = dept_elem.text.strip()
                print(f"  Nazwa katedry (6179, ./following-sibling::a): {dept_name}")
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
                dept_name = driver.execute_script(script, plusik)
                if not dept_name:
                    raise Exception("Brak tekstu między <img> a <div>")
                print(f"  Nazwa katedry (pozostałe, JS): {dept_name}")
        except Exception as e:
            print(f"  Nie udało się znaleźć nazwy katedry: {e}. Używam domyślnej nazwy: {dept_name}")
        print(f"  Potwierdzenie dept_name przed rozwinięciem: {dept_name}")

        # Rozwiń katedrę, jeśli nie jest rozwinięta
        if "plus.gif" in plusik.get_attribute("src"):
            print(f"  Rozwijam katedrę {dept_id}...")
            try:
                if faculty_id in ["6168", "6171", "6170", "6178", "6169"]:
                    ActionChains(driver).move_to_element(plusik).click(plusik).perform()
                    print("  Użyto ActionChains do kliknięcia.")
                else:
                    plusik.click()
                    print("  Użyto zwykłego click() do kliknięcia.")
                time.sleep(1)
            except Exception as e:
                print(f"  Kliknięcie nie powiodło się: {e}. Próbuję execute_script...")
                driver.execute_script(f"get_left_tree_branch('{dept_id}', 'img_{dept_id}', 'div_{dept_id}', '2', '{branch_param}');")
                time.sleep(0.5)

        # Sprawdź, czy div katedry jest widoczny
        div_dept = wait.until(EC.visibility_of_element_located((By.ID, f"div_{dept_id}")))
        print(f"  Div katedry {dept_id} załadowany i widoczny.")

        # Zbierz nauczycieli
        coordinator_links = div_dept.find_elements(By.XPATH, ".//a[@href[contains(., 'type=10')]]")
        coordinators = [(link.text.strip(), link.get_attribute("href")) for link in coordinator_links]
        print(f"  Znaleziono {len(coordinators)} nauczycieli w {dept_name}.")

        # Przetwarzaj nauczycieli
        for coordinator_name, coordinator_url in coordinators:
            print(f"    Przechodzę do nauczyciela: {coordinator_name}")
            driver.get(coordinator_url)
            time.sleep(0.5)

            # Sprawdź, czy istnieje legenda
            legend_exists = driver.find_elements(By.ID, "legend")
            if not legend_exists:
                print(f"    Brak legendy w planie dla {coordinator_name}. Pomijam.")
                continue

            try:
                legend = wait.until(EC.presence_of_element_located((By.ID, "legend")))
                data_div = legend.find_element(By.CLASS_NAME, "data")
                legend_text = data_div.get_attribute("innerHTML")
                print(f"    Legend text: {legend_text}")

                # Parsuj przedmioty z legendy
                subject_pattern = r"<strong>(.*?)</strong> - (.*?)(?:, występowanie|\s*<br|\s*<hr)"
                subjects = list(re.finditer(subject_pattern, legend_text))

                # Znajdź wszystkie divy course_x na stronie
                course_divs = driver.find_elements(By.XPATH, "//div[starts-with(@id, 'course_')]")
                print(f"    Znaleziono {len(course_divs)} divów course_x")

                # Przetwarzaj przedmioty z legendy
                if subjects:
                    for match in subjects:
                        subject_code = match.group(1)
                        subject_name = match.group(2).strip()
                        for div in course_divs:
                            div_text = div.get_attribute("innerHTML")
                            if subject_code in div_text:
                                subject_type = get_subject_type(div_text)
                                if not entry_exists(faculty_name, dept_name, coordinator_name, subject_name, subject_type):
                                    entry = {
                                        "Wydział": faculty_name,
                                        "Katedra": dept_name,
                                        "Koordynator": coordinator_name,
                                        "Przedmiot": subject_name,
                                        "Typ": subject_type
                                    }
                                    print(f"    Zapisuję wpis: {entry}")
                                    results.append(entry)
                else:
                    for div in course_divs:
                        div_text = div.get_attribute("innerHTML")
                        print(f"    Div text dla course_x: {div_text}")
                        subject_code = div_text.split("<br>")[0].strip()
                        subject_name = "Brak szczegółów"
                        subject_type = get_subject_type(div_text)
                        if not entry_exists(faculty_name, dept_name, coordinator_name, subject_name, subject_type):
                            entry = {
                                "Wydział": faculty_name,
                                "Katedra": dept_name,
                                "Koordynator": coordinator_name,
                                "Przedmiot": subject_name,
                                "Typ": subject_type
                            }
                            print(f"    Zapisuję wpis: {entry}")
                            results.append(entry)
                print(f"    Zebrano przedmioty dla {coordinator_name}")
            except Exception as e:
                print(f"      Błąd dla {coordinator_name}: {e}")

            # Wróć na stronę główną i rozwiń wydział
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

# 5. Przekształć dane do struktury JSON z priorytetem wykładu i osobnym polem Typ
json_data = {}
for entry in results:
    faculty = entry["Wydział"]
    dept = entry["Katedra"]
    subject = entry["Przedmiot"]
    subject_type = entry["Typ"]
    coordinator = entry["Koordynator"]

    # Inicjalizuj strukturę, jeśli nie istnieje
    if faculty not in json_data:
        json_data[faculty] = {}
    if dept not in json_data[faculty]:
        json_data[faculty][dept] = {}
    if subject not in json_data[faculty][dept]:
        json_data[faculty][dept][subject] = {}

    # Dodaj koordynatora do listy dla konkretnego typu
    if subject_type not in json_data[faculty][dept][subject]:
        json_data[faculty][dept][subject][subject_type] = []
    if coordinator not in json_data[faculty][dept][subject][subject_type]:
        json_data[faculty][dept][subject][subject_type].append(coordinator)

# 6. Filtruj dane - tylko wykład lub inne typy, jeśli wykładu nie ma
final_json = {}
for faculty, depts in json_data.items():
    final_json[faculty] = {}
    for dept, subjects in depts.items():
        final_json[faculty][dept] = {}
        for subject, types in subjects.items():
            if "wykład" in types:
                final_json[faculty][dept][subject] = {
                    "Typ": "wykład",
                    "Koordynatorzy": types["wykład"]
                }
            else:
                # Jeśli nie ma wykładu, weź pierwszy napotkany typ
                for subj_type, coordinators in types.items():
                    final_json[faculty][dept][subject] = {
                        "Typ": subj_type,
                        "Koordynatorzy": coordinators
                    }
                    break

# 7. Zapisz do JSON
with open("PLAN.json", "w", encoding="utf-8") as jsonfile:
    json.dump(final_json, jsonfile, ensure_ascii=False, indent=2)

driver.quit()
print("Dane zapisane do pliku plan_zajec.json!")