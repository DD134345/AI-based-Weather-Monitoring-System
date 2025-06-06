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
        
        setupUI()
        observeData()
        checkPermissions()
    }

    private fun setupUI() {
        setupConnectionOptions()
        setupChart()
        binding.swipeRefresh.setOnRefreshListener { viewModel.refreshData() }
    }

    private fun setupConnectionOptions() {
        binding.bluetoothChip.setOnClickListener {
            showBluetoothDevices()
        }

        binding.wifiChip.setOnClickListener {
            showWifiDialog()
        }

        binding.serialChip.setOnClickListener {
            showSerialDialog()
        }
    }

    private fun showWifiDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle("WiFi Connection")
            .setView(R.layout.dialog_wifi_connection)
            .setPositiveButton("Connect") { dialog, _ ->
                val ipAddress = (dialog as? AlertDialog)?.findViewById<TextInputEditText>(R.id.ipAddress)?.text.toString()
                viewModel.connectWifi(ipAddress)
            }
            .show()
    }

    private fun showSerialDialog() {
        // Only available when connected via USB
        if (!UsbSerialDriver.isSupported(this)) {
            Toast.makeText(this, "USB Serial connection not supported", Toast.LENGTH_SHORT).show()
            return
        }
        viewModel.connectSerial()
    }

    private fun observeData() {
        viewModel.connectionStatus.observe(this) { status ->
            binding.connectionStatus.text = status
        }

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

    private fun updateChart(data: WeatherData) {
        // Update chart with new data point
        val chart = binding.chart
        val entry = Entry(data.timestamp.toFloat(), data.temperature)
        // Add entry to dataset and notify chart
        // ... (chart update logic)
    }

    private fun checkPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            requestPermissions(
                arrayOf(
                    Manifest.permission.BLUETOOTH_SCAN,
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.ACCESS_FINE_LOCATION
                ),
                PERMISSION_REQUEST_CODE
            )
        }
    }

    private fun showBluetoothDevices() {
        if (!checkPermissions()) {
            requestPermissions()
            return
        }
        BluetoothDeviceListDialog().show(supportFragmentManager, null)
    }

    companion object {
        private const val PERMISSION_REQUEST_CODE = 123
    }
}