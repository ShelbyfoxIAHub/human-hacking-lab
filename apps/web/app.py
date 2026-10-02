from http.server import BaseHTTPRequestHandler, HTTPServer
import os

LAB_NAME = os.getenv("LAB_NAME", "Human Hacking Lab")


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{LAB_NAME}</title>
</head>
<body>
  <h1>{LAB_NAME}</h1>
  <p>Educational portal for an isolated cybersecurity training lab.</p>
  <p>This service does not process credentials.</p>
  <ul>
    <li>Identities: synthetic</li>
    <li>Data: synthetic</li>
    <li>Scope: local lab</li>
  </ul>
</body>
</html>""".encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    HTTPServer(("0.0.0.0", 8080), Handler).serve_forever()
