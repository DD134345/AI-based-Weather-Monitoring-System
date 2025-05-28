#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>
#include <ArduinoJson.h>

// Pin configuration
#define DHTPIN 13
#define DHTTYPE DHT11
#define LED_PIN 2

// Sensors
DHT dht(DHTPIN, DHTTYPE);
Adafruit_BMP085 bmp;

// WiFi credentials
const char* ssid = "WeatherStation";
const char* password = "weather123";

// Bluetooth
BLEServer* pServer = NULL;
BLECharacteristic* pCharacteristic = NULL;
#define SERVICE_UUID "181A"
#define CHAR_UUID "2A6E"

void setup() {
    Serial.begin(115200);
    pinMode(LED_PIN, OUTPUT);
    
    // Initialize sensors
    dht.begin();
    if (!bmp.begin()) {
        Serial.println("BMP180 Error!");
        while (1) { delay(10); }
    }
    
    setupWiFi();
    setupBLE();
}

void loop() {
    // Read sensors
    float temp = dht.readTemperature();
    float humidity = dht.readHumidity();
    float pressure = bmp.readPressure() / 100.0F;
    
    // Create JSON
    StaticJsonDocument<200> doc;
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["pressure"] = pressure;
    
    String jsonString;
    serializeJson(doc, jsonString);
    
    // Send data
    Serial.println(jsonString);
    if (pCharacteristic) {
        pCharacteristic->setValue(jsonString.c_str());
    }
    
    // Activity indicator
    digitalWrite(LED_PIN, !digitalRead(LED_PIN));
    delay(5000);
}