import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [faculties, setFaculties] = useState([]);      // Lista wydziałów
  const [directions, setDirections] = useState([]);    // Lista kierunków
  const [subjects, setSubjects] = useState([]);        // Lista przedmiotów
  const [selectedFaculty, setSelectedFaculty] = useState('');  // Wybrany wydział
  const [selectedDirection, setSelectedDirection] = useState('');  // Wybrany kierunek
  const [selectedSubject, setSelectedSubject] = useState('');  // Wybrany przedmiot
  const [schedule, setSchedule] = useState([]);        // Wyniki harmonogramu
  const [error, setError] = useState(null);            // Błędy
  const [loading, setLoading] = useState(false);       // Stan ładowania

  // Pobieranie wydziałów przy załadowaniu komponentu
  useEffect(() => {
    const fetchFaculties = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/faculties');
        setFaculties(response.data);
      } catch (error) {
        console.error('Błąd podczas pobierania wydziałów:', error);
        setError('Nie udało się załadować wydziałów.');
      }
    };
    fetchFaculties();
  }, []);

  // Pobieranie kierunków po zmianie wydziału
  useEffect(() => {
    const fetchDirections = async () => {
      if (!selectedFaculty) {
        setDirections([]);
        setSelectedDirection('');
        setSubjects([]);
        setSelectedSubject('');
        return;
      }

      try {
        const response = await axios.get('http://localhost:5000/api/directions', {
          params: { faculty: selectedFaculty },
        });
        setDirections(response.data);
        setSelectedDirection(''); // Reset kierunku
        setSubjects([]);
        setSelectedSubject(''); // Reset przedmiotu
      } catch (error) {
        console.error('Błąd podczas pobierania kierunków:', error);
        setError('Nie udało się załadować kierunków.');
        setDirections([]);
      }
    };
    fetchDirections();
  }, [selectedFaculty]);

  // Pobieranie przedmiotów po zmianie kierunku
  useEffect(() => {
    const fetchSubjects = async () => {
      if (!selectedFaculty || !selectedDirection) {
        setSubjects([]);
        setSelectedSubject('');
        return;
      }

      try {
        const response = await axios.get('http://localhost:5000/api/subjects', {
          params: { faculty: selectedFaculty, direction: selectedDirection },
        });
        setSubjects(response.data);
        setSelectedSubject(''); // Reset przedmiotu
      } catch (error) {
        console.error('Błąd podczas pobierania przedmiotów:', error);
        setError('Nie udało się załadować przedmiotów.');
        setSubjects([]);
      }
    };
    fetchSubjects();
  }, [selectedFaculty, selectedDirection]);

  // Obsługa wyszukiwania
  const handleSearch = async () => {
    if (!selectedFaculty || !selectedDirection) {
      setError('Proszę wybrać wydział i kierunek.');
      setSchedule([]);
      return;
    }

    setLoading(true);
    setError(null);
    setSchedule([]);

    try {
      const response = await axios.get('http://localhost:5000/api/schedule', {
        params: {
          faculty: selectedFaculty,
          direction: selectedDirection,
          subject: selectedSubject || null, // Przekazujemy null, jeśli przedmiot nie wybrany
        },
      });
      setSchedule(response.data);
    } catch (error) {
      console.error('Błąd podczas wyszukiwania:', error);
      setError('Nie udało się pobrać harmonogramu.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <h1>Harmonogram zajęć</h1>

      {/* Formularz wyboru */}
      <div className="form-container">
        <div className="form-group">
          <label htmlFor="faculty">Wydział:</label>
          <select
            id="faculty"
            value={selectedFaculty}
            onChange={(e) => setSelectedFaculty(e.target.value)}
          >
            <option value="">Wybierz wydział</option>
            {faculties.map((faculty, index) => (
              <option key={index} value={faculty}>
                {faculty}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="direction">Kierunek:</label>
          <select
            id="direction"
            value={selectedDirection}
            onChange={(e) => setSelectedDirection(e.target.value)}
            disabled={!selectedFaculty}
          >
            <option value="">Wybierz kierunek</option>
            {directions.map((direction, index) => (
              <option key={index} value={direction}>
                {direction}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="subject">Przedmiot:</label>
          <select
  id="subject"
  value={selectedSubject}
  onChange={(e) => setSelectedSubject(e.target.value)}
  disabled={!selectedDirection}
>
  <option value="">Wszystkie przedmioty</option>
  {subjects.map((subject, index) => (
    <option key={index} value={subject} title={subject}>
      {subject.length > 40 ? subject.substring(0, 37) + "..." : subject}
    </option>
  ))}
</select>

        </div>

        <button onClick={handleSearch} disabled={loading || !selectedFaculty || !selectedDirection}>
          {loading ? 'Szukanie...' : 'Szukaj'}
        </button>
      </div>

      {/* Wyświetlanie wyników */}
      {error && <p className="error">{error}</p>}
      {loading && <p className="loading">Ładowanie danych...</p>}
      {!loading && schedule.length === 0 && !error && (
        <p className="info">Wybierz wydział i kierunek, aby zobaczyć harmonogram.</p>
      )}
      {schedule.length > 0 && (
        <table>
          <thead>
            <tr>
              <th>Wydział</th>
              <th>Prowadzący</th>
              <th>Nazwa przedmiotu</th>
              <th>Typ zajęć</th>
              <th>Kierunek</th>
            </tr>
          </thead>
          <tbody>
            {schedule.map((item, index) => (
              <tr key={index}>
                <td>{item.Wydzial}</td>
                <td>{item.Prowadzacy}</td>
                <td>{item.Nazwa_przedmiotu}</td>
                <td>{item.Typ_zajec}</td>
                <td>{item.Kierunek}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

export default App;