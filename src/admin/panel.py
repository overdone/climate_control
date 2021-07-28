from net.http_server import HttpServer


def get_main_page(srv, request):
    return srv.send('hello')


class AdminPanel:
    def __init__(self):
        self._server = HttpServer()
        self._server.add_route('/', get_main_page)

    def start(self):
        self._server.start()

    def stop(self):
        self._server.stop()
