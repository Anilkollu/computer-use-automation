from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
import os

APP_DIR = Path(__file__).parent / "target-app"
os.chdir(APP_DIR)

server = ThreadingHTTPServer(("127.0.0.1", 3000), SimpleHTTPRequestHandler)

print("Mock Bank running at http://127.0.0.1:3000/login.html")
print("Press Ctrl+C to stop.")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nMock Bank stopped.")
    server.server_close()
