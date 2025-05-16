#include <DHT.h>
#include <Wire.h>
#include <Adafruit_BME280.h>
#include <ArduinoJson.h>

#define DHTPIN 2       // DHT11 data pin
#define DHTTYPE DHT11  // DHT11 sensor type
#define SEALEVELPRESSURE_HPA (1013.25)

DHT dht(DHTPIN, DHTTYPE);
Adafruit_BME280 bme;

void setup() {
    Serial.begin(9600);
    dht.begin();
    
    if (!bme.begin(0x76)) {
        Serial.println("{\"error\": \"BME280 not found\"}");
        while (1);
    }
}

void loop() {
    // Create JSON document
    StaticJsonDocument<200> doc;
    
    // Read DHT11 sensor
    float dht_temp = dht.readTemperature();
    float dht_humidity = dht.readHumidity();
    
    // Read BME280 sensor
    float bme_temp = bme.readTemperature();
    float bme_humidity = bme.readHumidity();
    float pressure = bme.readPressure() / 100.0F;
    
    // Average temperature and humidity readings
    float temp = (isnan(dht_temp) ? bme_temp : (dht_temp + bme_temp) / 2);
    float humidity = (isnan(dht_humidity) ? bme_humidity : (dht_humidity + bme_humidity) / 2);
    
    // Package data
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["pressure"] = pressure;
    
    // Send JSON over serial
    serializeJson(doc, Serial);
    Serial.println();
    
    delay(5000);  // Wait 5 seconds between readings
}