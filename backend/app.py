from flask import Flask, jsonify, request
import pandas as pd
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Włączenie CORS

# Wczytanie pliku CSV do pamięci przy uruchomieniu aplikacji
csv_file = "schedule_all.csv"  # Upewnij się, że plik zawiera kolumnę "Studia"
df = pd.read_csv(csv_file, delimiter=",")

# Endpoint: Pobieranie listy wydziałów
@app.route('/api/faculties', methods=['GET'])
def get_faculties():
    faculties = sorted(df["Wydział"].unique())
    return jsonify(faculties)

# Endpoint: Pobieranie listy kierunków dla wybranego wydziału
@app.route('/api/directions', methods=['GET'])
def get_directions():
    faculty = request.args.get('faculty')
    if faculty:
        directions = sorted(df[df["Wydział"] == faculty]["Kierunek"].unique())
    else:
        directions = sorted(df["Kierunek"].unique())
    return jsonify(directions)

# Endpoint: Pobieranie listy przedmiotów dla wybranego wydziału i kierunku
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    faculty = request.args.get('faculty')
    direction = request.args.get('direction')
    
    filtered_df = df
    if faculty:
        filtered_df = filtered_df[filtered_df["Wydział"] == faculty]
    if direction:
        filtered_df = filtered_df[filtered_df["Kierunek"] == direction]

    subjects = sorted(filtered_df["Nazwa przedmiotu"].unique())
    return jsonify(subjects)

# Nowy endpoint: Pobieranie dostępnych typów studiów dla wybranego wydziału, kierunku i przedmiotu
@app.route('/api/study_types', methods=['GET'])
def get_study_types():
    faculty = request.args.get('faculty')
    direction = request.args.get('direction')
    subject = request.args.get('subject')
    
    filtered_df = df
    if faculty:
        filtered_df = filtered_df[filtered_df["Wydział"] == faculty]
    if direction:
        filtered_df = filtered_df[filtered_df["Kierunek"] == direction]
    if subject:
        filtered_df = filtered_df[filtered_df["Nazwa przedmiotu"] == subject]

    study_types = sorted(filtered_df["Studia"].unique())
    return jsonify(study_types)

# Endpoint: Pobieranie harmonogramu z filtrowaniem i nową logiką dla prowadzących
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    faculty = request.args.get('faculty')
    direction = request.args.get('direction')
    subject = request.args.get('subject')
    study_type = request.args.get('study_type')

    if not faculty or not direction:
        return jsonify({"error": "Wydział i kierunek są wymagane"}), 400

    # Filtrowanie danych
    filtered_df = df[(df["Wydział"] == faculty) & (df["Kierunek"] == direction)]
    if subject:
        filtered_df = filtered_df[filtered_df["Nazwa przedmiotu"] == subject]
    if study_type:
        filtered_df = filtered_df[filtered_df["Studia"] == study_type]

    # Sortowanie: wykłady (wyk) jako pierwsze
    filtered_df["SortOrder"] = filtered_df["Typ zajęć"].apply(lambda x: 1 if x == "wyk" else 2)
    filtered_df = filtered_df.sort_values(["Nazwa przedmiotu", "SortOrder", "Prowadzący"])

    # Usuwanie duplikatów dla tego samego prowadzącego w obrębie przedmiotu
    result_df = pd.DataFrame()
    for subject_name in filtered_df["Nazwa przedmiotu"].unique():
        subject_df = filtered_df[filtered_df["Nazwa przedmiotu"] == subject_name]
        for prowadzacy in subject_df["Prowadzący"].unique():
            prowadzacy_df = subject_df[subject_df["Prowadzący"] == prowadzacy]
            if "wyk" in prowadzacy_df["Typ zajęć"].values:
                wyk_df = prowadzacy_df[prowadzacy_df["Typ zajęć"] == "wyk"].iloc[0:1]
                result_df = pd.concat([result_df, wyk_df])
            else:
                result_df = pd.concat([result_df, prowadzacy_df])

    # Konwersja do JSON z dodaniem pola "Studia"
    schedule = result_df[["Wydział", "Kierunek", "Nazwa przedmiotu", "Prowadzący", "Typ zajęć", "Studia"]].to_dict(orient="records")
    return jsonify(schedule)

if __name__ == '__main__':
    app.run(debug=True, port=5000)