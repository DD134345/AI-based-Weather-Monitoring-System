import React from 'react';

const WeatherDisplay = ({ weatherData }) => {
    if (!weatherData) {
        return <div className="loading">Loading weather data...</div>;
    }

    return (
        <div className="weather-card">
            <div className="location">
                {weatherData.city}, {weatherData.country}
            </div>
            <div className="weather-info">
                <div className="weather-item">
                    <h3>Temperature</h3>
                    <p>{weatherData.temperature.toFixed(1)}°C</p>
                </div>
                <div className="weather-item">
                    <h3>Humidity</h3>
                    <p>{weatherData.humidity}%</p>
                </div>
                <div className="weather-item">
                    <h3>Pressure</h3>
                    <p>{weatherData.pressure} hPa</p>
                </div>
                <div className="weather-item">
                    <h3>Conditions</h3>
                    <p>{weatherData.description}</p>
                </div>
                <div className="weather-item">
                    <h3>AI Prediction</h3>
                    <p>{weatherData.prediction ? 'Rain Expected' : 'No Rain Expected'}</p>
                </div>
            </div>
        </div>
    );
};

export default WeatherDisplay;