import axios from 'axios';

const getCurrentLocation = async () => {
    try {
        const response = await axios.get('https://ipapi.co/json/');
        const { city, latitude: lat, longitude: lon } = response.data;
        return { city, lat, lon };
    } catch (error) {
        console.error("Error fetching location:", error);
        return { city: 'London', lat: 51.5074, lon: -0.1278 }; // Default to London
    }
};

const getLocationInput = () => {
    const city = prompt("Enter your city name:");
    const lat = parseFloat(prompt("Enter your latitude (e.g. 51.5074 for London):"));
    const lon = parseFloat(prompt("Enter your longitude (e.g. -0.1278 for London):"));
    return { city, lat, lon };
};

export { getCurrentLocation, getLocationInput };