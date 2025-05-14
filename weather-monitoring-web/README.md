# Weather Monitoring Web Application

## Overview
This project is a web application that connects to an AI-based weather monitoring system to inform users of the weather in their current location. It provides real-time weather updates and predictions based on user input or automatic location detection.

## Features
- Automatic location detection using IP address.
- Manual location input for users who prefer to enter their location.
- Displays current weather information including temperature, humidity, and rain prediction.
- Responsive design for a seamless user experience.

## Project Structure
```
weather-monitoring-web
├── src
│   ├── assets
│   │   └── styles
│   │       └── main.css
│   ├── components
│   │   ├── WeatherDisplay.js
│   │   └── LocationInput.js
│   ├── services
│   │   ├── weatherAPI.js
│   │   └── locationService.js
│   ├── utils
│   │   └── helpers.js
│   ├── app.js
│   └── index.html
├── tests
│   └── components
│       └── WeatherDisplay.test.js
├── package.json
├── .env
└── README.md
```

## Installation
1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```
2. Navigate to the project directory:
   ```bash
   cd weather-monitoring-web
   ```
3. Install the dependencies:
   ```bash
   npm install
   ```

## Usage
1. Create a `.env` file in the root directory and add your OpenWeatherMap API key:
   ```
   OPENWEATHER_API_KEY=your_api_key_here
   ```
2. Start the development server:
   ```bash
   npm start
   ```
3. Open your browser and navigate to `http://localhost:3000` to view the application.

## Testing
To run the tests for the components, use the following command:
```bash
npm test
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.

## License
This project is licensed under the MIT License.