import socket
import threading
import struct
import time
import sys
from select import select

class Client:
    def __init__(self, file_size, tcp_amount, udp_amount):
        self.file_size = int(file_size)
        self.tcp_amount = int(tcp_amount)
        self.udp_amount = int(udp_amount)
        self.magic_cookie = 0xabcddcba
        self.offer_type = 0x2
        self.request_type = 0x3
        self.payload_type = 0x4
        self.running = True


        # Add statistics counters
        self.total_tcp_speed = 0
        self.total_udp_speed = 0
        self.tcp_transfer_count = 0
        self.udp_transfer_count = 0

    def listen_for_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind(('', 13117))
        udp_socket.settimeout(1)  # Set timeout to avoid busy-waiting
        print("\033[93mClient started, listening for offer requests...\033[0m")


        while self.running:
            try:
                ready, _, _ = select([udp_socket], [], [], 1)
                if ready:
                    data, addr = udp_socket.recvfrom(1024)
                    if len(data) == 9:
                        cookie, msg_type, udp_port, tcp_port = struct.unpack('!IBHH', data)
                        if cookie == self.magic_cookie and msg_type == self.offer_type:
                            #print(f"\033[92mReceived offer from {addr[0]}:{udp_port}\033[0m")
                            print(f"\033[92mReceived offer from {addr[0]}\033[0m")

                            self.start_speed_test(addr[0], udp_port, tcp_port)
            except KeyboardInterrupt:
                self.running = False
                print("\033[91mClient shutting down...\033[0m")
                udp_socket.close()
                sys.exit(0)

    def start_speed_test(self, server_ip, udp_port, tcp_port):
        tcp_threads = []
        udp_threads = []

        for _ in range(self.tcp_amount):
            thread = threading.Thread(target=self.tcp_transfer, args=(server_ip, tcp_port))
            tcp_threads.append(thread)
            thread.start()

        for _ in range(self.udp_amount):
            thread = threading.Thread(target=self.udp_transfer, args=(server_ip, udp_port))
            udp_threads.append(thread)
            thread.start()

        for thread in tcp_threads + udp_threads:
            thread.join()

        print("\033[93mAll transfers complete, listening to offer requests\033[0m")

        # Display average speeds after all transfers are done
        if self.tcp_transfer_count > 0:
            avg_tcp_speed = self.total_tcp_speed / self.tcp_transfer_count
            print(f"\033[96mAverage TCP speed: {avg_tcp_speed:.2f} bits/second\033[0m")

        if self.udp_transfer_count > 0:
            avg_udp_speed = self.total_udp_speed / self.udp_transfer_count
            print(f"\033[96mAverage UDP speed: {avg_udp_speed:.2f} bits/second\033[0m")

    def tcp_transfer(self, server_ip, tcp_port):


        """
        Performs a TCP transfer with the server and measures the transfer time and speed.

        Args:
            server_ip (str): Server IP address.
            tcp_port (int): Server TCP port.
        """
        start_time = time.time()
        retry_count = 3  # Retry up to 3 times on failure
        while retry_count > 0:
            try:
                with socket.create_connection((server_ip, tcp_port)) as sock:
                    sock.sendall(str(self.file_size).encode() + b'\n')
                    received_size = 0
                    while received_size < self.file_size:
                        data = sock.recv(1024)
                        if not data:
                            break
                        received_size += len(data)
                elapsed_time = time.time() - start_time
                speed = (self.file_size * 8) / elapsed_time
                #statistics
                self.total_tcp_speed += speed
                self.tcp_transfer_count += 1
                print(f"\033[92mTCP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second\033[0m")
                return
            except Exception as e:
                print(f"\033[91mTCP transfer failed: {e}, retrying...\033[0m")
                retry_count -= 1
                time.sleep(1)

        print("\033[91mTCP transfer failed after 3 retries\033[0m")

    def udp_transfer(self, server_ip, udp_port):
        """
        Performs a UDP transfer with the server, collects received segments, and calculates packet loss.

        Args:
            server_ip (str): Server IP address.
            udp_port (int): Server UDP port.
        """
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        request_message = struct.pack('!IBQ', self.magic_cookie, self.request_type, self.file_size)
        udp_socket.sendto(request_message, (server_ip, udp_port))

        start_time = time.time()
        received_segments = set()
        total_segments = 0

        while time.time() - start_time < 1:
            try:
                udp_socket.settimeout(1)
                data, _ = udp_socket.recvfrom(1024)

                if len(data) < 21:
                    print(f"\033[91mReceived malformed UDP packet (size: {len(data)} bytes)\033[0m")
                    continue  # Skip processing this packet

                # Unpack the packet with 21 bytes
                cookie, msg_type, total_segments = struct.unpack('!IBQ', data[:13])
                segment = struct.unpack('!Q', data[13:21])[0]


                if cookie == self.magic_cookie and msg_type == self.payload_type:
                    received_segments.add(segment)
            except socket.timeout:
                break
            except Exception as e:
                print(f"\033[91mError in UDP transfer: {e}\033[0m")

        elapsed_time = time.time() - start_time
        speed = (len(received_segments) * 1024 * 8) / elapsed_time
        #statistics
        self.total_udp_speed += speed
        self.udp_transfer_count += 1
        packet_loss = (1 - len(received_segments) / total_segments) * 100 if total_segments > 0 else 100
        print(f"\033[92mUDP transfer finished, total time: {elapsed_time:.2f} seconds, total speed: {speed:.2f} bits/second, packet loss: {packet_loss:.2f}%\033[0m")


if __name__ == "__main__":
    while True:
        try:
            file_size = int(input("Enter file size (in bytes): "))
            if file_size <= 0:
                print("\033[91mFile size must be a positive integer. Please try again.\033[0m")
                continue
            break
        except ValueError:
            print("\033[91mInvalid input. File size must be a positive integer.\033[0m")

    while True:
        try:
            tcp_amount = int(input("Enter number of TCP connections: "))
            if tcp_amount < 0:
                print("\033[91mNumber of TCP connections must be a non-negative integer. Please try again.\033[0m")
                continue
            break
        except ValueError:
            print("\033[91mInvalid input. Number of TCP connections must be a non-negative integer.\033[0m")

    while True:
        try:
            udp_amount = int(input("Enter number of UDP connections: "))
            if udp_amount < 0:
                print("\033[91mNumber of UDP connections must be a non-negative integer. Please try again.\033[0m")
                continue
            if tcp_amount == 0 and udp_amount == 0:
                print("\033[91mAt least one of TCP or UDP connections must be greater than zero.\033[0m")
                continue
            break
        except ValueError:
            print("\033[91mInvalid input. Number of UDP connections must be a non-negative integer.\033[0m")

    client = Client(file_size, tcp_amount, udp_amount)
    client.listen_for_offers()


