import re
import socket
import sys
import io


class HttpServer:
    def __init__(self, host="0.0.0.0", port=80):
        self._host = host
        self._port = port
        self._routes = []
        self._stopped = True
        self._connect = None
        self._socket = None
        self._on_request_handler = None
        self._on_not_found_handler = None
        self._on_error_handler = None

    def start(self):
        self._stopped = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind((self._host, self._port))
        self._socket.listen()

        while not self._stopped:
            try:
                self._connect, address = self._socket.accept()
                request = self.get_request()
                if len(request) == 0:
                    self._connect.close()
                    continue
                if self._on_request_handler:
                    if not self._on_request_handler(request, address):
                        continue
                route = self.find_route(request)
                if route:
                    route["handler"](self, request)
                else:
                    self._route_not_found(request)
            except Exception as e:
                self._internal_error(e)
            finally:
                if self._connect:
                    self._connect.close()

    def stop(self):
        self._stopped = True
        if self._socket:
            self._socket.close()

    def add_route(self, path, handler, method="GET"):
        self._routes.append(
            {"path": path, "handler": handler, "method": method})

    def send(self, data):
        if self._connect is None:
            raise Exception("Can't send response, no connection instance")
        self._connect.sendall(data.encode())

    def find_route(self, request):
        lines = request.split("\r\n")
        method = re.search("^([A-Z]+)", lines[0]).group(1)
        path = re.search("^[A-Z]+\\s+(/[-a-zA-Z0-9_.]*)", lines[0]).group(1)
        for route in self._routes:
            if method != route["method"]:
                continue
            if path == route["path"]:
                return route
            else:
                match = re.search("^" + route["path"] + "$", path)
                if match:
                    print(method, path, route["path"])
                    return route

    def get_request(self, buffer_length=4096):
        return str(self._connect.recv(buffer_length), "utf8")

    def on_request(self, handler):
        self._on_request_handler = handler

    def on_not_found(self, handler):
        self._on_not_found_handler = handler

    def on_error(self, handler):
        self._on_error_handler = handler

    def _route_not_found(self, request):
        if self._on_not_found_handler:
            self._on_not_found_handler(request)
        else:
            self.send("HTTP/1.0 404 Not Found\r\n")
            self.send("Content-Type: text/plain\r\n\r\n")
            self.send("Not found")

    def _internal_error(self, error):
        if self._on_error_handler:
            self._on_error_handler(error)
        else:
            if "print_exception" in dir(sys):
                output = io.StringIO()
                sys.print_exception(error, output)
                str_error = output.getvalue()
                output.close()
            else:
                str_error = str(error)
            self.send("HTTP/1.0 500 Internal Server Error\r\n")
            self.send("Content-Type: text/plain\r\n\r\n")
            self.send("Error: " + str_error)
            print(str_error)
