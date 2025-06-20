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
        webSocket?.send("refresh")
    }

    override fun onCleared() {
        webSocket?.close(1000, "View Model cleared")
        super.onCleared()
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