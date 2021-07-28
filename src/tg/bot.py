import json
from net.http_client import HttpClient
from device.air import AirCond
from settings import AIR_PIN

GET_UPDATE_TIMEOUT = 30
GET_UPDATES_LIMIT = 5


def nested_get(dic, path, default):
    next_level = dic
    for k in path:
        next_level = next_level.get(k, None)
        if next_level is None:
            return default
    return next_level


class BrainyHomeBot:
    def __init__(self, token, proto, host, port):
        self._bot_url = '/bot{token}'.format(token=token)
        self._offset = 0
        self._client = HttpClient(proto, host, port)
        self._stopped = False

        self._devices = dict({
            1: AirCond(AIR_PIN)
        })

    def handle_command(self, command):
        # TODO: We sent all commend to first device now
        device = self._devices[1]
        if device:
            return device.handle_command(command)
        return None

    def get_updates(self):
        updates = []
        url = '{bot_url}/getUpdates?limit={limit}&timeout={timeout}&offset={offset}'.format(
            bot_url=self._bot_url,
            limit=GET_UPDATES_LIMIT,
            timeout=GET_UPDATE_TIMEOUT,
            offset=self._offset,
        )

        resp = self._client.get_request(url)

        if resp['status'] != 200:
            updates = nested_get(resp, ['body', 'result'], [])

        return updates

    def send_message(self, chat_id, message, keyboard=None):
        url = '{bot_url}/sendMessage?chat_id={chat_id}&text={message}'.format(
            bot_url=self._bot_url,
            chat_id=chat_id,
            message=message,
        )

        if keyboard:
            url += '&reply_markup={}'.format(json.dumps(keyboard))

        self._client.get_request(url)

    def long_poll_updates(self):
        if self._stopped:
            return

        updates = self.get_updates()

        if len(updates) > 0:
            last_update = updates[-1]
            self._offset = last_update['update_id'] + 1
            message = None

            if 'message' in last_update:
                message = last_update['message']

            if 'edited_message' in last_update:
                message = last_update['edited_message']

            text = nested_get(message, ['text'], '')
            result = self.handle_command(text)

            chat_id = nested_get(message, ['chat', 'id'], None)
            if chat_id:
                self.send_message(chat_id, result[0], result[1])

        self.long_poll_updates()

    def run(self):
        self._stopped = False
        self.long_poll_updates()

    def stop(self):
        self._stopped = True

