from flask import Flask, request, jsonify
from src.weather_predictor import WeatherPredictor
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
predictor = WeatherPredictor()

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        lat = request.args.get('lat')
        lon = request.args.get('lon')
        
        if not lat or not lon:
            return jsonify({'error': 'Missing latitude or longitude'}), 400
            
        prediction = predictor.predict([float(lat), float(lon)])
        return jsonify({
            'temperature': float(prediction[0]),
            'humidity': float(prediction[1]),
            'pressure': float(prediction[2])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=int(os.getenv('PORT', 3001)))