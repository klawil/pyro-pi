import logging, time, threading

class pyropi:
    # General variable declaration
    GPIO_map = [14,15,18,23,24,25,8,7, 2,3,4,17,27,22,10,9]
    box_id_pins = [16,20,21]
    imported = True
    box_id = 0
    log = logging.getLogger('pyropi')

    def __init__(self):
        # Try to import the RPi GPIO library
        try:
            import RPi.GPIO as GPIO
        except:
            self.log.info('Failed to import RPi.GPIO')
            self.imported = False

        # Get the box id for firing purposes
        self.get_box_id()

    def fire_pin(box, cue):
        """Fire a certain pin and cue (if on this box)"""
        print str(box) + ': ' + str(cue)

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
            pin_state = GPIO.input(self.box_id_pins[i])

            # Add to the box ID
            box_id = box_id + (pin_state * (2 ** index))

    def setup_GPIO():
        # Try to import RPi.GPIO
        try:
            import RPi.GPIO as GPIO
            imported = True
        except:
            imported = False

        # Array that maps cues to GPIO pins
        GPIO_map = [14,15,18,23,24,25,8,7, 2,3,4,17,27,22,10,9]
        box_id_pins = [16,20,21]

        # set up the GPIO if possible
        if imported:
            # Generic library setup
            GPIO.setmode(GPIO.BCM)
            GPIO.setwarnings(False)

        return GPIO_map


pyro = pyropi()
print pyro.box_id
