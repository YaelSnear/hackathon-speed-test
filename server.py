import socket
import threading
import struct
import time
import sys
from select import select

class Server:
    def __init__(self, ip, udp_port, tcp_port):
        self.ip = ip
        self.udp_port = udp_port
        self.tcp_port = tcp_port
        self.magic_cookie = 0xabcddcba
        self.offer_type = 0x2
        self.running = True

    def send_offers(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        offer_message = struct.pack('!IBHH', self.magic_cookie, self.offer_type, self.udp_port, self.tcp_port)
        print(f"\033[92mServer started, listening on IP address {self.ip}\033[0m")

        while self.running:
            udp_socket.sendto(offer_message, ('<broadcast>', self.udp_port))
            time.sleep(1)

    def handle_tcp_connection(self, conn, addr):
        print(f"\033[94mTCP connection established with {addr}\033[0m")
        try:
            data = conn.recv(1024)
            if data:
                file_size = int(data.decode().strip())
                conn.sendall(b'0' * file_size)
        except Exception as e:
            print(f"\033[91mError handling TCP connection: {e}\033[0m")
        finally:
            conn.close()

    # def handle_udp_requests(self, udp_socket):
    #     """
    #     Handles incoming UDP requests using select() for non-blocking I/O.
    #     """
    #     udp_socket.settimeout(1)  # Set timeout to avoid blocking forever
    #     while self.running:
    #         try:
    #             ready, _, _ = select([udp_socket], [], [], 1)  # Use select for non-busy waiting
    #             if ready:
    #                 data, addr = udp_socket.recvfrom(1024)
    #                 if len(data) == 13:
    #                     cookie, msg_type, file_size = struct.unpack('!IBQ', data)
    #                     if cookie == self.magic_cookie and msg_type == 0x3:
    #                         print(f"\033[94mReceived UDP request from {addr}\033[0m")
    #                         total_segments = file_size // 1024
    #                         for segment in range(total_segments):
    #                             if segment % 10 != 0:  # Simulate 10% packet loss
    #                                 payload = struct.pack('!IBQQ', self.magic_cookie, 0x4, total_segments, segment) + b'0' * 1024
    #                                 udp_socket.sendto(payload, addr)
    #                         print(f"\033[92mCompleted UDP transfer to {addr}\033[0m")
    #                 else:
    #                     print(f"\033[91mUnexpected UDP packet size: {len(data)} bytes\033[0m")
    #         except socket.timeout:
    #             continue
    #         except Exception as e:
    #             print(f"\033[91mError handling UDP request: {e}\033[0m")

    # def handle_udp_requests(self, udp_socket):
    #     """
    #     Handles incoming UDP requests using select() for non-blocking I/O.
    #     """
    #     udp_socket.settimeout(1)  # Set timeout to avoid blocking forever
    #     while self.running:
    #         try:
    #             ready, _, _ = select([udp_socket], [], [], 1)  # Use select for non-busy waiting
    #             if ready:
    #                 data, addr = udp_socket.recvfrom(1024)
    #                 if len(data) >= 9:  # Check if the packet has at least the minimum required length
    #                     cookie, msg_type, file_size = struct.unpack('!IBQ', data[:13])  # Unpack only the first 13 bytes
    #                     if cookie == self.magic_cookie and msg_type == 0x3:
    #                         print(f"\033[94mReceived UDP request from {addr}\033[0m")
    #                         total_segments = file_size // 1024
    #                         for segment in range(total_segments):
    #                             if segment % 10 != 0:  # Simulate 10% packet loss
    #                                 payload = struct.pack('!IBQQ', self.magic_cookie, 0x4, total_segments,
    #                                                       segment) + b'0' * 1024
    #                                 udp_socket.sendto(payload, addr)
    #                         print(f"\033[92mCompleted UDP transfer to {addr}\033[0m")
    #                 else:
    #                     print(f"\033[91mReceived incomplete or malformed UDP packet ({len(data)} bytes)\033[0m")
    #         except socket.timeout:
    #             continue
    #         except Exception as e:
    #             print(f"\033[91mError handling UDP request: {e}\033[0m")

    # def handle_udp_requests(self, udp_socket):
    #     """
    #     Handles incoming UDP requests using select() for non-blocking I/O.
    #     """
    #     #udp_socket.settimeout(1)  # Set timeout to avoid blocking forever
    #     while self.running:
    #         try:
    #             ready, _, _ = select([udp_socket], [], [], 1)  # Use select for non-busy waiting
    #             if ready:
    #                 data, addr = udp_socket.recvfrom(1024)
    #
    #                 # Check if the packet size is at least 13 bytes
    #                 if len(data) < 5:  #empty packet / not good
    #                     print(f"\033[91mReceived incomplete or malformed UDP packet ({len(data)} bytes)\033[0m")
    #                     continue  # Skip processing this packet
    #
    #                 # Unpack the first 13 bytes of the packet
    #                 #cookie, msg_type, file_size = struct.unpack('!IQ', data[:13])
    #                 cookie, msg_type = struct.unpack('!Ib', data[:5]) #meta data
    #                 file_size = struct.unpack('!Q', data[5:13])[0] # file content
    #
    #                 if cookie == self.magic_cookie and msg_type == 0x3:
    #                     print(f"\033[94mReceived UDP request from {addr}\033[0m")
    #                     total_segments = file_size // 1024
    #                     for segment in range(total_segments):
    #                         if segment % 10 != 0:  # Simulate 10% packet loss
    #                             payload = struct.pack('!IBQQ', self.magic_cookie, 0x4, total_segments,
    #                                                   segment) + b'0' * 1024
    #                             udp_socket.sendto(payload, addr)
    #                     print(f"\033[92mCompleted UDP transfer to {addr}\033[0m")
    #                 else:
    #                     print(f"\033[91mInvalid UDP request from {addr}\033[0m")
    #
    #         #except socket.timeout:
    #          #   continue
    #         except Exception as e:
    #             print(f"\033[91mError handling UDP request: {e}\033[0m")

    # def handle_udp_requests(self, udp_socket):
    #     """
    #     Handles incoming UDP requests using select() for non-blocking I/O.
    #     """
    #     BUFFER_SIZE = 2048  # Set a buffer size large enough to handle complete packets
    #     while self.running:
    #         try:
    #             ready, _, _ = select([udp_socket], [], [], 1)  # Use select for non-busy waiting
    #             if ready:
    #                 data, addr = udp_socket.recvfrom(BUFFER_SIZE)  # Use the buffer size here
    #
    #                 # Check if the packet size is at least 13 bytes
    #                 if len(data) < 13:  # Check for minimum valid packet size
    #                     print(f"\033[91mReceived incomplete or malformed UDP packet ({len(data)} bytes)\033[0m")
    #                     continue  # Skip processing this packet
    #
    #                 # Unpack the first 13 bytes of the packet
    #                 cookie, msg_type, file_size = struct.unpack('!IBQ', data[:13])  # Correct unpacking for 13 bytes
    #
    #                 if cookie == self.magic_cookie and msg_type == 0x3:
    #                     print(f"\033[94mReceived UDP request from {addr}\033[0m")
    #                     total_segments = file_size // 1024
    #                     for segment in range(total_segments):
    #                         if segment % 10 != 0:  # Simulate 10% packet loss
    #                             payload = struct.pack('!IBQQ', self.magic_cookie, 0x4, total_segments,
    #                                                   segment) + b'0' * 1024
    #                             udp_socket.sendto(payload, addr)
    #                     print(f"\033[92mCompleted UDP transfer to {addr}\033[0m")
    #                 else:
    #                     print(f"\033[91mInvalid UDP request from {addr}\033[0m")
    #
    #         except Exception as e:
    #             print(f"\033[91mError handling UDP request: {e}\033[0m")

    def handle_udp_requests(self, udp_socket):
        """
        Handles incoming UDP requests using select() for non-blocking I/O.
        """
        BUFFER_SIZE = 1024  # Set a buffer size large enough to handle complete packets
        while self.running:
            try:
                ready, _, _ = select([udp_socket], [], [], 1)  # Use select for non-busy waiting
                if ready:
                    data, addr = udp_socket.recvfrom(BUFFER_SIZE)  # Use the buffer size here

                    # Check if the packet size is at least 13 bytes
                    if len(data) < 13:  # Check for minimum valid packet size
                        #print(f"\033[91mReceived incomplete or malformed UDP packet ({len(data)} bytes)\033[0m")
                        continue  # Skip processing this packet

                    # Unpack the first 13 bytes of the packet
                    cookie, msg_type, file_size = struct.unpack('!IBQ', data[:13])  # Correct unpacking for 13 bytes

                    # Check if cookie and message type are valid
                    if cookie != self.magic_cookie or msg_type != 0x3:
                        print(f"\033[91mInvalid packet received (cookie: {hex(cookie)}, msg_type: {msg_type})\033[0m")
                        continue  # Skip processing this packet

                    # If valid, proceed with handling the request
                    print(f"\033[94mReceived UDP request from {addr}\033[0m")
                    total_segments = file_size // 1024
                    for segment in range(total_segments):
                        if segment % 10 != 0:  # Simulate 10% packet loss
                            payload = struct.pack('!IBQQ', self.magic_cookie, 0x4, total_segments,
                                                  segment) + b'0' * 1024
                            udp_socket.sendto(payload, addr)
                    print(f"\033[92mCompleted UDP transfer to {addr}\033[0m")

            # except Exception as e:
            #     print(f"\033[91mError handling UDP request: {e}\033[0m")

            except OSError:
                if not self.running:
                    break  # Exit cleanly if the socket is closed during shutdown
            except Exception as e:
                if not self.running:
                    break  # Suppress further errors if shutting down
                print(f"\033[91mError handling UDP request: {e}\033[0m")

    # def start(self):
    #     udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    #     udp_socket.bind((self.ip, self.udp_port))
    #     udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #
    #     tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #     tcp_socket.bind((self.ip, self.tcp_port))
    #     tcp_socket.listen(5)
    #
    #     threading.Thread(target=self.send_offers).start()
    #     threading.Thread(target=self.handle_udp_requests, args=(udp_socket,)).start()
    #
    #     while self.running:
    #         try:
    #             ready, _, _ = select([tcp_socket], [], [], 1)  # Use select to avoid busy-waiting
    #             if ready:
    #                 conn, addr = tcp_socket.accept()
    #                 threading.Thread(target=self.handle_tcp_connection, args=(conn, addr)).start()
    #         except KeyboardInterrupt:
    #             # self.running = False
    #             # print("\033[91mServer shutting down...\033[0m")
    #             # tcp_socket.close()
    #             # udp_socket.close()
    #             # sys.exit(0)
    #             print("\n\033[93mStopping server... Cleaning up resources.\033[0m")
    #             self.running = False
    #             udp_socket.close()
    #             tcp_socket.close()
    #             print("\033[91mServer has been shut down gracefully.\033[0m")
    #             sys.exit(0)

    def start(self):
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        udp_socket.bind((self.ip, self.udp_port))
        udp_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_socket.bind((self.ip, self.tcp_port))
        tcp_socket.listen(5)

        threading.Thread(target=self.send_offers).start()
        threading.Thread(target=self.handle_udp_requests, args=(udp_socket,)).start()

        try:
            while self.running:
                ready, _, _ = select([tcp_socket], [], [], 1)  # Use select to avoid busy-waiting
                if ready:
                    conn, addr = tcp_socket.accept()
                    threading.Thread(target=self.handle_tcp_connection, args=(conn, addr)).start()
        except KeyboardInterrupt:
            print("\n\033[93mStopping server... Cleaning up resources.\033[0m")
        finally:
            self.running = False
            try:
                udp_socket.close()
                tcp_socket.close()
            except OSError:
                pass  # Ignore errors during socket closure
            print("\033[91mServer has been shut down gracefully.\033[0m")
            sys.exit(0)



if __name__ == "__main__":
    ip_address = socket.gethostbyname(socket.gethostname())
    server = Server(ip_address, udp_port=13117, tcp_port=20000)
    server.start()
