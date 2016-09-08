import socket, threading, time, logging, fcntl, struct
from pyro import pyropi

class pyropi_server:
    # General variable definitions
    port = 8000
    pi_boxes = []
    ip_base = None
    local_ip = None
    candc_ip = None
    keep_server = True

    def __init__(self):
        # Set up logging
        logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
        self.log = logging.getLogger('server')

        # Get the local IP address
        self.get_ip_addr()
        self.log.info('IP Address: ' + str(self.local_ip))

        # Make the base ip
        self.ip_base = ".".join(self.local_ip.split(".")[:3]) + "."

        # Add a pyropi object
        self.pyropi = pyropi()

        # Start the server
        server_thread = threading.Thread(target=self.run_server)
        server_thread.start()

        # Kick off the thread that looks for the c&c server
        candc_thread = threading.Thread(target=self.find_candc)
        candc_thread.start()

    def get_ip_addr(self):
        """Obtain the IP address to identify as"""
        # Try to get wlan0
        try:
            self.local_ip = self.get_ip_from_if('wlan0')
            return
        except:
            pass

        # Try to get eth0
        try:
            self.local_ip = self.get_ip_from_if('eth0')
            return
        except:
            pass

        # Get the IP associated with the hostname
        self.local_ip = socket.gethostbyname(socket.gethostname())

    def get_ip_from_if(self, ifname):
        """Attempts to return the IP address associated with the given interface"""
        # Create the socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, stuct.pack('256s', ifname[:15]))[20:24])

    def find_candc(self):
        """Look for the c&c server using multiple threads"""
        # Build an array of threads to use to scan
        IP = 1
        threads = []
        while ( IP < 255 ):
            # Create the test IP and a thread
            test_ip = self.ip_base + str(IP)
            IP = IP + 1
            if ( test_ip == self.local_ip ):
                continue
            threads.append(threading.Thread(target=self.test_candc_ip, args=[test_ip]))

        # Add a handled attribute to all of the threads
        for thread in threads:
            thread.handled = False
            thread.started = False

        # Variables for starting threads
        max_threads = 150
        while self.candc_ip == None:
            index = -1
            active_threads = 0
            all_done = True
            while index < len(threads) - 1:
                index = index + 1
                if threads[index].started and (not threads[index].isAlive()):
                    # Thread has finished executing
                    threads[index].handled = True
                elif (not threads[index].started) and active_threads < max_threads:
                    # Thread has not been started and we can start more
                    all_done = False
                    active_threads = active_threads + 1
                    threads[index].started = True
                    threads[index].start()
                elif threads[index].started and threads[index].isAlive():
                    # The thread is still running
                    all_done = False
                    active_threads = active_threads + 1
            if all_done:
                break

        # Check for a valid c&c ip
        if self.candc_ip == None:
            self.log.info("No C&C server, becoming C&C")
            self.candc_ip = self.local_ip

        # Send a message to the c&c server to add our IP to the list
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((self.candc_ip, self.port))
        sock.send('add_me')
        buffer = sock.recv(1024)
        sock.close()

    def test_candc_ip(self, IP):
        """Determines if an IP is the c&c server"""
        # Check for a c&c IP
        if self.candc_ip != None:
            return False

        # Build the socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)

        # Try to connect
        try:
            result = sock.connect_ex((IP, self.port))
            sock.close()
            if result != 0:
                return False
        except:
            return False

        # See if the server is a firing box
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        sock.connect((IP, self.port))
        sock.send('are_fire')
        loop = 0
        buffer = sock.recv(64)
        if ( len(buffer) == 0 or buffer != "1" ):
            sock.close()
            return False

        # See if the server knows who the c&c server is
        sock.send('c+c')
        buffer = sock.recv(64)
        if ( len(buffer) != 0 and buffer != "none" and self.candc_ip == None ):
            # Save the c&c IP if there isn't already one saved and if the server gave one
            self.candc_ip = buffer

        sock.send('exit')
        sock.close()

        return False

    def run_server(self):
        """Run a socket server that accepts and responds to commands"""
        # Create the server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows immediate re-use
        server.bind(("0.0.0.0", self.port))
        server.listen(10)

        while self.keep_server:
            # Read an incoming message
            connection, address = server.accept()
            buffer = connection.recv(1024)
            if ( len(buffer) > 0 ):
                # Pass the message to the parsing function
                self.log.info("%s: %s", address[0], buffer)
                try:
                    response = self.parse_command(buffer, address)
                except:
                    response = "Exception"
                connection.send(response)

            connection.close()

        # Kill the server socket
        server.close()

        return False

    def parse_command(self, command, address):
        """Parse and execute a command"""
        # Split the command to parse
        command = command.split(':')
        ## Control Commands
        if ( command[0] == "exit" ):
            # Exit the server
            self.keep_server = False
            return "Exiting"
        elif ( command[0] == "add_me" ):
            # Add the server to the list of servers
            self.pi_boxes.append(address[0])
            return "Success"
        ## Signalling
        elif ( command[0] == "fire_cue" ):
            # Send the fire command to all of the boxes
            self.fire_all(command)
            return "Success"
        ## Fire Control
        elif ( command[0] == "fire" ):
            # Fire a box and trigger
            self.pyropi.fire_pin(command[1], command[2])
            return "Success"

        return "NotFound"

    def fire_all(self, command):
        """Start the threads to send a fire command to all boxes"""
        # Build the commands
        command[0] = "fire"
        command = ":".join(command)

        # Build the threads
        threads = []
        for IP in self.pi_boxes:
            threads.append(threading.Thread(target=self._send_command, args=(IP, command)))

        # Start the threads
        for thread in threads:
            thread.start()

    def _send_command(self, IP, command):
        """Send a command to a specific box"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        sock.connect((IP, self.port))
        sock.send(command)
        buffer = sock.recv(1024)
        sock.close()

serv = pyropi_server()
