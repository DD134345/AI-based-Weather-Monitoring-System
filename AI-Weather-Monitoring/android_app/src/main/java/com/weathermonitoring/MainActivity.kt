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
        setupConnectButton()
    }

    private fun setupObservers() {
        viewModel.weatherData.observe(this) { data ->
            binding.apply {
                temperatureValue.text = getString(R.string.temperature_format, data.temperature)
                humidityValue.text = getString(R.string.humidity_format, data.humidity)
                pressureValue.text = getString(R.string.pressure_format, data.pressure)
            }
        }

        viewModel.prediction.observe(this) { prediction ->
            binding.predictionValue.text = prediction
        }

        viewModel.connectionState.observe(this) { state ->
            updateConnectionState(state)
        }
    }

    private fun setupConnectButton() {
        binding.connectFab.setOnClickListener {
            showConnectionDialog()
        }
    }

    private fun setupRefresh() {
        binding.swipeRefresh.setOnRefreshListener {
            viewModel.refreshData()
            binding.swipeRefresh.isRefreshing = false
        }
    }

    private fun showConnectionDialog() {
        val items = arrayOf("WiFi", "USB")
        MaterialAlertDialogBuilder(this)
            .setTitle("Connect to Device")
            .setItems(items) { _, which ->
                when (which) {
                    0 -> showWifiDialog()
                    1 -> viewModel.connectSerial()
                }
            }
            .show()
    }

    private fun showWifiDialog() {
        val input = EditText(this).apply {
            hint = "IP Address"
            setText("192.168.1.100")
        }

        MaterialAlertDialogBuilder(this)
            .setTitle("WiFi Connection")
            .setView(input)
            .setPositiveButton("Connect") { _, _ ->
                viewModel.connectWifi(input.text.toString())
            }
            .setNegativeButton("Cancel", null)
            .show()
    }

    private fun updateConnectionState(state: ConnectionState) {
        val (icon, message) = when (state) {
            is ConnectionState.Connected -> Pair(R.drawable.ic_connected, "Connected")
            is ConnectionState.Disconnected -> Pair(R.drawable.ic_connect, "Disconnected")
            is ConnectionState.Connecting -> Pair(R.drawable.ic_connecting, "Connecting...")
            is ConnectionState.Error -> Pair(R.drawable.ic_error, "Error: ${state.message}")
        }
        binding.connectFab.setImageResource(icon)
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
    }
}