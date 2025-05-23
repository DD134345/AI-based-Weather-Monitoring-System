#include <Wire.h>
#include "DHT.h"
#include <Adafruit_BMP085.h>
#include <ArduinoJson.h>
#include "BluetoothSerial.h"

// Pin Definitions
#define DHTPIN 13     
#define DHTTYPE DHT11

// Create objects
DHT dht(DHTPIN, DHTTYPE);
Adafruit_BMP085 bmp;
BluetoothSerial SerialBT;

// Configuration
const char* deviceName = "WeatherStation";
unsigned long previousMillis = 0;
const long interval = 5000;  // Interval between readings (5 seconds)

void setup() {
  // Initialize Serial communication
  Serial.begin(115200);
  
  // Initialize Bluetooth
  SerialBT.begin(deviceName);
  
  // Initialize sensors
  dht.begin();
  if (!bmp.begin()) {
    Serial.println("Could not find BMP180 sensor!");
    SerialBT.println("Could not find BMP180 sensor!");
    while (1) {}
  }
  
  Serial.println("Weather Station Ready!");
  SerialBT.println("Weather Station Ready!");
}

void sendSensorData(Stream &output) {
  StaticJsonDocument<200> doc;
  
  // Read DHT11 sensor
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();
  
  // Read BMP180 sensor
  float pressure = bmp.readPressure() / 100.0F; // Convert to hPa
  float altitude = bmp.readAltitude();
  
  // Check if any reads failed
  if (isnan(temperature) || isnan(humidity)) {
    doc["error"] = "Failed to read DHT11";
  } else {
    doc["temperature"] = temperature;
    doc["humidity"] = humidity;
    doc["pressure"] = pressure;
    doc["altitude"] = altitude;
    doc["timestamp"] = millis();
  }
  
  // Send JSON data
  serializeJson(doc, output);
  output.println();
}

void loop() {
  unsigned long currentMillis = millis();
  
  // Check if it's time to send new data
  if (currentMillis - previousMillis >= interval) {
    previousMillis = currentMillis;
    
    // Send data through Serial
    sendSensorData(Serial);
    
    // Send data through Bluetooth
    sendSensorData(SerialBT);
  }
  
  // Handle incoming commands from both Serial and Bluetooth
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    handleCommand(command, Serial);
  }
  
  if (SerialBT.available()) {
    String command = SerialBT.readStringUntil('\n');
    handleCommand(command, SerialBT);
  }
}

void handleCommand(String command, Stream &output) {
  command.trim();
  
  if (command == "getData") {
    sendSensorData(output);
  }
  else if (command == "status") {
    output.println("Weather Station Online");
  }
  else {
    output.println("Unknown command");
  }
}