const express = require('express');
const cors = require('cors');
const app = express();
const port = process.env.PORT || 3000;

// Enable CORS
app.use(cors());
app.use(express.json());

// Serve static files from public directory
app.use(express.static('public'));

// API endpoint to get weather data
app.get('/api/weather', async (req, res) => {
    try {
        const { lat, lon } = req.query;
        const WeatherPredictor = require('./AI');
        const predictor = new WeatherPredictor();
        
        const location = {
            lat: parseFloat(lat),
            lon: parseFloat(lon),
            city: 'Current Location'
        };

        const weatherData = await predictor.fetch_weather_data(location);
        const rainPrediction = await predictor.predict_rain(
            weatherData.temperature,
            weatherData.humidity,
            weatherData.pressure
        );

        res.json({
            ...weatherData,
            rainPrediction
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(port, () => {
    console.log(`Server running at http://localhost:${port}`);
});