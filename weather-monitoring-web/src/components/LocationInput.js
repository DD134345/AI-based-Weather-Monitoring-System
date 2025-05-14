import React, { useState } from 'react';

const LocationInput = ({ onLocationSubmit }) => {
    const [city, setCity] = useState('');
    const [lat, setLat] = useState('');
    const [lon, setLon] = useState('');

    const handleSubmit = (e) => {
        e.preventDefault();
        onLocationSubmit({ city, lat: parseFloat(lat), lon: parseFloat(lon) });
    };

    return (
        <form onSubmit={handleSubmit}>
            <div>
                <label>
                    City:
                    <input 
                        type="text" 
                        value={city} 
                        onChange={(e) => setCity(e.target.value)} 
                        required 
                    />
                </label>
            </div>
            <div>
                <label>
                    Latitude:
                    <input 
                        type="number" 
                        value={lat} 
                        onChange={(e) => setLat(e.target.value)} 
                        required 
                    />
                </label>
            </div>
            <div>
                <label>
                    Longitude:
                    <input 
                        type="number" 
                        value={lon} 
                        onChange={(e) => setLon(e.target.value)} 
                        required 
                    />
                </label>
            </div>
            <button type="submit">Submit Location</button>
        </form>
    );
};

export default LocationInput;