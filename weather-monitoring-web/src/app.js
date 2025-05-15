import React, { useState, useEffect } from 'react';
import WeatherDisplay from './components/WeatherDisplay';
import { fetchWeatherData } from './services/weatherAPI';
import './assets/styles/main.css';

function App() {
  const [weather, setWeather] = useState(null);
  const [error, setError] = useState(null);
  const [location, setLocation] = useState(null);

  useEffect(() => {
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        async (position) => {
          try {
            const { latitude, longitude } = position.coords;
            setLocation({ lat: latitude, lon: longitude });
            
            // Fetch weather data from OpenWeatherMap
            const weatherData = await fetchWeatherData(latitude, longitude);
            
            // Fetch AI prediction
            const response = await fetch(`/api/weather?lat=${latitude}&lon=${longitude}`);
            if (!response.ok) throw new Error('Weather prediction failed');
            const aiData = await response.json();
            
            // Combine weather data with AI prediction
            setWeather({
              ...weatherData,
              prediction: aiData.prediction
            });
          } catch (err) {
            setError(err.message);
          }
        },
        (err) => setError('Failed to get location: ' + err.message)
      );
    } else {
      setError('Geolocation is not supported by your browser');
    }
  }, []);

  return (
    <div className="App">
      <h1>Weather Monitoring System</h1>
      {error ? (
        <div className="error">{error}</div>
      ) : (
        <WeatherDisplay weatherData={weather} />
      )}
    </div>
  );
}

export default App;