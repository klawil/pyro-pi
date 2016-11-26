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
        self.wfile.write(json.dumps(GPIO_Pins))

    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        self._set_headers()

        # Get the posted data
        content_len = int(self.headers.getheader('content-length', 0))
        post_body = self.rfile.read(content_len)
        parsed_body = json.loads(post_body)

        # Get the pin to modify
        pin = parsed_body.get('pin', False)
        if pin == False or GPIO_Pins.get(pin, None) == None:
            self.wfile.write(json.dumps({"success": False, "message": "Invalid pin provided", "pin": pin}))
            return False

        # Get the state to set the pin to
        state = parsed_body.get('state', False)
        if state != False and state != True:
            self.wfile.write(json.dumps({"success": False, "message": "Invalid state provided"}))
            return False
        elif state and GPIO_Imported:
            gpio_state = GPIO.LOW
        elif GPIO_Imported:
            gpio_state = GPIO.HIGH
        GPIO_Pins[pin] = state

        if GPIO_Imported:
            GPIO.output(pin, gpio_state)

        # Doesn't do anything with posted data
        self.wfile.write(json.dumps({"success": True}))

def run(server_class=HTTPServer, handler_class=S, port=8000):
    # Set up the logging
    global xmas_log
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
    xmas_log = logging.getLogger('xmaspi')

    # Set up the CPIO
    global GPIO
    global GPIO_Pins
    GPIO_Pins = {14:False, 15:False, 18:False, 23:False, 24:False, 25:False, 8:False, 7:False}
    global GPIO_States
    GPIO_States = [False, False, False, False, False, False, False, False]
    global GPIO_Imported
    GPIO_Imported = False
    try:
        import RPi.GPIO as GPIO
        GPIO_Imported = True

        # Setup all the pins
        for pin in self.GPIO_Pins:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)
    except:
        xmas_log.info("Failed to import RPi.GPIO")

    # Start the server
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    xmas_log.info("Starting HTTPd")
    httpd.serve_forever()

if __name__ == "__main__":
    from sys import argv

    if len(argv) == 2:
        run(port=int(argv[1]))
    else:
        run()
