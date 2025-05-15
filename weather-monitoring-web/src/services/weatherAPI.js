import axios from 'axios';

const API_KEY = process.env.REACT_APP_OPENWEATHER_API_KEY;
const BASE_URL = "https://api.openweathermap.org/data/2.5/weather";

export const fetchWeatherData = async (lat, lon) => {
    try {
        const response = await axios.get(`${BASE_URL}`, {
            params: {
                lat: lat,
                lon: lon,
                appid: API_KEY,
                units: 'metric'
            }
        });

        const data = response.data;
        return {
            temperature: data.main.temp,
            humidity: data.main.humidity,
            pressure: data.main.pressure,
            city: data.name,
            country: data.sys.country,
            description: data.weather[0].description,
            rain: data.rain ? data.rain['1h'] : 0
        };
    } catch (error) {
        console.error("Error fetching weather data:", error);
        throw error;
    }
};