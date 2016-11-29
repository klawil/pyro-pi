import logging, time, threading, socket
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import SocketServer, json

class S(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        self._set_headers()
        self.wfile.write(json.dumps(xmaspi.states))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()

        # Get the posted data
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        parsed_body = json.loads(post_body)

        # Get the pin to modify
        for change in parsed_body:
            response_object.append(xmaspi.toggle(change.get('pin', None), change.get('state', False)))

        self.wfile.write(json.dumps(response_object))

class xmaspi_server:
    # General variable definitions
    port = 8000
    pins = [7, 8, 25, 24, 23, 18, 15, 14]
    states = []
    imported = True

    def __init__(self):
        # Set up the logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('xmaspi')

        # Try to import the RPi GPIO library
        try:
            global GPIO
            import RPi.GPIO as GPIO
        except:
            self.log.info('Failed to import RPi.GPIO')
            self.imported = False

        # Set up the GPIO general
        if self.imported:
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

        # Set up the channels
        for pin in self.pins:
            if self.imported:
                GPIO.setup(pin, GPIO.OUT)
                GPIO.output(pin, GPIO.HIGH)
            self.states.append(False)

    def toggle(self, channel, state):
        """Turn a channel on or off"""
        # Check for the GPIO import
        if not self.imported:
            return {
                "success": False,
                "message": "RPi.GPIO is not imported"
            }

        # Check the channel
        channel = int(channel)
        if channel >= len(self.pins):
            return {
                "success": False,
                "message": "Invalid channel"
            }

        # Check the state
        if state != False and state != True:
            return {
                "success": False,
                "message": "Invalid state"
            }
        elif state:
            gpio_state = GPIO.LOW
        else:
            gpio_state = GPIO.HIGH

        self.states[channel] = state

        GPIO.output(self.pins[channel], gpio_state)

        return {
            "success": True,
            "message": "",
            "state": state,
            "channel": channel
        }

    def run(self):
        """Start the HTTP server"""
        server_address = ("", self.port)
        httpd = HTTPServer(server_address, S)
        self.log.info("Starting HTTPd")
        httpd.serve_forever()

if __name__ == "__main__":
    global xmaspi
    xmaspi = xmaspi_server()
    xmaspi.run()
