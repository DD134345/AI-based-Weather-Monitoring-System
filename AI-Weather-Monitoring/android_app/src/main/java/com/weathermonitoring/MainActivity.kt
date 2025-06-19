\AI-based-Weather-Monitoring-System\AI-Weather-Monitoring\android_app\src\main\java\com\weathermonitoring\WeatherApp.kt
package com.weathermonitoring

import android.Manifest
import android.app.Application
import android.bluetooth.BluetoothDevice
import android.os.Build
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import androidx.activity.viewModels
import androidx.appcompat.app.AlertDialog
import androidx.core.content.ContextCompat
import androidx.lifecycle.*
import com.github.mikephil.charting.charts.LineChart
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.weathermonitoring.databinding.ActivityMainBinding
import com.weathermonitoring.dialogs.BluetoothDeviceListDialog
import com.weathermonitoring.serial.UsbSerialDriver
import kotlinx.coroutines.launch

// Application class
class WeatherApp : Application() {
    companion object {
        lateinit var instance: WeatherApp private set
    }
    override fun onCreate() {
        super.onCreate()
        instance = this
    }
}

// Data model
data class WeatherData(
    val temperature: Float,
    val humidity: Float,
    val pressure: Float,
    val timestamp: Long = System.currentTimeMillis()
)

// ViewModel
class WeatherViewModel : ViewModel() {
    private val _weatherData = MutableLiveData<WeatherData>()
    val weatherData: LiveData<WeatherData> = _weatherData
    
    private val bluetoothManager by lazy { BluetoothManager(WeatherApp.instance) }
    
    fun connectToDevice(device: BluetoothDevice) = viewModelScope.launch {
        bluetoothManager.connect(device)
    }
    
    fun refreshData() = viewModelScope.launch {
        bluetoothManager.requestUpdate()
    }
    
    fun connectWifi(ipAddress: String) {
        // Implement WiFi connection logic
    }
    
    fun connectSerial() {
        // Implement Serial connection logic
    }
}

// Main Activity
class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val viewModel: WeatherViewModel by viewModels()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupObservers()
        setupRefresh()
        viewModel.connect()
    }

    private fun setupObservers() {
        viewModel.weatherData.observe(this) { data ->
            binding.apply {
                temperatureValue.text = "%.1f°C".format(data.temperature)
                humidityValue.text = "%.1f%%".format(data.humidity)
                pressureValue.text = "%.1f hPa".format(data.pressure)
                lastUpdate.text = "Last update: ${data.timestamp}"
            }
        }
    }

    private fun setupRefresh() {
        binding.swipeRefresh.setOnRefreshListener {
            viewModel.refreshData()
            binding.swipeRefresh.isRefreshing = false
        }
    }
}