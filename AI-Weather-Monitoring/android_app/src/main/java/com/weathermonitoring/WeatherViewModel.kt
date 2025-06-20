package com.weathermonitoring

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.google.gson.Gson
import kotlinx.coroutines.launch
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import java.util.concurrent.TimeUnit

class WeatherViewModel : ViewModel() {
    private val _weatherData = MutableLiveData<WeatherData>()
    val weatherData: LiveData<WeatherData> = _weatherData

    private val _connectionState = MutableLiveData<ConnectionState>()
    val connectionState: LiveData<ConnectionState> = _connectionState

    private val _prediction = MutableLiveData<String>()
    val prediction: LiveData<String> = _prediction

    private var webSocket: WebSocket? = null
    private val wsClient = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(10, TimeUnit.SECONDS)
        .build()

    fun connectWifi(ipAddress: String) {
        val request = Request.Builder()
            .url("ws://$ipAddress:8765")
            .build()

        webSocket = wsClient.newWebSocket(request, createWebSocketListener())
        _connectionState.value = ConnectionState.Connecting
    }

    private fun createWebSocketListener() = object : WebSocketListener() {
        override fun onOpen(webSocket: WebSocket, response: Response) {
            _connectionState.postValue(ConnectionState.Connected)
        }

        override fun onMessage(webSocket: WebSocket, text: String) {
            try {
                val data = Gson().fromJson(text, WeatherData::class.java)
                _weatherData.postValue(data)
                updatePrediction(data)
            } catch (e: Exception) {
                _connectionState.postValue(ConnectionState.Error(e.message ?: "Parse error"))
            }
        }

        override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
            _connectionState.postValue(ConnectionState.Error(t.message ?: "Connection failed"))
        }
    }

    private fun updatePrediction(data: WeatherData) {
        viewModelScope.launch {
            val prediction = when {
                data.humidity > 80 && data.pressure < 1000 -> "Heavy rain likely"
                data.humidity > 70 && data.pressure < 1010 -> "Light rain possible"
                data.humidity < 40 -> "Clear weather"
                else -> "Stable conditions"
            }
            _prediction.value = prediction
        }
    }

    fun refreshData() {
        viewModelScope.launch {
            // Simulate fetching data
            val temperature = (20..30).random().toFloat()
            val humidity = (50..70).random().toFloat()
            val pressure = (1000..1020).random().toFloat()

            _weatherData.value = WeatherData(temperature, humidity, pressure)

            // Simulate prediction
            val predictionText = when {
                temperature > 25 && humidity > 60 -> "Hot and humid"
                temperature < 20 && humidity < 50 -> "Cool and dry"
                else -> "Moderate"
            }
            _prediction.value = predictionText
        }
    }

    override fun onCleared() {
        webSocket?.close(1000, "View Model cleared")
        super.onCleared()
    }

    fun connectBluetooth() {
        viewModelScope.launch {
            _connectionState.value = ConnectionState.Connecting
            try {
                // Initialize Bluetooth connection
                // This is a placeholder - implement actual Bluetooth logic
                _connectionState.value = ConnectionState.Connected
            } catch (e: Exception) {
                _connectionState.value = ConnectionState.Error(e.message ?: "Bluetooth connection failed")
            }
        }
    }

    fun connectSerial() {
        viewModelScope.launch {
            _connectionState.value = ConnectionState.Connecting
            try {
                // Initialize Serial connection
                // This is a placeholder - implement actual Serial logic
                _connectionState.value = ConnectionState.Connected
            } catch (e: Exception) {
                _connectionState.value = ConnectionState.Error(e.message ?: "Serial connection failed")
            }
        }
    }
}

sealed class ConnectionState {
    object Connected : ConnectionState()
    object Disconnected : ConnectionState()
    object Connecting : ConnectionState()
    data class Error(val message: String) : ConnectionState()
}

data class WeatherData(
    val temperature: Float,
    val humidity: Float,
    val pressure: Float,
    val timestamp: String
)