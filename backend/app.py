from flask import Flask, jsonify, request
import pyodbc
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Włączenie CORS

# Połączenie z SQL Server
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=DESKTOP-4SOLSPV\SQLEXPRESS;"  
    "DATABASE=Plan_Zajec;"  
    "Trusted_Connection=yes;" 
)

# Endpoint: Pobieranie listy wydziałów
@app.route('/api/faculties', methods=['GET'])
def get_faculties():
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT Wydzial FROM Schedule ORDER BY Wydzial")
        rows = cursor.fetchall()
        conn.close()
        faculties = [row[0] for row in rows]
        return jsonify(faculties)
    except Exception as e:
        print(f"Błąd podczas pobierania wydziałów: {e}")
        return jsonify({"error": "Błąd serwera podczas pobierania wydziałów"}), 500

# Endpoint: Pobieranie listy kierunków dla wybranego wydziału
@app.route('/api/directions', methods=['GET'])
def get_directions():
    faculty = request.args.get('faculty')
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if faculty:
            query = "SELECT DISTINCT Kierunek FROM Schedule WHERE Wydzial = ? ORDER BY Kierunek"
            cursor.execute(query, (faculty,))
        else:
            query = "SELECT DISTINCT Kierunek FROM Schedule ORDER BY Kierunek"
            cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        directions = [row[0] for row in rows]
        return jsonify(directions)
    except Exception as e:
        print(f"Błąd podczas pobierania kierunków: {e}")
        return jsonify({"error": "Błąd serwera podczas pobierania kierunków"}), 500

# Endpoint: Pobieranie listy przedmiotów dla wybranego wydziału i kierunku
@app.route('/api/subjects', methods=['GET'])
def get_subjects():
    faculty = request.args.get('faculty')
    direction = request.args.get('direction')
    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        if faculty and direction:
            query = "SELECT DISTINCT Nazwa_przedmiotu FROM Schedule WHERE Wydzial = ? AND Kierunek = ? ORDER BY Nazwa_przedmiotu"
            cursor.execute(query, (faculty, direction))
        else:
            return jsonify([])
        rows = cursor.fetchall()
        conn.close()
        subjects = [row[0] for row in rows]
        return jsonify(subjects)
    except Exception as e:
        print(f"Błąd podczas pobierania przedmiotów: {e}")
        return jsonify({"error": "Błąd serwera podczas pobierania przedmiotów"}), 500

# Endpoint: Pobieranie harmonogramu z filtrowaniem
@app.route('/api/schedule', methods=['GET'])
def get_schedule():
    faculty = request.args.get('faculty')
    direction = request.args.get('direction')
    subject = request.args.get('subject')

    if not faculty or not direction:
        return jsonify({"error": "Wydział i kierunek są wymagane"}), 400

    try:
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()

        query = """
        WITH Wykładowcy AS (
            SELECT 
                Wydzial,
                Kierunek,
                Nazwa_przedmiotu,
                Prowadzacy,
                Typ_zajec,
                ROW_NUMBER() OVER (PARTITION BY Kierunek, Nazwa_przedmiotu ORDER BY Prowadzacy) AS rn
            FROM Schedule
            WHERE Typ_zajec = 'wyk'
                AND Wydzial = ?
                AND Kierunek = ?
                AND (Nazwa_przedmiotu = ? OR ? IS NULL)
        ),
        Pozostali AS (
            SELECT 
                s.Wydzial,
                s.Kierunek,
                s.Nazwa_przedmiotu,
                s.Prowadzacy,
                s.Typ_zajec
            FROM Schedule s
            LEFT JOIN Wykładowcy w 
                ON s.Kierunek = w.Kierunek 
                AND s.Nazwa_przedmiotu = w.Nazwa_przedmiotu 
                AND s.Prowadzacy = w.Prowadzacy
            WHERE s.Typ_zajec != 'wyk' 
                AND s.Wydzial = ?
                AND s.Kierunek = ?
                AND (s.Nazwa_przedmiotu = ? OR ? IS NULL)
                AND w.Prowadzacy IS NULL
        ),
        Wynik AS (
            SELECT 
                Wydzial,
                Kierunek,
                Nazwa_przedmiotu,
                Prowadzacy,
                Typ_zajec,
                CASE 
                    WHEN Typ_zajec = 'wyk' THEN 1
                    ELSE 2
                END AS SortOrder
            FROM Wykładowcy
            WHERE rn = 1
            UNION ALL
            SELECT 
                Wydzial,
                Kierunek,
                Nazwa_przedmiotu,
                Prowadzacy,
                Typ_zajec,
                CASE 
                    WHEN Typ_zajec = 'wyk' THEN 1
                    ELSE 2
                END AS SortOrder
            FROM Pozostali
        )
        SELECT 
            Wydzial,
            Kierunek,
            Nazwa_przedmiotu,
            Prowadzacy,
            Typ_zajec
        FROM Wynik
        ORDER BY 
            Wydzial,
            Kierunek,
            Nazwa_przedmiotu,
            SortOrder,
            Prowadzacy;
        """
        
        cursor.execute(query, (faculty, direction, subject, subject, faculty, direction, subject, subject))
        rows = cursor.fetchall()
        conn.close()

        # Konwersja wyników na JSON
        schedule = [
            {
                "Wydzial": row[0],
                "Kierunek": row[1],
                "Nazwa_przedmiotu": row[2],
                "Prowadzacy": row[3],
                "Typ_zajec": row[4]
            } for row in rows
        ]
        return jsonify(schedule)
    except Exception as e:
        print(f"Błąd podczas pobierania harmonogramu: {e}")
        return jsonify({"error": "Błąd serwera podczas pobierania harmonogramu"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)
