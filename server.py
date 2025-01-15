import socket
import threading
import struct
import time
import os
import random
from select import select

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


# Configuration
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
UDP_PORT = 13117
TCP_PORT = 20000
BUFFER_SIZE = 64*1024
PAYLOAD_SIZE = 8*1024  
conn_id_counter = 0  # Global counter

server_running = threading.Event()

def get_server_ip():
    """Retrieve the server's local IP address."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]

def udp_broadcast():
    """Periodically broadcasts a UDP offer message."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        offer_message = struct.pack('!IBHH', MAGIC_COOKIE, OFFER_MSG_TYPE, UDP_PORT, TCP_PORT)
        print(f"{Colors.BOLD}{Colors.OKBLUE}Broadcasting offers on UDP port {UDP_PORT}...{Colors.ENDC}")
        while server_running.is_set():
            sock.sendto(offer_message, ('<broadcast>', UDP_PORT))
            time.sleep(1)


def handle_udp_connection():
    global conn_id_counter
    """Handles incoming UDP requests and responds with payload packets."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.bind(('', UDP_PORT))
        print(f"{Colors.OKGREEN}Listening for UDP requests on port {UDP_PORT}{Colors.ENDC}")

        while server_running.is_set():
            readable, _, _ = select([udp_sock], [], [], 1)
            for sock in readable:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if len(data) < 13:
                    continue
                cookie, msg_type, file_size = struct.unpack('!IBQ', data[:13])
                if cookie != MAGIC_COOKIE or msg_type != REQUEST_MSG_TYPE:
                    print(f"{Colors.FAIL}Invalid UDP request from {addr}{Colors.ENDC}")
                    continue

                conn_id_counter += 1  # Increment conn_id for each new request
                conn_id = conn_id_counter

                total_segments = (file_size + PAYLOAD_SIZE - 1) // PAYLOAD_SIZE
                for segment in range(total_segments):
                    header = struct.pack('!IBQQQ', MAGIC_COOKIE, PAYLOAD_MSG_TYPE, total_segments, segment, conn_id)
                    payload_data = os.urandom(PAYLOAD_SIZE - len(header))
                    sock.sendto(header + payload_data, addr)
                print(f"{Colors.OKGREEN}Completed UDP transfer to {addr} with conn_id {conn_id}{Colors.ENDC}")



def handle_tcp_connection(conn, addr):
    """Handles a single TCP connection and sends the requested file."""
    try:
        file_size_data = conn.recv(BUFFER_SIZE)
        if not file_size_data:
            return
        file_size = int(file_size_data.decode().strip())
        print(f"{Colors.OKCYAN}TCP connection from {addr}, sending {file_size} bytes...{Colors.ENDC}")

        # Limit file size to prevent overload (e.g., max 100 MB)
        if file_size > 100 * 1024 * 1024:
            print(f"{Colors.WARNING}Requested file size too large from {addr}{Colors.ENDC}")
            conn.sendall(b"ERROR: File size too large.\n")
            return

        data = os.urandom(file_size)
        conn.sendall(data)
        print(f"{Colors.OKGREEN}TCP transfer to {addr} complete{Colors.ENDC}")
    except Exception as e:
        print(f"{Colors.FAIL}Error handling TCP connection from {addr}: {e}{Colors.ENDC}")
    finally:
        conn.close()

def tcp_server():
    """Listens for incoming TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_sock:
        tcp_sock.bind(('', TCP_PORT))
        tcp_sock.listen(5)
        print(f"{Colors.OKGREEN}Listening for TCP connections on port {TCP_PORT}{Colors.ENDC}")
        while server_running.is_set():
            readable, _, _ = select([tcp_sock], [], [], 1)
            for sock in readable:
                conn, addr = sock.accept()
                threading.Thread(target=handle_tcp_connection, args=(conn, addr), daemon=True).start()

def start_server():
    """Starts the server."""
    server_running.set()
    server_ip = get_server_ip()
    print(f"{Colors.BOLD}{Colors.HEADER}Server started at {server_ip}{Colors.ENDC}")
    threading.Thread(target=udp_broadcast, daemon=True).start()
    threading.Thread(target=handle_udp_connection, daemon=True).start()
    try:
        tcp_server()
    except KeyboardInterrupt:
        print(f"{Colors.WARNING}\nShutting down server...{Colors.ENDC}")
        server_running.clear()
    finally:
        print(f"{Colors.OKGREEN}Server terminated.{Colors.ENDC}")

if __name__ == "__main__":
    start_server()
