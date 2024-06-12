import http.server
import socketserver
import requests
from queue import Queue
import json


servers = ["http://localhost:5000", "http://localhost:5001", "http://localhost:5002"]

server_queue = Queue()
for server in servers:
    server_queue.put(server)

class LoadBalancerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        server = server_queue.get()
        try:
            response = requests.get(f"{server}{self.path}")
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except requests.RequestException as e:
            self.send_error(502, f"Bad Gateway: {e}")
        server_queue.put(server)

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        server = server_queue.get()
        try:
            headers = {key: value for key, value in self.headers.items()}
            print(f"{server}{self.path}")
            response = requests.post(f"{server}{self.path}", data=post_data, headers=headers)
            self.send_response(response.status_code)
            for key, value in response.headers.items():
                self.send_header(key, value)
            self.end_headers()
            self.wfile.write(response.content)
        except requests.RequestException as e:
            self.send_error(502, f"Bad Gateway: {e}")
        server_queue.put(server)

PORT = 8080
handler = LoadBalancerHandler

with socketserver.TCPServer(("", PORT), handler) as httpd:
    print(f"Serving at port {PORT}")
    httpd.serve_forever()
