class SerialConnection:
    def __init__(self):
        self.connected = False

    def connect(self) -> bool:
        # TODO: Implement actual serial connection logic
        self.connected = True
        return True

    def disconnect(self) -> bool:
        self.connected = False
        return True

    def read_data(self) -> dict:
        # TODO: Implement actual data reading logic
        return {"temperature": 0, "humidity": 0}