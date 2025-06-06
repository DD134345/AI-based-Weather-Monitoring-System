#include <WiFi.h>
#include <BLEDevice.h>
#include <BLEServer.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

// Pin configuration
#define DHTPIN 13
#define DHTTYPE DHT11
#define LED_PIN 2

// Data buffer size
#define BUFFER_SIZE 60  // Store 5 minutes of data (5s intervals)

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

// Web server
AsyncWebServer server(80);

// Data buffer
struct WeatherData {
    float temperature;
    float humidity;
    float pressure;
    unsigned long timestamp;
};
WeatherData dataBuffer[BUFFER_SIZE];
int bufferIndex = 0;

// Task handles
TaskHandle_t sensorTaskHandle = NULL;
TaskHandle_t bleTaskHandle = NULL;

const unsigned long FAST_SAMPLING_INTERVAL = 5000; // 5 seconds
const unsigned long SLOW_SAMPLING_INTERVAL = 3600000; // 1 hour
const unsigned long UPDATE_INTERVAL = 10000; // 10 seconds

void setup() {
    Serial.begin(115200);
    
    // Initialize SPIFFS for data storage
    if(!SPIFFS.begin(true)) {
        Serial.println("SPIFFS Mount Failed");
        return;
    }
    
    // Initialize pins
    pinMode(LED_PIN, OUTPUT);
    
    // Initialize sensors
    dht.begin();
    if (!bmp.begin()) {
        Serial.println("BMP180 Error!");
        while (1) { delay(10); }
    }
    
    // Setup network connections
    setupWiFi();
    setupBLE();
    setupWebServer();
}

void loop() {
    static unsigned long lastReading = 0;
    unsigned long currentTime = millis();
    
    if (currentTime - lastReading >= UPDATE_INTERVAL) {
        float temp = dht.readTemperature();
        float humidity = dht.readHumidity();
        float pressure = bmp.readPressure() / 100.0F;
        
        if (isValidReading(temp, humidity, pressure)) {
            sendData(temp, humidity, pressure);
            lastReading = currentTime;
        }
    }
}

void sensorTask(void *parameter) {
    static unsigned long lastFastReading = 0;
    static unsigned long lastSlowReading = 0;
    
    while(true) {
        unsigned long currentTime = millis();
        
        // Fast sampling for short-term predictions
        if (currentTime - lastFastReading >= FAST_SAMPLING_INTERVAL) {
            float temp = dht.readTemperature();
            float humidity = dht.readHumidity();
            float pressure = bmp.readPressure() / 100.0F;
            
            if (!isnan(temp) && !isnan(humidity) && pressure > 0) {
                sendSensorData(temp, humidity, pressure);
                lastFastReading = currentTime;
            }
        }
        
        // Hourly sampling for long-term predictions
        if (currentTime - lastSlowReading >= SLOW_SAMPLING_INTERVAL) {
            saveToBuffer();
            lastSlowReading = currentTime;
        }
        
        vTaskDelay(pdMS_TO_TICKS(1000)); // Check every second
    }
}

void sendSensorData(float temp, float humidity, float pressure) {
    StaticJsonDocument<200> doc;
    doc["temperature"] = temp;
    doc["humidity"] = humidity;
    doc["pressure"] = pressure;
    doc["timestamp"] = millis();
    
    String output;
    serializeJson(doc, output);
    Serial.println(output);
    
    // Also send via BLE if connected
    if (deviceConnected) {
        pCharacteristic->setValue(output.c_str());
        pCharacteristic->notify();
    }
}

void bleTask(void *parameter) {
    TickType_t xLastWakeTime = xTaskGetTickCount();
    
    while(true) {
        if (pCharacteristic) {
            // Get latest data
            WeatherData latest = dataBuffer[(bufferIndex - 1 + BUFFER_SIZE) % BUFFER_SIZE];
            
            // Create JSON
            StaticJsonDocument<200> doc;
            doc["temperature"] = latest.temperature;
            doc["humidity"] = latest.humidity;
            doc["pressure"] = latest.pressure;
            doc["timestamp"] = latest.timestamp;
            
            String jsonString;
            serializeJson(doc, jsonString);
            
            // Update BLE characteristic
            pCharacteristic->setValue(jsonString.c_str());
            pCharacteristic->notify();
        }
        
        // Run task every 1 second
        vTaskDelayUntil(&xLastWakeTime, pdMS_TO_TICKS(1000));
    }
}

void setupWebServer() {
    // Serve current data
    server.on("/data", HTTP_GET, [](AsyncWebServerRequest *request) {
        WeatherData latest = dataBuffer[(bufferIndex - 1 + BUFFER_SIZE) % BUFFER_SIZE];
        
        StaticJsonDocument<200> doc;
        doc["temperature"] = latest.temperature;
        doc["humidity"] = latest.humidity;
        doc["pressure"] = latest.pressure;
        doc["timestamp"] = latest.timestamp;
        
        String jsonString;
        serializeJson(doc, jsonString);
        
        request->send(200, "application/json", jsonString);
    });
    
    // Serve historical data
    server.on("/history", HTTP_GET, [](AsyncWebServerRequest *request) {
        String jsonArray = "[";
        for(int i = 0; i < BUFFER_SIZE; i++) {
            if (dataBuffer[i].timestamp > 0) {
                StaticJsonDocument<200> doc;
                doc["temperature"] = dataBuffer[i].temperature;
                doc["humidity"] = dataBuffer[i].humidity;
                doc["pressure"] = dataBuffer[i].pressure;
                doc["timestamp"] = dataBuffer[i].timestamp;
                
                String jsonString;
                serializeJson(doc, jsonString);
                
                if (i > 0) jsonArray += ",";
                jsonArray += jsonString;
            }
        }
        jsonArray += "]";
        
        request->send(200, "application/json", jsonArray);
    });
    
    server.begin();
}

void saveDataToSPIFFS() {
    File file = SPIFFS.open("/data.json", "w");
    if(!file) {
        return;
    }
    
    // Save entire buffer
    String jsonArray = "[";
    for(int i = 0; i < BUFFER_SIZE; i++) {
        if (dataBuffer[i].timestamp > 0) {
            StaticJsonDocument<200> doc;
            doc["temperature"] = dataBuffer[i].temperature;
            doc["humidity"] = dataBuffer[i].humidity;
            doc["pressure"] = dataBuffer[i].pressure;
            doc["timestamp"] = dataBuffer[i].timestamp;
            
            String jsonString;
            serializeJson(doc, jsonString);
            
            if (i > 0) jsonArray += ",";
            jsonArray += jsonString;
        }
    }
    jsonArray += "]";
    
    file.print(jsonArray);
    file.close();
}