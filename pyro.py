import logging, time, threading

class pyropi:
    # General variable declaration
    GPIO_map = [14,15,18,23,24,25,8,7, 2,3,4,17,27,22,10,9]
    box_id_pins = [16,20,21,12]
    box_id_output = [11,5,6,13]
    power_pin = 19
    ready_pin = 26
    imported = True
    ready = False
    box_id = 0

    def __init__(self):
        # Set up logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('pyropi')

        # Try to import the RPi GPIO library
        try:
            global GPIO
            import RPi.GPIO as GPIO
        except:
            self.log.info('Failed to import RPi.GPIO')
            self.imported = False

        # Set up the pins
        self.setup_pins()

        # Get the box id for firing purposes
        self.get_box_id()
        self.log.info('Box Id ' + str(self.box_id))

    def setup_pins(self):
        """"Set up the output and input pins and set their default values"""
        # Exit if there is no RPi library
        if not self.imported:
            return 0

        # Set the mode
        GPIO.setmode(GPIO.BCM)

        # Set up the output LED's
        # Power
        GPIO.setup(self.power_pin, GPIO.OUT)
        GPIO.output(self.power_pin, GPIO.HIGH)
        # Ready
        GPIO.setup(self.ready_pin, GPIO.OUT)
        GPIO.output(self.ready_pin, GPIO.LOW)

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

    def get_box_id(self):
        """Return the ID of the box based on switch positions"""
        # Default to box id 0
        if not self.imported:
            return 0

        # Get the actual box ID based on switches
        index = 0
        box_id = 0
        while ( index < len(self.box_id_pins)):
            # Set up the pin for input
            GPIO.setup(self.box_id_pins[index], GPIO.IN, pull_up_down=GPIO.PUD_UP)

            # Read the state of the pin
            pin_state = 1 - GPIO.input(self.box_id_pins[i])

            # Set the corresponding output pin
            GPIO.output(self.box_id_output[index], GPIO.HIGH if pin_state else GPIO.LOW)

            # Add to the box ID
            box_id = box_id + (pin_state * (2 ** index))

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
        firing_thread = threading.Thread(target=self._fire_pin, args=[pin])
        firing_thread.start()

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
