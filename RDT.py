import multiprocessing
import socket
import time

from Header import RDTHeader


class RDTSocket():
    def __init__(self) -> None:
        """
        You shold define necessary attributes in this function to initialize the RDTSocket
        """
        #############################################################################
        # TODO: NECESSARY ATTRIBUTES HERE                                           #
        #############################################################################
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.peer_address = None
        self.header = RDTHeader()
        self.recv_buffer = []
        self.send_lock = multiprocessing.Lock()
        self.recv_lock = multiprocessing.Lock()
        self.close_event = multiprocessing.Event()
        self.ack_event = multiprocessing.Event()
        self.timeout = 1  # Timeout for retransmissions
        self.expected_seq_num = 0

        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        # pass
    
    def bind(self, address: (str, int)): # type: ignore
        """
        When trying to establish a connection. The socket must be bound to an address 
        and listening for connections. address is the address bound to the socket on 
        the other end of the connection.

        This function should be blocking. 
        
        params: 
            address:    Target IP address and its port
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        self.sock.bind(address)
        #############################################################################
        # raise NotImplementedError()

    def accept(self): # type: ignore
        """
        When using this SOCKET to create an RDT SERVER, it should accept the connection
        from a CLIENT. After that, an RDT connection should be established.
        Please note that this function needs to support multithreading and be able to
        establish multiple socket connections. Messages from different sockets should
        be isolated from each other, requiring you to multiplex the data received at
        the underlying UDP.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        while True:
            data, addr = self.sock.recvfrom(1024)
            if data:
                self.header.from_bytes(data)
                if self.header.SYN == 1:
                    # Send SYN-ACK packet
                    with self.send_lock:
                        self.peer_address = addr
                        self.header.SYN = 1
                        self.header.ACK = 1
                        self.sock.sendto(self.header.to_bytes(), self.peer_address)
                        break

        # Wait for ACK from client
        while True:
            data, addr = self.sock.recvfrom(1024)
            if data:
                self.header.from_bytes(data)
                if self.header.ACK == 1:
                    break

        # Create new RDTSocket instance for the connection
        conn = RDTSocket()
        # conn.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.peer_address = self.peer_address
        conn.sock=self.sock
        print("accepted")
        return conn

    def connect(self, address: (str, int)):  # type: ignore
        """
        When using this SOCKET to create an RDT client, it should send the connection
        request to target SERVER. After that, an RDT connection should be established.

        params:
            address:    Target IP address and its port
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        self.peer_address = address
        # Send SYN packet to initiate connection
        self.header.SYN = 1
        self.header.ACK = 0
        print("Sender: Sending SYN packet...")
        self.sock.sendto(self.header.to_bytes(), self.peer_address)

        # Wait for SYN-ACK response
        print("Sender: Waiting for SYN-ACK response...")
        while True:
            data, addr = self.sock.recvfrom(1024)
            if data:
                print("Sender: Received SYN-ACK response")
                self.header.from_bytes(data)
                print("Sender: Received header:", self.header.SYN, self.header.ACK)
                if self.header.SYN == 1 and self.header.ACK == 1:
                    # Send ACK
                    print("Sender: Sending ACK...")
                    self.header.SYN = 0
                    self.header.ACK = 1
                    self.sock.sendto(self.header.to_bytes(), self.peer_address)
                    break
        #############################################################################
        # raise NotImplementedError()

    def send(self, data=None, tcpheader=None, test_case=0):
        """
        RDT can use this function to send specified data to a target that has already 
        established a reliable connection. Please note that the corresponding CHECKSUM 
        for the specified data should be calculated before computation. Additionally, 
        this function should implement flow control during the sending phase. Moreover, 
        when the data to be sent is too large, this function should be able to divide 
        the data into multiple chunks and send them to the destination in a pipelined 
        manner.

        params:
            data:       The data that will be sent.
            tcpheader:  Message header.Include SYN, ACK, FIN, CHECKSUM, etc. Use this
                        attribute when needed.
            test_case:  Indicate the test case will be used in this experiment
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        with self.send_lock:
            chunks = [data[i:i + 1024] for i in range(0, len(data), 1024)]
            for chunk_index, chunk in enumerate(chunks):
                print(f"Sending chunk {chunk_index + 1}/{len(chunks)}: {chunk}")
                self.header.PAYLOAD = chunk
                self.header.LEN = len(chunk)
                self.header.SEQ_num = chunk_index  # Update sequence number
                # self.header.CHECKSUM = self.calculate_checksum()
                self.sock.sendto(self.header.to_bytes(), self.peer_address)
                # Wait for ACK
                while True:
                    print(f"Waiting for ACK for chunk {chunk_index + 1}")
                    data, addr = self.sock.recvfrom(1024)
                    print(f"Received data: {data}")
                    if data:
                        recv_header = RDTHeader()
                        recv_header.from_bytes(data)
                        if recv_header.ACK == 1 and recv_header.SEQ_num == chunk_index:
                            print(f"Received ACK for chunk {chunk_index + 1}")
                            break
                    else:
                        print("Timeout, resending packet")
                        self.sock.sendto(self.header.to_bytes(), self.peer_address)
        #############################################################################
        # raise NotImplementedError()

    def recv(self):
        """
        This function receives data, verifies it, and sends an ACK back to the sender.
        If corrupted or missing data packets are detected, a request for retransmission
        should be sent to the other party.

        This function is blocking.
        """
        while True:
            print("Waiting to receive data...")
            data, addr = self.sock.recvfrom(1024)
            print("Data received:", data)
            if data:
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                print("Received header:", recv_header)

                if recv_header.FIN == 1:
                    # Received FIN signal, send ACK and perform closing operations
                    print("Received FIN signal. Sending ACK...")
                    self.header.ACK = 1
                    self.header.SEQ_num = recv_header.SEQ_num
                    self.sock.sendto(self.header.to_bytes(), addr)

                    # Send FIN
                    print("Sending FIN...")
                    self.header.FIN = 1
                    self.header.ACK = 0
                    self.sock.sendto(self.header.to_bytes(), addr)

                    # Wait for a short time to make sure the other party receives the FIN
                    time.sleep(1)
                    self.close_event.set()
                    # Perform closing operations or signal upper layer for closing
                    return None, None  # Signal upper layer to close connection
                    # break
                elif self.is_packet_valid(recv_header):
                    if recv_header.SEQ_num == self.expected_seq_num:
                        print(f"Expected packet received: SEQ_num={recv_header.SEQ_num}")
                        self.expected_seq_num += 1
                        self.header.ACK = 1
                        self.header.SEQ_num = recv_header.SEQ_num
                        self.sock.sendto(self.header.to_bytes(), addr)
                        print("\nrecv back ",recv_header.PAYLOAD,addr)
                        return recv_header.PAYLOAD, addr
                    else:
                        print(f"Unexpected SEQ_num: {recv_header.SEQ_num}. Expected: {self.expected_seq_num}")
                else:
                    print("Packet corrupted, requesting retransmission")

                # Send ACK for the last correctly received packet
                self.header.ACK = 1
                self.header.SEQ_num = self.expected_seq_num - 1
                self.sock.sendto(self.header.to_bytes(), addr)

    def is_packet_valid(self, header):
        # Implement your packet validation logic here (e.g., checksum)
        # This is a placeholder for actual validation logic
        return True

    def close(self):
        """
        Close current RDT connection.
        You should follow the 4-way-handshake, and then the RDT connection will be terminated.
        """
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        # Initiate connection termination (4-way handshake)
        print("Initiating connection termination (4-way handshake)")
        self.header.FIN = 1
        self.header.ACK = 0
        self.sock.sendto(self.header.to_bytes(), self.peer_address)

        # Wait for ACK of FIN
        print("Waiting for ACK of FIN...")
        while True:
            data, addr = self.sock.recvfrom(1024)
            if data:
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                if recv_header.ACK == 1:
                    print("ACK of FIN received")
                    break

        # Wait for FIN from peer
        print("Waiting for FIN from peer...")
        while True:
            data, addr = self.sock.recvfrom(1024)
            if data:
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                if recv_header.FIN == 1:
                    print("FIN from peer received")
                    # Send ACK for FIN
                    self.header.FIN = 0
                    self.header.ACK = 1
                    self.sock.sendto(self.header.to_bytes(), self.peer_address)
                    print("ACK for FIN sent")
                    break

        self.close_event.set()
        #############################################################################

