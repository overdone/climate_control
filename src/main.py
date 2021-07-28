import gc
from machine import Pin
import network

from tg.bot import BrainyHomeBot
from admin.panel import AdminPanel
import settings

gc.collect()


def do_wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(settings.WIFI_SID, settings.WIFI_PASS)

        while not sta_if.isconnected():
            pass


def create_ap():
    ap = network.WLAN(network.AP_IF)
    ap.config(essid=settings.AP_NAME)
    ap.config(max_clients=2)
    ap.active(True)


control_mode = False
bot = None
admin = None


def run_mode(control):
    global bot, admin

    if control:
        print('Run admin panel')
        if bot:
            bot.stop()

        create_ap()
        admin = AdminPanel()
        admin.start()

    else:
        print('Run bot')
        if admin:
            admin.stop()

        do_wifi_connect()
        bot = BrainyHomeBot(
            settings.BOT_TOKEN,
            settings.TELEGRAM_API_PROTO,
            settings.TELEGRAM_API_HOST,
            settings.TELEGRAM_API_PORT
        )
        bot.run()


def handle_button(pin):
    global control_mode
    control_mode = not control_mode

    run_mode(control_mode)


def run():
    config_button = Pin(4, Pin.IN, Pin.PULL_UP)
    config_button.irq(handler=handle_button, trigger=Pin.IRQ_FALLING)
    run_mode(False)


run()
