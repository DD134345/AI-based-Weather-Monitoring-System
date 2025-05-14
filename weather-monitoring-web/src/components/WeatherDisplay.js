import React from 'react';

const WeatherDisplay = ({ weatherData }) => {
    if (!weatherData) {
        return <div>Loading...</div>;
    }

    const { temperature, humidity, rain } = weatherData;
    const rainPrediction = rain ? 'Rain expected' : 'No rain expected';

    return (
        <div className="weather-display">
            <h2>Current Weather</h2>
            <p>Temperature: {temperature}°C</p>
            <p>Humidity: {humidity}%</p>
            <p>{rainPrediction}</p>
        </div>
    );
};

export default WeatherDisplay;