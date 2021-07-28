import socket
import ssl
import json


def parse_response(response):
    fields = response.decode().split('\r\n')

    return {
        'status': fields[0].split()[1],
        'body': json.loads(fields[-1])
    }


class HttpClient:
    def __init__(self, proto, host, port):
        self._proto = proto
        self._host = host
        self._port = port

    def make_request(self, req_data):
        address = socket.getaddrinfo(self._host, self._port)[0][-1]
        s = socket.socket()

        if self._proto == 'https':
            s.connect(address)
            s = ssl.wrap_socket(s)
            s.write(req_data)
            resp = s.read(4096)
        else:
            s.connect(address)
            s.send(req_data)
            resp = s.recv(4096)

        s.close()

        return resp

    def get_request(self, url):
        data = 'GET {url} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n' \
            .format(url=url, host=self._host) \
            .encode()

        return parse_response(self.make_request(data))

    def post_request(self, url, body):
        b_body = body.encode()
        data = 'POST {url} HTTP/1.1\r\nHost: {host}\r\nContent-Length: {body_l}\r\nConnection: close\r\n\r\n{body}\r\n' \
            .format(url=url, host=self._host, body_l=len(b_body), body=b_body) \
            .encode()

        return parse_response(self.make_request(data))
