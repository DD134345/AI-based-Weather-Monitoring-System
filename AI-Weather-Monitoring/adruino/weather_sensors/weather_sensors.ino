#include <WiFi.h>
#include <DHT.h>
#include <Adafruit_BMP085.h>
#include <ArduinoJson.h>
#include <SPIFFS.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <mbedtls/md5.h>

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

const unsigned long FAST_SAMPLING_INTERVAL = 5000; // 5 seconds
const unsigned long SLOW_SAMPLING_INTERVAL = 3600000; // 1 hour
const unsigned long UPDATE_INTERVAL = 10000; // 10 seconds

// Function declarations
void setupWiFi();
bool isValidReading(float temp, float humidity, float pressure);
void sendData(float temp, float humidity, float pressure);
void saveToBuffer();

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
        String jsonString; // Declare jsonString here
        for(int i = 0; i < BUFFER_SIZE; i++) {
            if (dataBuffer[i].timestamp > 0) {
                StaticJsonDocument<200> doc;
                doc["temperature"] = dataBuffer[i].temperature;
                doc["humidity"] = dataBuffer[i].humidity;
                doc["pressure"] = dataBuffer[i].pressure;
                doc["timestamp"] = dataBuffer[i].timestamp;
                
                
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

// Implementations for the missing functions
void setupWiFi() {
    Serial.println("Connecting to WiFi");
    WiFi.begin(ssid, password);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    
    Serial.println("WiFi connected");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
}

bool isValidReading(float temp, float humidity, float pressure) {
    return (!isnan(temp) && !isnan(humidity) && !isnan(pressure));
}

void sendData(float temp, float humidity, float pressure) {
    Serial.print("Temperature: ");
    Serial.print(temp);
    Serial.print(" *C, Humidity: ");
    Serial.print(humidity);
    Serial.print(" %, Pressure: ");
    Serial.print(pressure);
    Serial.println(" hPa");
}

void saveToBuffer() {
    WeatherData newData;
    newData.temperature = dht.readTemperature();
    newData.humidity = dht.readHumidity();
    newData.pressure = bmp.readPressure() / 100.0F;
    newData.timestamp = millis();
    
    dataBuffer[bufferIndex] = newData;
    bufferIndex = (bufferIndex + 1) % BUFFER_SIZE;
}

bool getMD5(uint8_t* data, uint16_t len, char* output){
  unsigned char _buf[16];
  mbedtls_md5_context _ctx;
  mbedtls_md5_init(&_ctx);
  mbedtls_md5_starts(&_ctx);
  mbedtls_md5_update(&_ctx, data, len);
  mbedtls_md5_finish(&_ctx, _buf);
  mbedtls_md5_free(&_ctx);
  for(int i=0; i<16; i++){
    sprintf(output + i*2, "%02x", _buf[i]);
  }
  return true;
}