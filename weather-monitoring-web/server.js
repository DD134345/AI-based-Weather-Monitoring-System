const express = require('express');
const cors = require('cors');
const { spawn } = require('child_process');
const path = require('path');

const app = express();
const port = process.env.PORT || 3001;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'build')));

app.get('/api/weather', async (req, res) => {
    try {
        const { lat, lon } = req.query;
        
        // Spawn Python process
        const pythonProcess = spawn('python', [
            path.join(__dirname, '..', 'AI'),
            '--lat', lat,
            '--lon', lon
        ]);

        let result = '';

        // Collect data from Python script
        pythonProcess.stdout.on('data', (data) => {
            result += data.toString();
        });

        // Handle Python script completion
        pythonProcess.on('close', (code) => {
            if (code !== 0) {
                return res.status(500).json({ error: 'Failed to process weather data' });
            }
            try {
                const weatherData = JSON.parse(result);
                res.json(weatherData);
            } catch (error) {
                res.status(500).json({ error: 'Invalid data received from AI model' });
            }
        });

    } catch (error) {
        console.error('Server error:', error);
        res.status(500).json({ error: 'Internal server error' });
    }
});

app.listen(port, () => {
    console.log(`Server running on port ${port}`);
});