import React from 'react';
import { render, screen } from '@testing-library/react';
import WeatherDisplay from '../../src/components/WeatherDisplay';

describe('WeatherDisplay Component', () => {
    test('renders weather information correctly', () => {
        const weatherData = {
            temperature: 20,
            humidity: 50,
            rainPrediction: false,
        };

        render(<WeatherDisplay weather={weatherData} />);

        expect(screen.getByText(/Temperature:/i)).toBeInTheDocument();
        expect(screen.getByText(/20/i)).toBeInTheDocument();
        expect(screen.getByText(/Humidity:/i)).toBeInTheDocument();
        expect(screen.getByText(/50/i)).toBeInTheDocument();
        expect(screen.getByText(/No rain expected/i)).toBeInTheDocument();
    });

    test('renders rain prediction correctly when rain is expected', () => {
        const weatherData = {
            temperature: 18,
            humidity: 70,
            rainPrediction: true,
        };

        render(<WeatherDisplay weather={weatherData} />);

        expect(screen.getByText(/Rain expected/i)).toBeInTheDocument();
    });
});