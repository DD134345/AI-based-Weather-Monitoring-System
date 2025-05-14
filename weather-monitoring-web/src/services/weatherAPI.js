const API_KEY = process.env.OPENWEATHER_API_KEY;
const BASE_URL = "http://api.openweathermap.org/data/2.5/weather";

export const fetchWeatherData = async (lat, lon) => {
    try {
        const response = await fetch(`${BASE_URL}?lat=${lat}&lon=${lon}&appid=${API_KEY}&units=metric`);
        if (!response.ok) {
            throw new Error('Failed to fetch weather data');
        }
        const data = await response.json();
        return {
            temperature: data.main.temp,
            humidity: data.main.humidity,
            pressure: data.main.pressure,
            rain: data.rain ? data.rain['1h'] : 0
        };
    } catch (error) {
        console.error("Error fetching weather data:", error);
        return null;
    }
};