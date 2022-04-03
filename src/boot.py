import network
import gc
import settings

gc.collect()


def do_wifi_connect():
    sta_if = network.WLAN(network.STA_IF)
    if not sta_if.isconnected():
        sta_if.active(True)
        sta_if.connect(settings.WIFI_SID, settings.WIFI_PASS)

        while not sta_if.isconnected():
            pass


do_wifi_connect()
