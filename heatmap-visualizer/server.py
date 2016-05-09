import SimpleHTTPServer
import SocketServer
import os
import json


PORT = 8080

Handler = SimpleHTTPServer.SimpleHTTPRequestHandler

class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):

  def _write_headers(self):
    self.send_response(200)
    self.send_header('Content-type', 'application/json')
    self.end_headers()

  def do_GET(self):

    if self.path == "/maps":
      self._write_headers()
      maps = json.dumps(os.listdir("./maps"))
      self.wfile.write(maps)

    elif self.path.startswith("/maps") and not self.path.endswith(".json"):
      self._write_headers()
      maps = json.dumps([self.path + "/" + f for f in os.listdir("." + self.path)])
      self.wfile.write(maps)

    else:
      return SimpleHTTPServer.SimpleHTTPRequestHandler.do_GET(self)


class Server(SocketServer.TCPServer):
  #address_family = socket.AF_INET
  allow_reuse_address = True

server = Server(("", PORT), Handler)

print "Serving at port", PORT

try:
  server.serve_forever()
except KeyboardInterrupt:
  server.shutdown()
