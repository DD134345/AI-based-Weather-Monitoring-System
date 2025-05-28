import 'package:flutter/material.dart';
import '../services/device_service.dart';

class HomeScreen extends StatefulWidget {
  @override
  _HomeScreenState createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final DeviceService _deviceService = DeviceService();
  Map<String, dynamic>? _weatherData;
  String _connectionStatus = 'Disconnected';

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Weather Monitor'),
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: _showConnectionDialog,
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_weatherData == null) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text('Status: $_connectionStatus'),
            SizedBox(height: 20),
            ElevatedButton(
              onPressed: _showConnectionDialog,
              child: Text('Connect to Device'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _refreshData,
      child: ListView(
        padding: EdgeInsets.all(16),
        children: [
          _buildWeatherCard(),
        ],
      ),
    );
  }

  Widget _buildWeatherCard() {
    return Card(
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          children: [
            Text(
              'Current Weather',
              style: Theme.of(context).textTheme.headline6,
            ),
            SizedBox(height: 16),
            _buildWeatherRow('Temperature', '${_weatherData!['temperature']}°C'),
            _buildWeatherRow('Humidity', '${_weatherData!['humidity']}%'),
            _buildWeatherRow('Pressure', '${_weatherData!['pressure']} hPa'),
          ],
        ),
      ),
    );
  }

  Widget _buildWeatherRow(String label, String value) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text(value, style: TextStyle(fontWeight: FontWeight.bold)),
        ],
      ),
    );
  }

  Future<void> _refreshData() async {
    final data = await _deviceService.readData();
    if (data != null) {
      setState(() => _weatherData = data);
    }
  }

  Future<void> _showConnectionDialog() async {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Connect to Device'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              title: Text('Bluetooth'),
              leading: Icon(Icons.bluetooth),
              onTap: () => _connect('bluetooth'),
            ),
            ListTile(
              title: Text('WiFi'),
              leading: Icon(Icons.wifi),
              onTap: () => _connect('wifi'),
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _connect(String type) async {
    Navigator.pop(context);
    setState(() => _connectionStatus = 'Connecting...');
    
    final connected = await _deviceService.connect(type);
    setState(() => _connectionStatus = connected ? 'Connected' : 'Connection failed');
    
    if (connected) {
      _startDataStream();
    }
  }

  void _startDataStream() {
    _deviceService.dataStream.listen(
      (data) => setState(() => _weatherData = data),
      onError: (error) => setState(() => _connectionStatus = 'Error: $error'),
    );
  }
}