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
        
        setupToolbar()
        setupObservers()
        setupRefresh()
        setupConnectButton()
    }

    private fun setupToolbar() {
        setSupportActionBar(binding.toolbar)
        supportActionBar?.setTitle(R.string.app_name)
    }

    private fun setupObservers() {
        viewModel.weatherData.observe(this) { data ->
            updateWeatherDisplay(data)
        }

        viewModel.connectionState.observe(this) { state ->
            updateConnectionState(state)
        }

        viewModel.prediction.observe(this) { prediction ->
            binding.predictionValue.text = prediction
        }
    }

    private fun updateWeatherDisplay(data: WeatherData) {
        binding.apply {
            temperatureValue.text = getString(R.string.temperature_format, data.temperature)
            humidityValue.text = getString(R.string.humidity_format, data.humidity)
            pressureValue.text = getString(R.string.pressure_format, data.pressure)
        }
    }

    private fun updateConnectionState(state: ConnectionState) {
        when (state) {
            is ConnectionState.Connected -> {
                binding.connectFab.setImageResource(R.drawable.ic_connected)
                showSnackbar("Connected")
            }
            is ConnectionState.Disconnected -> {
                binding.connectFab.setImageResource(R.drawable.ic_connect)
                showSnackbar("Disconnected")
            }
            is ConnectionState.Error -> {
                binding.connectFab.setImageResource(R.drawable.ic_error)
                showSnackbar("Connection error: ${state.message}")
            }
        }
    }

    private fun setupRefresh() {
        binding.swipeRefresh.setOnRefreshListener {
            viewModel.refreshData()
            binding.swipeRefresh.isRefreshing = false
        }
    }

    private fun setupConnectButton() {
        binding.connectFab.setOnClickListener {
            showConnectionDialog()
        }
    }

    private fun showConnectionDialog() {
        MaterialAlertDialogBuilder(this)
            .setTitle("Connect to Device")
            .setItems(R.array.connection_methods) { _, which ->
                when (which) {
                    0 -> viewModel.connectBluetooth()
                    1 -> showWifiDialog()
                    2 -> viewModel.connectSerial()
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

    private fun showSnackbar(message: String) {
        Snackbar.make(binding.root, message, Snackbar.LENGTH_SHORT).show()
    }
}