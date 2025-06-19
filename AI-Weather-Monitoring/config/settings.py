from pathlib import Path

SYSTEM_CONFIG = {
    'connection': {
        'reconnect_attempts': 3,
        'reconnect_delay': 5,
        'timeout': 10
    },
    'data': {
        'buffer_size': 1000,
        'update_interval': 5
    },
    'validation': {
        'temperature_range': (-40, 60),
        'humidity_range': (0, 100),
        'pressure_range': (900, 1100)
    },
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(levelname)s - %(message)s',
        'date_format': '%Y-%m-%d %H:%M:%S'
    }
}