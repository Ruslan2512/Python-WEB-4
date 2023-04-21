import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import pathlib
import mimetypes
from datetime import datetime
import json
import socket
from threading import Thread

# from jinja2 import Environment, FileSystemLoader

BASE_DIR = pathlib.Path()
# env = Environment(loader=FileSystemLoader('templates'))
BUFFER = 1024
SERVER_IP = '127.0.0.1'
SERVER_PORT = 5000

def send_data_to_socket(body):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client_socket.sendto(body, (SERVER_IP, SERVER_PORT))
    client_socket.close()


class HttpHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        body = self.rfile.read(int(self.headers['Content-Length']))
        send_data_to_socket(body)
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()


    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        if pr_url.path == '/':
            self.send_html('index.html')
        elif pr_url.path == '/message':
            self.send_html('message.html')
        else:
            if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                self.send_static()
            else:
                self.send_html('error.html', 404)


    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as f:
            self.wfile.write(f.read())


    # def render_template(self, filename, status_code=200):
    #     self.send_response(status_code)
    #     self.send_header('Content-Type', 'text/html')
    #     self.end_headers()
    #     with open('blog.json', 'r', encoding='utf-8') as fd:
    #         r = json.load(fd)
    #     template = env.get_template(filename)
    #     print(template)
    #     html = template.render(blogs=r)
    #     self.wfile.write(html.encode())


    def send_static(self):
        self.send_response(200)
        mime_type= mimetypes.guess_type(self.path)
        if mime_type:
            self.send_header("Content-Type", mime_type[0])
        else:
            self.send_header("Content-Type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as f:
            self.wfile.write(f.read())


def run(server=HTTPServer, handler=HttpHandler):
    address = ('0.0.0.0', 3000)
    http_server = server(address, handler)
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        http_server.server_close()


def save_data(data):
    body = urllib.parse.unquote_plus(data.decode())
    try:
        print(body)
        payload = {key: value for key, value in [el.split('=') for el in body.split('&')]}
        print(payload)
        current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%MS")
        result_dict = {}
        print(result_dict)
        with open(BASE_DIR.joinpath('storage/data.json'), 'a', encoding='utf-8') as fa:
            result_dict[current_datetime] = payload
            json.dump(result_dict, fa, ensure_ascii=False)
    except ValueError as err:
        logging.error(f"Field parse data {body} with error {err}")
    except OSError as err:
        logging.error(f"Field write data {body} with error {err}")

def run_socket_server(ip, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server = ip, port
    server_socket.bind(server)
    try:
        while True:
            data, address = server_socket.recvfrom(BUFFER)
            save_data(data)
    except KeyboardInterrupt:
        logging.info('Socket server stopped')
    finally:
        server_socket.close()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(threadName)s %(message)s')
    STORAGE_DIR = pathlib.Path().joinpath('storage')
    FILE_STORAGE = STORAGE_DIR / 'data.json'
    if not FILE_STORAGE.exists():
        with open(FILE_STORAGE, 'a', encoding='utf-8') as fa:
            json.dump({}, fa, ensure_ascii=False)
    thread_server = Thread(target=run)
    thread_server.start()
    thread_socket = Thread(target=run_socket_server(SERVER_IP, SERVER_PORT))
    thread_socket.start()