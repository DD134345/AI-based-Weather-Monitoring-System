import React, { useState, useEffect } from 'react';
import WeatherDisplay from './components/WeatherDisplay';
import LocationInput from './components/LocationInput';
import { fetchWeatherData } from './services/weatherAPI';
import { getCurrentLocation } from './services/locationService';

const App = () => {
    const [weatherData, setWeatherData] = useState(null);
    const [location, setLocation] = useState(null);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchWeather = async () => {
            try {
                const currentLocation = await getCurrentLocation();
                setLocation(currentLocation);
                const data = await fetchWeatherData(currentLocation);
                setWeatherData(data);
            } catch (err) {
                setError(err.message);
            }
        };

        fetchWeather();
    }, []);

    const handleLocationChange = async (newLocation) => {
        setLocation(newLocation);
        try {
            const data = await fetchWeatherData(newLocation);
            setWeatherData(data);
        } catch (err) {
            setError(err.message);
        }
    };

    return (
        <div>
            <h1>Weather Monitoring System</h1>
            {error && <p>Error: {error}</p>}
            {weatherData ? (
                <WeatherDisplay data={weatherData} />
            ) : (
                <LocationInput onLocationChange={handleLocationChange} />
            )}
        </div>
    );
};

export default App;