import machine
import dht
from device.base import BaseDevice


class THSensor(BaseDevice):
    def __init__(self, pin):
        self._sensor = dht.DHT22(machine.Pin(pin))
        self._current_temp = 0
        self._current_humidity = None
        # self._measure_timer = machine.Timer(period=2000, mode=machine.Timer.PERIODIC, callback=self.measure)

    def __str__(self):
        return 'Temp: {}, Humidity: {}'\
            .format(self._current_temp, self._current_humidity)

    def measure(self):
        self._sensor.measure()
        self._current_temp = self._sensor.temperature()
        self._current_humidity = self._sensor.humidity()

    def handle_command(self, command):
        if command == '\u1f321':
            self.measure()
            return str(self), self.get_keyboard()

    def get_keyboard(self):
        return dict({
            'keyboard': [
                [{'text': '\u1f321'}],
            ]
        })
