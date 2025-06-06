\AI-based-Weather-Monitoring-System\AI-Weather-Monitoring\android_app\src\main\java\com\weathermonitoring\WeatherApp.kt
package com.weathermonitoring

import android.app.Application
import android.bluetooth.BluetoothDevice
import androidx.appcompat.app.AppCompatActivity
import android.os.Bundle
import androidx.activity.viewModels
import androidx.lifecycle.*
import com.github.mikephil.charting.charts.LineChart
import com.weathermonitoring.databinding.ActivityMainBinding
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
}

// Main Activity
class MainActivity : AppCompatActivity() {
    private lateinit var binding: ActivityMainBinding
    private val viewModel: WeatherViewModel by viewModels()
    private val chart by lazy { binding.chart }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        
        setupUI()
        observeData()
    }

    private fun setupUI() {
        setupChart()
        binding.fab.setOnClickListener { showBluetoothDevices() }
        binding.swipeRefresh.setOnRefreshListener { viewModel.refreshData() }
    }

    private fun setupChart() {
        chart.apply {
            description.isEnabled = false
            setTouchEnabled(true)
            setDrawGridBackground(false)
            setDrawBorders(false)
            animateX(1000)
        }
    }

    private fun observeData() {
        viewModel.weatherData.observe(this) { data ->
            updateUI(data)
            binding.swipeRefresh.isRefreshing = false
        }
    }

    private fun updateUI(data: WeatherData) {
        binding.apply {
            temperatureValue.text = getString(R.string.temperature_format, data.temperature)
            humidityValue.text = getString(R.string.humidity_format, data.humidity)
            pressureValue.text = getString(R.string.pressure_format, data.pressure)
        }
        updateChart(data)
    }

    private fun showBluetoothDevices() {
        if (!checkPermissions()) {
            requestPermissions()
            return
        }
        BluetoothDeviceListDialog().show(supportFragmentManager, null)
    }
}