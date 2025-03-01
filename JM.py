from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import re
import time

# Ustawienie przeglądarki
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
wait = WebDriverWait(driver, 15)

# 1. Przejście do strony "Nauczyciele"
driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
print("Weszliśmy na stronę Nauczycieli!")

# 2. Przygotuj dane do CSV
results = []
processed_dept_ids = set()

# Funkcja do przetwarzania katedry dla 6179
def process_department(dept_id, faculty_name):
    try:
        print(f"  Próba lokalizacji katedry: {dept_id}")
        plusik = wait.until(EC.presence_of_element_located((By.ID, f"img_{dept_id}")))
        print(f"  Znaleziono element img_{dept_id} w DOM-ie.")
        driver.execute_script("arguments[0].scrollIntoView(true);", plusik)  # Przewijanie do plusika
        time.sleep(0.5)  # Dajemy więcej czasu na załadowanie
        print(f"  Stan plusika: src={plusik.get_attribute('src')}, visible={plusik.is_displayed()}")

        # Pobierz nazwę katedry dla 6179
        dept_name = f"Katedra {dept_id}"  # Domyślna wartość
        try:
            dept_elem = plusik.find_element(By.XPATH, "./following-sibling::a")
            dept_name = dept_elem.text.strip()
            print(f"  Nazwa katedry: {dept_name}")
        except Exception as e:
            print(f"  Nie udało się znaleźć nazwy katedry: {e}. Używam domyślnej nazwy: {dept_name}")
        print(f"  Potwierdzenie dept_name przed rozwinięciem: {dept_name}")

        # Rozwiń katedrę, jeśli nie jest rozwinięta
        if "plus.gif" in plusik.get_attribute("src"):
            print(f"  Rozwijam katedrę {dept_id}...")
            try:
                plusik.click()
                print("  Użyto zwykłego click() do kliknięcia.")
                time.sleep(1)
            except Exception as e:
                print(f"  Kliknięcie nie powiodło się: {e}. Próbuję execute_script...")
                driver.execute_script(f"get_left_tree_branch('{dept_id}', 'img_{dept_id}', 'div_{dept_id}', '2', '1');")
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

                subject_pattern = r"<strong>(.*?)</strong> - (.*?)(?:, występowanie|\s*<br|\s*<hr)"
                for match in re.finditer(subject_pattern, legend_text):
                    subject_code = match.group(1)
                    subject_name = match.group(2).strip()
                    entry = {
                        "Wydział": faculty_name,
                        "Katedra": dept_name,
                        "Koordynator": coordinator_name,
                        "Przedmiot": f"{subject_code} - {subject_name}"
                    }
                    print(f"    Zapisuję wpis: {entry}")
                    results.append(entry)
                print(f"    Zebrano przedmioty dla {coordinator_name}")
            except Exception as e:
                print(f"      Błąd dla {coordinator_name}: {e}")

            # Wróć na stronę główną i rozwiń wydział
            driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
            wait.until(EC.presence_of_element_located((By.ID, "6179")))
            driver.execute_script("branch(2,6179,0,'Jednostki Międzywydziałowe');")
            time.sleep(0.5)

        processed_dept_ids.add(dept_id)
        print(f"  Katedra {dept_name} zakończona.")

    except Exception as e:
        print(f"  Błąd przy przetwarzaniu katedry (ID: {dept_id}): {e}")
        processed_dept_ids.add(dept_id)

# Funkcja do przetwarzania wydziału 6179
def process_faculty():
    faculty_id = "6179"
    faculty_name = "Jednostki Międzywydziałowe"
    dept_ids = ["6196", "6197"]

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
                process_department(dept_id, faculty_name)
                print(f"Zakończono przetwarzanie katedry {dept_id}.")
                driver.get("https://plany.ubb.edu.pl/left_menu.php?type=2")
                wait.until(EC.presence_of_element_located((By.ID, faculty_id)))
                driver.execute_script(f"branch(2,{faculty_id},0,'{faculty_name}');")
                time.sleep(0.5)

    except Exception as e:
        print(f"Błąd przy przetwarzaniu wydziału {faculty_name}: {e}")

# Uruchom przetwarzanie
process_faculty()

# 5. Zapisz do CSV
with open("plan_zajec_6179.csv", "w", newline="", encoding="utf-8") as csvfile:
    fieldnames = ["Wydział", "Katedra", "Koordynator", "Przedmiot"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

driver.quit()
print("Dane zapisane do pliku plan_zajec_6179.csv!")