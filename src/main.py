import gc
import network

from tg.bot import ClimateControlBot
import settings

gc.collect()


def do_wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(settings.WIFI_SID, settings.WIFI_PASS)

        while not sta_if.isconnected():
            pass


def run():
    bot = ClimateControlBot(
        settings.BOT_TOKEN,
        settings.TELEGRAM_API_PROTO,
        settings.TELEGRAM_API_HOST,
        settings.TELEGRAM_API_PORT
    )
    bot.run()


do_wifi_connect()
run()
