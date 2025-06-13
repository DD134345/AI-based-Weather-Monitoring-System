class WeatherViewModel : ViewModel() {
    private val _connectionStatus = MutableLiveData<String>()
    val connectionStatus: LiveData<String> = _connectionStatus

    private val _weatherData = MutableLiveData<WeatherState>()
    val weatherData: LiveData<WeatherState> = _weatherData

    private val connectionManager = ConnectionManager()
    private var currentConnection: DeviceConnection? = null

    data class WeatherState(
        val currentWeather: WeatherData,
        val prediction: PredictionData,
        val historicalData: List<WeatherData>
    )

    data class PredictionData(
        val weatherType: String,
        val confidence: Float,
        val futureReadings: List<WeatherData>
    )

    fun connectBluetooth(device: BluetoothDevice) = viewModelScope.launch {
        currentConnection?.disconnect()
        currentConnection = BluetoothConnection(device)
        connect()
    }

    fun connectWifi(ipAddress: String) = viewModelScope.launch {
        currentConnection?.disconnect()
        currentConnection = WifiConnection(ipAddress)
        connect()
    }

    fun connectSerial() = viewModelScope.launch {
        currentConnection?.disconnect()
        currentConnection = SerialConnection()
        connect()
    }

    private suspend fun connect() {
        currentConnection?.let { connection ->
            _connectionStatus.value = "Connecting..."
            if (connection.connect()) {
                _connectionStatus.value = "Connected"
                startDataCollection()
            } else {
                _connectionStatus.value = "Connection failed"
            }
        }
    }

    private fun startDataCollection() = viewModelScope.launch {
        currentConnection?.let { connection ->
            while (connection.isConnected()) {
                connection.readData()?.let { data ->
                    _weatherData.value = data
                }
                delay(1000) // Update every second
            }
        }
    }

    fun refreshData() = viewModelScope.launch {
        currentConnection?.readData()?.let { data ->
            _weatherData.value = data
        }
    }

    fun updateWeatherDisplay() = viewModelScope.launch {
        try {
            val current = currentConnection?.readData()
            current?.let { data ->
                val historical = getHistoricalData()
                val prediction = getPrediction(data)

                _weatherData.value = WeatherState(
                    currentWeather = data,
                    prediction = prediction,
                    historicalData = historical
                )
            }
        } catch (e: Exception) {
            _connectionStatus.value = "Error: ${e.message}"
        }
    }

    private suspend fun getPrediction(currentData: WeatherData): PredictionData {
        // Implement prediction fetching logic
        return weatherRepository.getPrediction(currentData)
    }

    override fun onCleared() {
        super.onCleared()
        currentConnection?.disconnect()
    }
}

data class WeatherData(
    val temperature: Float,
    val humidity: Float,
    val pressure: Float,
    val timestamp: Long = System.currentTimeMillis()
)