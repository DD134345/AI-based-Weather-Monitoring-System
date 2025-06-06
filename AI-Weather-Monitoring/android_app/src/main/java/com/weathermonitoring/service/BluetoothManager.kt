class BluetoothManager(private val context: Context) {
    private var bluetoothGatt: BluetoothGatt? = null
    private val _weatherData = MutableLiveData<WeatherData>()
    val weatherData: LiveData<WeatherData> = _weatherData

    private val gattCallback = object : BluetoothGattCallback() {
        override fun onCharacteristicChanged(
            gatt: BluetoothGatt,
            characteristic: BluetoothGattCharacteristic,
            value: ByteArray
        ) {
            val jsonString = String(value)
            parseWeatherData(jsonString)?.let {
                _weatherData.postValue(it)
            }
        }
    }

    fun connect(device: BluetoothDevice) {
        device.connectGatt(context, false, gattCallback)
    }

    private fun parseWeatherData(jsonString: String): WeatherData? {
        return try {
            Gson().fromJson(jsonString, WeatherData::class.java)
        } catch (e: Exception) {
            null
        }
    }
}