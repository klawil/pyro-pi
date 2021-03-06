import logging, time, threading, socket

class pyropi:
    # General variable declaration
    GPIO_map = [14,15,18,23,24,25,8,7, 2,3,4,17,27,22,10,9]
    box_id_pins = [12,16,20,21]
    box_id_output = [5,6,13,19]
    ready_pin = 26
    button_pin = 11
    button_state = 1
    keep_watching = True
    imported = True
    ready = False
    box_id = 0
    port = None

    def __init__(self, port):
        # Set up logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.INFO, datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('pyropi')

        # Set up the port
        self.port = port

        # Try to import the RPi GPIO library
        try:
            global GPIO
            import RPi.GPIO as GPIO
        except:
            self.log.info('Failed to import RPi.GPIO')
            self.imported = False

        threading.Thread(target=self.setup).start()

    def setup(self):
        """The setup function (used for threading)"""
        # Set up the pins
        self.log.info("Setting up pins")
        self.setup_pins()

        # Start the button watching script
        threading.Thread(target=self.watch_button).start()

        # Get the box id
        self.log.info("Getting box ID")
        self.get_box_id()
        self.log.info("Box ID " + str(self.box_id))

    def setup_pins(self):
        """"Set up the output and input pins and set their default values"""
        # Exit if there is no RPi library
        if not self.imported:
            return 0

        # Set the mode
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        # Set up the ready LED
        GPIO.setup(self.ready_pin, GPIO.OUT)
        GPIO.output(self.ready_pin, GPIO.LOW)

        # Set up the push button
        GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Set up the box id input pins
        for pin in self.box_id_pins:
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        # Set up the box id output pins
        for pin in self.box_id_output:
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.LOW)

        # Set all of the firing pins
        for pin in self.GPIO_map:
            # Set up the pin for output
            GPIO.setup(pin, GPIO.OUT)
            GPIO.output(pin, GPIO.HIGH)

    def watch_button(self):
        """Watches the button for pushes"""
        # Check for GPIO library
        if not self.imported:
            return 0

        # Watch the button
        start_time = time.time()
        while self.keep_watching:
            # Get the buttons current state
            current_state = GPIO.input(self.button_pin)
            if current_state != self.button_state and current_state == 0:
                # The button is pressed and wasn't last loop
                start_time = time.time()
            elif current_state != self.button_state and time.time() - start_time >= 1:
                # The button was released and was held for longer than 1 second
                # Shut down the server
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.5)
                sock.connect(("127.0.0.1",self.port))
                sock.send("exit")
            elif current_state != self.button_state:
                # The button was released and was help for less than 1 second
                # Fire all of the cues in 1 second intervals
                threading.Thread(target=self.fire_all_pins).start()

            # Save the (possibly) new button state
            self.button_state = current_state

    def fire_all_pins(self):
        """Fire all the pins in 1 second increment"""
        for pin in self.GPIO_map:
            time.sleep(1)
            threading.Thread(target=self._fire_pin, args=[pin]).start()

    def get_box_id(self):
        """Return the ID of the box based on switch positions"""
        # Default to box id 0
        if not self.imported:
            return 0

        # Get the actual box ID based on switches
        index = 0
        box_id = 0
        while ( index < len(self.box_id_pins)):
            # Read the state of the pin
            pin_state = 1 - GPIO.input(self.box_id_pins[index])
            self.log.info('Pin ' + str(index) + ' (' + str(self.box_id_pins[index]) + '): ' + str(pin_state))

            # Set the corresponding output pin
            GPIO.output(self.box_id_output[index], GPIO.HIGH if pin_state else GPIO.LOW)

            # Add to the box ID
            box_id = box_id + (pin_state * (2 ** index))

            # Increment index
            index = index + 1

        self.box_id = box_id

    def fire_pin(self, box, cue):
        """Start a threaded function that fires the cue if needed"""
        # Check for the box id
        if int(box) != self.box_id:
            return 0

        # Get the pin to use
        try:
            pin = self.GPIO_map[int(cue) - 1]
        except:
            self.log.info("Error Finding cue " + str(cue))
            return false

        # Log that the pin is being fired
        self.log.info("Fire " + str(box) + "-" + str(cue) + " (pin " + str(pin) + ")")

        # Start the thread
        threading.Thread(target=self._fire_pin, args=[pin]).start()

    def _fire_pin(self, pin):
        """Fire a certain pin"""
        # Exit if GPIO is not imported
        if not self.imported:
            return 0

        # Fire the pin
        self.log.debug("Turning on " + str(pin))
        GPIO.output(pin, GPIO.LOW)
        time.sleep(0.1)
        self.log.debug("Turning off " + str(pin))
        GPIO.output(pin, GPIO.HIGH)

    def ready(self):
        """Turn on the ready light"""
        if not self.imported:
            return False

        GPIO.output(self.ready_pin, GPIO.HIGH)
        self.ready = True

    def blink_ready(self, times):
        """Blink the ready light a certain number of times"""
        if not self.imported:
            return False

        index = 0;
        while index < times:
            index = index + 1
            GPIO.output(self.ready_pin, GPIO.LOW)
            time.sleep(0.5)
            GPIO.output(self.ready_pin, GPIO.HIGH)
            time.sleep(0.5)

        if not self.ready:
            GPIO.output(self.ready_pin, GPIO.LOW)
