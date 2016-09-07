import socket, threading, time, logging
from firing import get_box_id, fire_pin

# global variables
local_ip = socket.gethostbyname(socket.gethostname()) # This servers IP
servers = [] # a list of all the other firing boxes
candc_ip = "none" # C&C server IP address
port = 8000
ip_base = local_ip.split('.') # Base of the IPs to search
ip_base[3] = ''
ip_base = '.'.join(ip_base)

def parse_command(cmd, conn, addr):
    """Parse a command passed to the server"""
    # Log the command and source
    server_log.info('(%s) %s', addr[0], cmd)

    # Process the command into the usable bits
    cmd = cmd.rstrip().split(':')

    # Process the commands
    if ( cmd[0] == "are_fire" ):
        # Asking if the box is running the software
        conn.send('1')
    elif ( cmd[0] == "c+c" ):
        # Asking for the IP of the C&C server
        conn.send(candc_ip)
    elif ( cmd[0] == "trigger" ):
        # Triggering the launch script
        if ( candc_ip != local_ip ):
            # Pass the command on to the c&c server
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect_ex((candc_ip, port))
            sock.send('trigger')
            sock.close()
        conn.send('1')
    elif ( cmd[0] == "fire" ):
        fire_pin(cmd[1], cmd[2])
        conn.send('1')

    # Return the command array
    return cmd

def run_server():
    """Runs the server that accepts and responds to queries from other servers"""
    # Create the server socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Allows immediate re-use
    server.bind((socket.gethostname(), port))
    server.listen(5) # Max 5 concurrent connections

    while True:
        # Read incoming messages
        connection, address = server.accept()
        buffer = connection.recv(64)
        if ( len(buffer) > 0 ):
            # Hey! There's a message!
            if ( buffer == "quit" ):
                # Handle exiting this thread (if needed)
                connection.send('Quitting')

                # Close ALL THE SOCKETS
                server.close()
                connection.close()

                # Log the exit request
                server_log.info("Exiting at request from %s", address[0])

                # Return null, effectively killing the thread
                return

            # Parse any non-exit command
            parse_command(cmd=buffer, conn=connection, addr=address)

def find_servers():
    IP = 1
    test_servers = []
    global candc_ip, servers
    while ( IP < 255 ):
        test_ip = ip_base + '.' + str(IP)
        if ( test_ip == local_ip ):
            continue
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            result = sock.connect_ex((test_ip, port))
            if result == 0:
                test_servers.append(test_ip)
        except:
            test_ip = None
        sock.close()
        IP = IP + 1

    for IP in test_servers:
        sock = socket.socket(socket.AG_INET, socket.SOCK_STREM)
        sock.connect_ex((IP, port))
        sock.send('are_fire')
        sock_buffer = sock.recv(64)
        sock.close()
        if ( sock_buffer == "1" ):
            servers.append(IP)

    for IP in servers:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREM)
        sock.connect_ex((IP, port))
        sock.send('c+c')
        sock_buffer = sock.recv(64)
        sock.close()
        if ( len(sock_buffer) > 0 and sock_buffer != "none" ):
            candc_ip = sock_buffer
            break

    if ( candc_ip == "none" ):
        candc_ip = local_ip

logging.basicConfig(format='%(asctime)s %(levelname)s: %(name)s: %(message)s', level=logging.DEBUG, datefmt='%m/%d/%Y %I:%M:%S %p')
server_log = logging.getLogger('server')
server_thread = threading.Thread(target=run_server)
server_thread.start()

find_servers()
print servers
print candc_ip
