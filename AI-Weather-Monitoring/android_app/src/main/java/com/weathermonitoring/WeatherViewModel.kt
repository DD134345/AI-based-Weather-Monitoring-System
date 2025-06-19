class WeatherViewModel : ViewModel() {
    private val _weatherData = MutableLiveData<WeatherData>()
    val weatherData: LiveData<WeatherData> = _weatherData

    private var webSocket: WebSocket? = null
    private val wsClient = OkHttpClient()

    fun connect() {
        val request = Request.Builder()
            .url("ws://192.168.1.100:8765")
            .build()

        webSocket = wsClient.newWebSocket(request, object : WebSocketListener() {
            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val data = Gson().fromJson(text, WeatherData::class.java)
                    _weatherData.postValue(data)
                } catch (e: Exception) {
                    Log.e("WeatherVM", "Parse error: ${e.message}")
                }
            }
        })
    }

    fun refreshData() {
        webSocket?.send("refresh")
    }

    override fun onCleared() {
        webSocket?.close(1000, "Activity closed")
        super.onCleared()
    }
}

data class WeatherData(
    val temperature: Float,
    val humidity: Float,
    val pressure: Float,
    val timestamp: String
)