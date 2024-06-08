import socket
import threading

from Header import RDTHeader
from RDT import RDTSocket  # Assuming your RDTSocket class is in RDTSocket.py

class Server:
    def __init__(self, address: (str, int), proxy_server_addr: (str, int)):
        self.address = address
        self.proxy_server_addr = proxy_server_addr
        self.connections = {}
        self.lock = threading.Lock()
        self.main_socket=None
        self.sock=None

    def listen(self):
        """
        Listen for incoming packets and distribute them to the appropriate RDTSocket.
        """
        while True:
            data, addr = self.sock.recvfrom(1024)
            header = RDTHeader()
            header.from_bytes(data)
            if header.check_valid():
                true_source = header.src
                # self.connections[self.main_socket.header.src]=self.main_socket

                with self.lock:
                    if true_source not in self.connections:
                        print(f"New connection from {true_source}")
                        # Send the received packet to the main RDTSocket's recv_buffer
                        self.main_socket.recv_buffer.append(data)
                    else:
                        rdt_socket = self.connections[true_source]
                        with rdt_socket.recv_lock:
                            rdt_socket.recv_buffer.append(data)