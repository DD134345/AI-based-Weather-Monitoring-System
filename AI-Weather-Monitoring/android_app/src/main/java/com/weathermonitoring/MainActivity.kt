class App : Application() {
    companion object {
        lateinit var instance: App
            private set
    }

    override fun onCreate() {
        super.onCreate()
        instance = this
    }
}

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
        binding.swipeRefresh.setOnRefreshListener { 
            viewModel.refreshData()
        }
    }

    private fun setupChart() {
        chart.apply {
            description.isEnabled = false
            setTouchEnabled(true)
            setDrawGridBackground(false)
            setDrawBorders(false)
            animateX(1000)
            legend.textColor = ContextCompat.getColor(context, R.color.textColor)
            xAxis.textColor = ContextCompat.getColor(context, R.color.textColor)
            axisLeft.textColor = ContextCompat.getColor(context, R.color.textColor)
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