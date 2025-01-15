import socket
import struct
import time
import threading
import random
import os
import select

# Constants
MAGIC_COOKIE = 0xabcddcba
OFFER_MSG_TYPE = 0x2
REQUEST_MSG_TYPE = 0x3
PAYLOAD_MSG_TYPE = 0x4
BUFFER_SIZE = 8 * 1024


# Enhanced ANSI color codes for terminal output
class Colors:
    # Text Colors
    HEADER = '\033[95m'
    INFO = '\033[94m'
    SUCCESS = '\033[92m'
    WARNING = '\033[93m'
    ERROR = '\033[91m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def listen_for_offers():
    """
    Listens for broadcast UDP offers from servers and returns the first valid offer's details.
    """
    UDP_PORT = 13117
    #print(f"{Colors.INFO}{Colors.BOLD}INFO: Listening for server offers on UDP port {UDP_PORT}{Colors.RESET}")
    print(f"{Colors.INFO}{Colors.BOLD}Client started, listening for offer requests...{Colors.RESET}")

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', UDP_PORT))

        while True:
            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                if len(data) >= 9:
                    magic_cookie, msg_type, udp_port, tcp_port = struct.unpack('!IbHH', data)
                    if magic_cookie == MAGIC_COOKIE and msg_type == OFFER_MSG_TYPE:
                        print(f"{Colors.SUCCESS}INFO: Received offer from {addr[0]}:{tcp_port}{Colors.RESET}")
                        return addr[0], udp_port, tcp_port
            except struct.error:
                print(f"{Colors.WARNING}WARNING: Received an invalid packet. Ignoring...{Colors.RESET}")
            except Exception as e:
                print(f"{Colors.ERROR}ERROR: {e}{Colors.RESET}")


def tcp_download(server_ip, tcp_port, file_size, conn_id, stats):
    """
    Performs a file download over TCP and records the transfer statistics.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.connect((server_ip, tcp_port))
            sock.sendall(f"{file_size}\n".encode())

            start_time = time.time()
            received = 0

            while True:
                ready_socks, _, _ = select.select([sock], [], [], 1)
                if ready_socks:
                    data = sock.recv(BUFFER_SIZE)
                    if not data:
                        break
                    received += len(data)
                else:
                    break

            end_time = time.time()
            duration = end_time - start_time
            speed = received * 8 / duration if duration > 0 else 0
            stats.append((conn_id, duration, speed))

        except socket.error as e:
            print(f"{Colors.ERROR}ERROR: TCP connection error: {e}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.ERROR}ERROR: Unexpected error during TCP download: {e}{Colors.RESET}")


def udp_download(server_ip, udp_port, conn_id, stats, file_size):
    """
    Performs a file download over UDP and records the transfer statistics, including packet loss.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_sock:
        udp_sock.settimeout(1)
        udp_sock.bind(('', 0))

        try:
            request_packet = struct.pack('!IbQ', MAGIC_COOKIE, REQUEST_MSG_TYPE, file_size)
            udp_sock.sendto(request_packet, (server_ip, udp_port))
            print(f"{Colors.INFO}INFO: Sent UDP request to {server_ip}:{udp_port}{Colors.RESET}")
        except Exception as e:
            print(f"{Colors.ERROR}ERROR: Failed to send UDP request: {e}{Colors.RESET}")
            return

        try:
            start_time = time.time()
            received_packets = set()
            total_packets = 0

            while True:
                ready_socks, _, _ = select.select([udp_sock], [], [], 1)
                if ready_socks:
                    try:
                        data, addr = udp_sock.recvfrom(BUFFER_SIZE)
                        if len(data) >= 29:  # Updated to 29 bytes (24 + 5 for conn_id)
                            magic_cookie, msg_type, total_segments, current_segment, server_conn_id = struct.unpack('!IBQQQ', data[:29])
                            if magic_cookie == MAGIC_COOKIE and msg_type == PAYLOAD_MSG_TYPE:
                                received_packets.add(current_segment)
                                total_packets = total_segments
                                conn_id = server_conn_id  # Extract conn_id from the packet

                                if current_segment + 1 == total_segments:
                                    break
                    except socket.timeout:
                        print(f"{Colors.WARNING}WARNING: UDP timeout, no more packets received{Colors.RESET}")
                        break
                else:
                    break

            end_time = time.time()
            duration = end_time - start_time
            packets_received = len(received_packets)
            packet_loss = ((total_packets - packets_received) / total_packets) * 100 if total_packets > 0 else 100
            speed = packets_received * BUFFER_SIZE * 8 / duration if duration > 0 else 0
            stats.append((conn_id, duration, speed, 100 - packet_loss))

        except Exception as e:
            print(f"{Colors.ERROR}ERROR: Error during UDP download: {e}{Colors.RESET}")


def start_client():
    """
    Starts the client, listens for offers, and manages file transfers over TCP and UDP.
    """
    try:
        while True:
            # Listen for offers
            server_ip, udp_port, tcp_port = listen_for_offers()

            # Get file size from the user
            while True:
                try:
                    file_size = int(input(f"{Colors.BOLD}Enter file size (in bytes): {Colors.RESET}"))
                    if file_size <= 0:
                        print(f"{Colors.WARNING}WARNING: File size must be a positive number.{Colors.RESET}")
                        continue
                    break
                except ValueError:
                    print(f"{Colors.WARNING}WARNING: Invalid input. Please enter a positive number for file size.{Colors.RESET}")

            # Get number of TCP connections from the user
            while True:
                try:
                    tcp_connections = int(input(f"{Colors.BOLD}Enter number of TCP connections: {Colors.RESET}"))
                    if tcp_connections <= 0:
                        print(f"{Colors.WARNING}WARNING: Number of TCP connections must be a positive integer.{Colors.RESET}")
                        continue
                    break
                except ValueError:
                    print(f"{Colors.WARNING}WARNING: Invalid input. Please enter a positive integer.{Colors.RESET}")

            # Get number of UDP connections from the user
            while True:
                try:
                    udp_connections = int(input(f"{Colors.BOLD}Enter number of UDP connections: {Colors.RESET}"))
                    if udp_connections <= 0:
                        print(f"{Colors.WARNING}WARNING: Number of UDP connections must be a positive integer.{Colors.RESET}")
                        continue
                    break
                except ValueError:
                    print(f"{Colors.WARNING}WARNING: Invalid input. Please enter a positive integer.{Colors.RESET}")

            # Initialize statistics and threads
            tcp_stats, udp_stats, tcp_threads, udp_threads = [], [], [], []

            # Start TCP threads
            for i in range(tcp_connections):
                thread = threading.Thread(target=tcp_download, args=(server_ip, tcp_port, file_size, i + 1, tcp_stats))
                tcp_threads.append(thread)
                thread.start()

            # Start UDP threads
            for i in range(udp_connections):
                thread = threading.Thread(target=udp_download, args=(server_ip, udp_port, i + 1, udp_stats, file_size))
                udp_threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in tcp_threads + udp_threads:
                thread.join()

            # Print TCP transfer statistics
            print(f"{Colors.BOLD}{Colors.HEADER}TCP Transfer Summary:{Colors.RESET}")
            for conn_id, duration, speed in tcp_stats:
                print(
                    f"{Colors.BOLD}{Colors.SUCCESS}  Connection ID  : {conn_id}{Colors.RESET}"
                    f"\n  {Colors.SUCCESS}Duration       : {duration:.2f} seconds{Colors.RESET}"
                    f"\n  {Colors.SUCCESS}Speed          : {speed:.2f} bps{Colors.RESET}\n"
                )

            # Print UDP transfer statistics
            print(f"{Colors.BOLD}{Colors.HEADER}UDP Transfer Summary:{Colors.RESET}")
            for conn_id, duration, speed, success_rate in udp_stats:
                color = Colors.SUCCESS if success_rate >= 95 else Colors.WARNING if success_rate >= 85 else Colors.ERROR
                # print with seconds
                print(
                    f"{Colors.BOLD}{color}  Connection ID  : {conn_id}{Colors.RESET}"
                    f"\n  {color}Duration       : {duration:.2f} seconds{Colors.RESET}"
                    f"\n  {color}Speed          : {speed:.2f} bps{Colors.RESET}"
                    f"\n  {color}Success Rate   : {success_rate:.2f}%{Colors.RESET}\n"
                )
            print(f"{Colors.HEADER}INFO: All transfers complete. Listening for new offers...{Colors.RESET}\n")

    except KeyboardInterrupt:
        print(f"{Colors.ERROR}ERROR: Client interrupted. Exiting...{Colors.RESET}")
    except Exception as e:
        print(f"{Colors.ERROR}ERROR: Unexpected error: {e}{Colors.RESET}")



if __name__ == "__main__":
    start_client()


