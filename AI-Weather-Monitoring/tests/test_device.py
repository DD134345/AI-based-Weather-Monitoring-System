import unittest
import asyncio
from unittest.mock import Mock, patch
from src.service.device_manager import DeviceManager

class TestDeviceManager(unittest.TestCase):
    def setUp(self):
        self.device = DeviceManager()

    @patch('serial.Serial')
    async def test_serial_connection(self, mock_serial):
        # Setup mock
        mock_serial.return_value.is_open = True
        mock_serial.return_value.in_waiting = True
        mock_serial.return_value.readline.return_value = b'{"temperature": 25.0, "humidity": 60.0, "pressure": 1013.25}\n'

        # Test connection
        result = await self.device.connect('serial', port='COM3')
        self.assertTrue(result)
        
        # Test data reading
        data = await self.device.read_data()
        self.assertIsNotNone(data)
        self.assertEqual(data['temperature'], 25.0)
        self.assertEqual(data['humidity'], 60.0)
        self.assertEqual(data['pressure'], 1013.25)

    @patch('aiohttp.ClientSession')
    async def test_wifi_connection(self, mock_session):
        # Setup mock
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json.return_value = {
            'temperature': 25.0,
            'humidity': 60.0,
            'pressure': 1013.25
        }
        mock_session.return_value.__aenter__.return_value.get.return_value.__aenter__.return_value = mock_response

        # Test connection
        result = await self.device.connect('wifi', ip='192.168.4.1')
        self.assertTrue(result)
        
        # Test data reading
        data = await self.device.read_data()
        self.assertIsNotNone(data)
        self.assertEqual(data['temperature'], 25.0)
        self.assertEqual(data['humidity'], 60.0)
        self.assertEqual(data['pressure'], 1013.25)

async def run_tests():
    return unittest.main()

if __name__ == '__main__':
    asyncio.run(run_tests())