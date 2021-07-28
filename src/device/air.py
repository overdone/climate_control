from machine import Pin
from esp32 import RMT

from base import BaseDevice
from utils import str_rjust, str_reverse

ON_PULSE = (428, 1280)  # ON ms, OFF ms
OFF_PULSE = (428, 428)
FRAME_HEADER = (3650, 1623)
FRAME_FOOTER = (428, 29428)

MIN_TEMP = 18
MAX_TEMP = 32

FAN_MODE = [
    {'name': 'MANUAL', 'value': 2},
    {'name': 'AUTOMATIC', 'value': 0xa},
    {'name': 'SILENT', 'value': 0xb},
]

AC_MODE = [
    {'name': 'AUTO', 'value': 0},
    {'name': 'DRY', 'value': 2},
    {'name': 'COOL', 'value': 3},
    {'name': 'HEAT', 'value': 4},
    {'name': 'FAN', 'value': 6},
]

TIMER_MODE = {
    'OFF': 0,
    'ON': 1
}


def get_checksum(frame):
    return sum(frame) & 0xff


def to_pulses(data):
    binary = str_reverse(''.join(reversed([str_rjust(bin(c)[2:], 8, '0') for c in data])))

    pulses = []
    for b in binary:
        pulses.extend(ON_PULSE if int(b) else OFF_PULSE)

    return pulses


class AirCond(BaseDevice):
    def __init__(self, pin):
        self._pin = pin
        self._rmt = RMT(0, pin=Pin(pin), clock_div=80, carrier_freq=38000,
                        carrier_duty_percent=50)

        self._temperature = 22  # default temp value
        self._power = False  # False - Off, True - On
        self._fan_mode = 2
        self._ac_mode = 2
        self._fanSpeed = 1
        self._swing = False
        self._eco = False
        self._comfort = False
        self._powerful = False
        self._timer = None
        self._timer_duration = 0
        self._frames = []

    def __str__(self):
        power_state = 'Вкл.' if self._power else 'Выкл.'
        powerful_state = 'Вкл.' if self._powerful else 'Выкл.'
        speed_state = 'Скорость: {}'.format(self._fanSpeed) if self._fan_mode == 0 else ''
        swing_state = 'Да' if self._swing else "Нет"
        comfort_state = 'Вкл.' if self._comfort else "Выкл."

        txt = '''
            Кондиционер {}
            Powerful: {}
            Режим: {}
            Вентилятор: {} {}
            Температура: {}
            Движение створки: {}
            Комфортный режим: {}
        '''.format(
            power_state,
            powerful_state,
            AC_MODE[self._ac_mode]['name'],
            FAN_MODE[self._fan_mode]['name'],
            speed_state,
            self._temperature,
            swing_state,
            comfort_state
        ).replace('\n', '%0A')

        return txt

    def build_frame_1(self):
        frame = [0x11, 0xda, 0x27, 0x00, 0xc5, 0x00, 0x10 if self._comfort else 0x00]
        frame.append(get_checksum(frame))

        self._frames = frame

        return frame

    def build_frame_2(self):
        frame = [0x11, 0xda, 0x27, 0x00, 0x42, 0x00, 0x00]
        frame.append(get_checksum(frame))

        self._frames.extend(frame)

        return frame

    def build_frame_3(self):
        frame = [0x00] * 19
        frame[0] = 0x11
        frame[1] = 0xda
        frame[2] = 0x27

        # Mode, On-off, timers
        frame[5] = (AC_MODE[self._ac_mode]['value'] << 4) | 0x08
        if self._power:
            frame[5] = frame[5] | 0x01
        if self._timer is not None:
            if self._timer == TIMER_MODE['OFF']:
                frame[5] = frame[5] | 0x04
            elif self._timer == TIMER_MODE['ON']:
                frame[5] = frame[5] | 0x02

        # Temperature
        frame[6] = self._temperature * 2

        # Fan Swing
        if self._fan_mode == 0:  # Manual mode
            frame[8] = FAN_MODE[0]['value'] + self._fanSpeed << 4
        else:
            frame[8] = FAN_MODE[self._fan_mode]['value'] << 4
        if self._swing:
            frame[8] = frame[8] | 0x0f

        # Timer Delay
        frame[10] = 0x00
        frame[11] = 0x00
        frame[12] = 0x00
        frame[11] = frame[11] | 0x06
        frame[12] = frame[12] | 0x60

        if self._timer == TIMER_MODE['OFF']:
            dur_min = self._timer_duration * 60
            if dur_min > 0xff:
                frame[12] = dur_min >> 8
                frame[11] = dur_min & 0xff
            else:
                frame[12] = dur_min >> 4
                frame[11] = frame[11] | (dur_min & 0x0f) << 4

        elif self._timer == TIMER_MODE['ON']:
            dur_min = self._timer_duration * 60
            frame[10] = dur_min & 0xff
            frame[11] = (dur_min >> 8) & 0xff

        # Powerful
        frame[13] = 1 if self._powerful else 0

        # Fixed
        frame[15] = 0xc1

        # Eco mode
        frame[16] = 0x80
        if self._eco:
            frame[16] = frame[16] | 0x04

        frame[18] = get_checksum(frame)

        self._frames = frame

        return frame

    def transmit(self):
        frame1 = to_pulses(self.build_frame_1())
        frame2 = to_pulses(self.build_frame_2())
        frame3 = to_pulses(self.build_frame_3())

        pulses = list()
        pulses.extend(OFF_PULSE * 5)  # header
        pulses.extend(FRAME_FOOTER)
        pulses.extend(FRAME_HEADER)
        pulses.extend(frame1)
        pulses.extend(FRAME_FOOTER)
        pulses.extend(FRAME_HEADER)
        pulses.extend(frame2)
        pulses.extend(FRAME_FOOTER)
        pulses.extend(FRAME_HEADER)
        pulses.extend(frame3)
        pulses.extend(FRAME_FOOTER)

        self._rmt.write_pulses(tuple(pulses))

    def handle_command(self, command):
        transmit = True

        if command == '\u23fb':
            self._power = not self._power
        elif command == '\u26a1':
            self._powerful = not self._powerful
        elif command == '\u2795':
            self._temperature += 0 if self._temperature == MAX_TEMP else 1
        elif command == '\u2796':
            self._temperature -= 0 if self._temperature == MIN_TEMP else 1
        elif command == 'mode':
            if self._ac_mode == len(AC_MODE) - 1:
                self._ac_mode = 0
            else:
                self._ac_mode = self._ac_mode + 1
        elif command == 'fan':
            if self._fan_mode == 0:
                if self._fanSpeed < 5:
                    self._fanSpeed += 1
                else:
                    self._fanSpeed = 1
                    self._fan_mode += 1
            else:
                if self._fan_mode == len(FAN_MODE) - 1:
                    self._fan_mode = 0
                else:
                    self._fan_mode += 1
        elif command == 'comfort':
            self._comfort = not self._comfort
        elif command == 'swing':
            self._swing = not self._swing
        elif command == '\u24d8':
            transmit = False
        else:
            return 'FAIL: Command {} not found'.format(command), self.get_keyboard()

        if transmit:
            self.transmit()

        return str(self), self.get_keyboard()

    def get_keyboard(self):
        return dict({
            'keyboard': [
                [{'text': '\u23fb'}],
                [{'text': '\u26a1'}],
                [
                    {'text': '\u2796'},
                    {'text': '\u2795'},
                ],
                [
                    {'text': 'mode'},
                    {'text': 'fan'},
                ],
                [
                    {'text': 'comfort'},
                    {'text': 'swing'},
                ],
                [{'text': '\u24d8'}]
            ]
        })
