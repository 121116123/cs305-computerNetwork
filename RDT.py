from __future__ import annotations

import multiprocessing
import socket
import threading
import time
from Header import RDTHeader

INITIAL_SSTHRESH = 16
CHUNK_SIZE = 256



class RDTSocket():
    def __init__(self) -> None:
        """
        You shold define necessary attributes in this function to initialize the RDTSocket
        """
        #############################################################################
        # TODO: NECESSARY ATTRIBUTES HERE                                           #
        #############################################################################
        self.server_thread = None
        self.base_seq_num = 0
        self.ssthresh = INITIAL_SSTHRESH
        self.cwnd = 1
        self.last_ack_id = 0
        self.send_tim = []
        self.send_lock = threading.Lock()
        self.timeout = 1
        self.send_seq_num = 0

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # self.peer_address = None
        self.header = RDTHeader()
        self.recv_buffer = []
        self.send_lock = multiprocessing.Lock()
        self.recv_lock = multiprocessing.Lock()
        self.close_event = multiprocessing.Event()
        self.ack_event = multiprocessing.Event()
        self.timeout = 1  # Timeout for retransmissions
        self.proxy_server_addr = None
        self.target_address = None
        self.my_address = None
        self.recv_buffer = []
        self.server = None
        #############################################################################
        # TODO: YOUR CODE HERE                                                      #
        #############################################################################
        # pass

    def bind(self, address: (str, int)):  # type: ignore
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
        self.server.main_socket = self
        self.server.sock = self.sock
        self.server_thread = threading.Thread(target=self.server.listen)
        self.server_thread.daemon = True
        self.server_thread.start()

        #############################################################################
        # raise NotImplementedError()

    def accept(self):  # type: ignore
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
            if self.recv_buffer:
                data = self.recv_buffer.pop(0)
                self.header.from_bytes(data)
                print(f"Received SYN packet: {self.header}")
                if self.header.SYN == 1:
                    # Send SYN-ACK packet
                    with self.send_lock:
                        # self.proxy_server_addr = addr
                        self.header.SYN = 1
                        self.header.ACK = 1
                        self.header.test_case = 20
                        self.header.set_checksum()
                        self.my_address = self.sock.getsockname()
                        self.target_address = self.header.src
                        self.header.assign_address(self.my_address, self.target_address)
                        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                        print(f"Sent SYN-ACK packet: {self.header}")
                        break

        # # Wait for ACK from client
        # while True:
        #     data, addr = self.sock.recvfrom(1024)
        #     if data:
        #         self.header.from_bytes(data)
        #         print(f"Received ACK packet: {self.header}")
        #         if self.header.ACK == 1:
        #             break

        # Create new RDTSocket instance for the connection
        conn = RDTSocket()
        conn.server = self.server
        # conn.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        conn.proxy_server_addr = self.proxy_server_addr
        conn.header.assign_address(self.my_address, self.target_address)
        # conn.header.Target_address = self.target_address
        conn.sock = self.sock
        self.server.connections[self.header.tgt] = conn
        while True:
            if conn.recv_buffer:
                conn.recv_buffer.pop()
                break
        print("Accepted, received ACK, and created a new connection")
        return conn

    def connect(self, address: (str, int)):  # type: ignore
        """
        When using this SOCKET to create an RDT client, it should send the connection
        request to target SERVER. After that, an RDT connection should be established.

        params:
            address:    Target IP address and its port
        """
        #############################################################################
        # TODO: YOUR CODE HERE
        # Send SYN packet to initiate connection
        self.header.SYN = 1
        self.header.ACK = 0
        self.header.test_case = 20
        self.my_address = self.sock.getsockname()
        self.target_address = address
        self.header.set_checksum()
        self.header.assign_address(self.my_address, self.target_address)
        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
        print(f"Sender: Send SYN packet {self.header}")

        # Wait for SYN-ACK response
        # print("Sender: Waiting for SYN-ACK response...")
        while True:
            if self.recv_buffer:
                data = self.recv_buffer.pop(0)
                self.header.from_bytes(data)
                print(f"Sender: Received SYN-ACK response {self.header}")
                if self.header.SYN == 1 and self.header.ACK == 1:
                    # Send ACK
                    self.header.SYN = 0
                    self.header.ACK = 1
                    self.header.test_case = 20
                    self.header.set_checksum()
                    self.header.assign_address(self.my_address, self.target_address)
                    self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                    # print(f"Sender: Send ACK packet... {self.header}")
                    break
        #############################################################################
        # raise NotImplementedError()

    def send_single(self, data=None, test_case=0):
        # TODO: send a single pack and check the ACK.
        with self.send_lock:
            self.header.PAYLOAD = data
            self.header.LEN = len(data)
            self.header.SEQ_num = self.send_seq_num  # Use send_seq_num
            self.header.ACK = 0
            self.header.set_checksum()
            self.header.test_case = test_case
            # self.header.assign_address(self.header.src,self.header.tgt)
            self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
            begin = time.time()
            while True:
                # Check if there is any data in the recv_buffer
                if self.recv_buffer:
                    data = self.recv_buffer.pop(0)
                    recv_header = RDTHeader()
                    recv_header.from_bytes(data)
                    if recv_header.ACK == 1:
                        self.send_seq_num += 1
                        # print("Received ACK for single message: ", recv_header)
                        break
                else:
                    end = time.time()
                    if end - begin > self.timeout:
                        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                        begin = end
                    time.sleep(0.01)  # Sleep for a short time to prevent busy waiting

    def send_chunk(self, idx, chunk, test_case):
        # TODO: send a single pack WITHOUT checking ACK.
        # SEQ_num should be self.base_seq_num + idx.
        # with self.send_lock:
        self.header.PAYLOAD = chunk
        self.header.LEN = len(chunk)
        self.header.SEQ_num = self.base_seq_num + idx  # Use send_seq_num
        self.header.ACK = 0
        self.header.set_checksum()
        self.header.test_case = test_case
        # self.header.assign_address(self.header.src,self.header.tgt)
        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)

        print(f"send chunk: {idx}")

    # def send(self, data=None, tcpheader=None, test_case=0):
    #     """
    #     RDT can use this function to send specified data to a target that has already
    #     established a reliable connection. Please note that the corresponding CHECKSUM
    #     for the specified data should be calculated before computation. Additionally,
    #     this function should implement flow control during the sending phase. Moreover,
    #     when the data to be sent is too large, this function should be able to divide
    #     the data into multiple chunks and send them to the destination in a pipelined
    #     manner.
    #
    #     params:
    #         data:       The data that will be sent.
    #         tcpheader:  Message header.Include SYN, ACK, FIN, CHECKSUM, etc. Use this
    #                     attribute when needed.
    #         test_case:  Indicate the test case will be used in this experiment
    #     """
    #     #############################################################################
    #     # TODO: YOUR CODE HERE                                                      #
    #     with self.send_lock:
    #         chunks = [data[i:i + 1024] for i in range(0, len(data), 1024)]
    #         for chunk_index, chunk in enumerate(chunks):
    #             print(f"Sending chunk {chunk_index + 1}/{len(chunks)}: {chunk}")
    #             self.header.PAYLOAD = chunk
    #             self.header.LEN = len(chunk)
    #             self.header.SEQ_num = self.send_seq_num  # Use send_seq_num
    #             self.header.CHECKSUM = self.header.calc_checksum()
    #             self.header.test_case = test_case
    #             # self.header.assign_address(self.header.src,self.header.tgt)
    #             self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #             while True:
    #                 print(f"Waiting for ACK for chunk {chunk_index + 1}")
    #                 self.sock.settimeout(self.timeout)  # Set socket timeout
    #                 try:
    #                     data, addr = self.sock.recvfrom(1024)
    #                     if data:
    #                         recv_header = RDTHeader()
    #                         recv_header.from_bytes(data)
    #                         if recv_header.ACK == 1 and recv_header.SEQ_num == self.send_seq_num:
    #                             self.send_seq_num += 1
    #                             print(f"Received ACK for chunk {chunk_index + 1}")
    #                             break
    #                 except socket.timeout:
    #                     print("Timeout, resending packet")
    #                     self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #                     # self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #     #############################################################################
    #     # raise NotImplementedError()

    # def recv(self):
    #     """
    #     This function receives data, verifies it, and sends an ACK back to the sender.
    #     If corrupted or missing data packets are detected, a request for retransmission
    #     should be sent to the other party.
    #
    #     This function is blocking.
    #     """
    #     while True:
    #         data, addr = self.sock.recvfrom(1024)
    #         if data:
    #             recv_header = RDTHeader()
    #             recv_header.from_bytes(data)
    #             print(f"Received packet: {recv_header}")
    #
    #             if recv_header.FIN == 1:
    #                 # Received FIN signal, send ACK and perform closing operations
    #                 self.header.ACK = 1
    #                 self.header.test_case = 20
    #                 self.header.SEQ_num = recv_header.SEQ_num
    #                 # self.header
    #                 self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #                 print(f"receiver: Sent ACK packet: {self.header}")
    #
    #                 # Send FIN
    #                 self.header.FIN = 1
    #                 self.header.ACK = 0
    #                 self.header.test_case = 20
    #                 self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #                 print(f"receiver: Sent FIN packet: {self.header}")
    #
    #                 # Wait for a short time to make sure the other party receives the FIN
    #                 time.sleep(1)
    #                 # self.close_event.set()
    #                 # Perform closing operations or signal upper layer for closing
    #                 return self.header, 1  # Signal upper layer to close connection
    #                 # break
    #             elif self.is_packet_valid(recv_header):
    #                 if recv_header.SEQ_num == self.expected_seq_num:
    #                     self.expected_seq_num += 1
    #                     self.header.ACK = 1
    #                     self.header.SEQ_num = recv_header.SEQ_num
    #                     self.header.test_case = recv_header.test_case
    #                     self.header.assign_address(recv_header.tgt, recv_header.src)
    #                     self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
    #                     print(f"receiver: Sent ACK packet: {self.header}")
    #                     return recv_header.PAYLOAD, 0
    #                 else:
    #                     print(f"receiver: Unexpected SEQ_num: {recv_header.SEQ_num}. Expected: {self.expected_seq_num}")
    #             else:
    #                 print("receiver: Packet corrupted, requesting retransmission")
    #
    #             # Send ACK for the last correctly received packet
    #             self.header.ACK = 1
    #             self.header.SEQ_num = self.expected_seq_num - 1
    #             self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)

    def listen_acks(self, data, test_case):
        dup_ack = 0
        while True:
            header = self.recv_ack()
            if header:
                ack_id = header.ACK_num
                # if ack_id < self.base_seq_num:
                #     continue
                print(f"ack_id: {ack_id}, last: {self.last_ack_id}")
                if ack_id == self.last_ack_id:
                    dup_ack += 1
                    if dup_ack >= 3:
                        dup_ack = 0
                        print(f"fast ret: {ack_id + 1}")
                        self.ssthresh = max(self.cwnd // 2, 2)
                        self.cwnd = self.ssthresh
                        self.send_chunk(ack_id + 1, data[ack_id + 1], test_case)
                        with self.send_lock:
                            # self.send_tim[ack_id + 1] = time.time()
                            for idx, t in enumerate(self.send_tim):
                                if t[0] == ack_id + 1:
                                    self.send_tim.pop(idx)
                                    break
                            self.send_tim.append((ack_id + 1, time.time()))
                else:
                    dup_ack = 0
                    print(f"acked : {ack_id}")
                    print(f"current que: {self.send_tim}")
                    self.last_ack_id = ack_id
                    if self.last_ack_id == len(data) - 1:
                        return
                    if self.cwnd < self.ssthresh:
                        self.cwnd += 1
                    else:
                        self.cwnd += 1 / self.cwnd
            else:
                tim = time.time()
                with self.send_lock:
                    if len(self.send_tim) > 0 and tim - self.send_tim[0][1] > self.timeout:
                        rm = []
                        for i, t in self.send_tim:
                            if t + self.timeout > tim:
                                break
                            rm.append((i, t))
                        for i, t in rm:
                            self.send_tim.remove((i, t))
                            print(f"timeout: {i}")
                            if i <= self.last_ack_id:
                                continue
                            self.ssthresh = max(self.cwnd // 2, 2)
                            self.cwnd = 1
                            self.send_chunk(i, data[i], test_case)
                            self.send_tim.append((i, time.time()))

                time.sleep(0.01)

    def send_init_header(self, chunk_cnt, test_case=0):
        print("Sending init header")
        self.send_single(chunk_cnt.to_bytes(4, byteorder='big').decode(), test_case)

    def send_pipelined(self, data: str = None, test_case=0):
        # could be sent by a single chunk.
        if len(data) < CHUNK_SIZE - 5:
            self.send_single(data + '     ', test_case)
            return

        # segmentation
        chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
        self.send_init_header(len(chunks), test_case)
        print("chunk_size: ",len(chunks))
        self.cwnd = 1
        self.ssthresh = INITIAL_SSTHRESH
        self.last_ack_id = -1
        self.base_seq_num = self.send_seq_num

        ack_thread = threading.Thread(target=self.listen_acks, args=(chunks, test_case))
        ack_thread.daemon = True
        ack_thread.start()

        for i in range(0, len(chunks)):
            while True:
                if i <= self.last_ack_id + self.cwnd:
                    self.send_chunk(i, chunks[i], test_case)
                    self.send_tim.append((i, time.time()))
                    self.send_seq_num += 1
                    break
                else:
                    time.sleep(0.01)

        ack_thread.join()

    def recv_pipelined(self):
        header,_ = self.recv_single()
        test_case = header.test_case
        if header.LEN >= 5:
            self.reply_ack(header.SEQ_num, test_case)
            return header.PAYLOAD[:-5]

        if header.LEN == 4:
            chunk_siz = int.from_bytes(header.PAYLOAD.encode(), byteorder='big')
            res = [None] * chunk_siz
            self.base_seq_num = header.SEQ_num + 1
            cur = 0
            self.test_cur = cur
            while cur < chunk_siz:
                header,_ = self.recv_single()
                if header is None:
                    continue
                idx = header.SEQ_num - self.base_seq_num
                if res[idx] is None:
                    res[idx] = header.PAYLOAD
                    while cur < chunk_siz and res[cur] is not None:
                        cur += 1
                self.reply_ack(self.base_seq_num + cur , test_case)
                self.test_cur = cur
            return ''.join(res)
        else:
            return None

    def recv_ack(self) -> RDTHeader | None:
        # TODO: receive an ACK. [NON-BLOCKING]
        # return None immediately if there is no packet.

        # Check if there is any data in the recv_buffer
        if self.recv_buffer:
            data = self.recv_buffer.pop(0)
            recv_header = RDTHeader()
            recv_header.from_bytes(data)
            if recv_header.ACK == 1:
                return recv_header
        return None

    def recv_single(self) -> (RDTHeader,int):
        # TODO: receive a packet. [BLOCKING]
        while True:
            if self.recv_buffer:
                data = self.recv_buffer.pop(0)
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                if recv_header.FIN == 1:
                # # Received FIN signal, send ACK and perform closing operations
                    self.header.ACK = 1
                    self.header.test_case = 20
                    self.header.SEQ_num = recv_header.SEQ_num
                    self.header.set_checksum()
                    # self.header
                    self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                    # Send FIN
                    self.header.FIN = 1
                    self.header.ACK = 0
                    self.header.test_case = 20
                    self.header.set_checksum()
                    self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                    # print(f"receiver: Sent FIN packet: {self.header}")

                    # Wait for a short time to make sure the other party receives the FIN
                    time.sleep(1)
                    # Perform closing operations or signal upper layer for closing
                    self.server.stop()
                    return self.header,1  # Signal upper layer to close connection
                    # break
                self.header.ACK = 1
                self.header.SEQ_num = recv_header.SEQ_num
                self.header.test_case = recv_header.test_case
                self.header.assign_address(recv_header.tgt, recv_header.src)
                self.header.set_checksum()
                self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                print(f"receiver: Sent ACK packet: {self.header}")
                return recv_header,0
            else:
                time.sleep(0.01)  # Sleep for a short time to prevent busy waiting

    def reply_ack(self, ack_num, test_case):
        # TODO: reply an ACK pack with ack_num.
        self.header.ACK = 1
        self.header.ACK_num = ack_num
        self.header.test_case = test_case
        self.header.PAYLOAD = None
        self.header.set_checksum()
        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
        # print(f"Sent ACK for SEQ_num {self.header.ACK_num}")

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
        self.header.test_case = 20
        self.header.PAYLOAD = None
        self.header.set_checksum()
        # print("proxy_sever ", self.proxy_server_addr)
        self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)

        # Wait for ACK of FIN
        # print("Waiting for ACK of FIN...")
        while True:
            if self.recv_buffer:
                data = self.recv_buffer.pop(0)
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                if recv_header.ACK == 1:
                    print("ACK of FIN received")
                    break

        # Wait for FIN from peer
        # print("Waiting for FIN from peer...")
        while True:
            if self.recv_buffer:
                data = self.recv_buffer.pop(0)
                recv_header = RDTHeader()
                recv_header.from_bytes(data)
                if recv_header.FIN == 1:
                    print("FIN from peer received")
                    # Send ACK for FIN
                    self.header.FIN = 0
                    self.header.ACK = 1
                    self.header.test_case = 20
                    self.header.assign_address(self.my_address, self.target_address)
                    self.header.set_checksum()
                    self.sock.sendto(self.header.to_bytes(), self.proxy_server_addr)
                    print(f"ACK for FIN sent,{self.header}")
                    break
                # Stop the server thread
        self.server.stop()
        # Close the socket
        self.sock.close()
        # self.close_event.set()
        #############################################################################


class Server:
    def __init__(self, address: (str, int), proxy_server_addr: (str, int)):
        self.address = address
        self.proxy_server_addr = proxy_server_addr
        self.connections = {}
        self.lock = threading.Lock()
        self.main_socket = None
        self.sock = None
        self.stop_event = 0

    def listen(self):
        """
        Listen for incoming packets and distribute them to the appropriate RDTSocket.
        """
        while self.stop_event== 0 :
            data, addr = self.sock.recvfrom(1024)
            header = RDTHeader()
            header.from_bytes(data)
            print("listen  ", header)
            if header.check_valid():
                true_source = header.src
                with self.lock:
                    if true_source not in self.connections:
                        # print("put in main socket: ", self.main_socket.my_address)
                        # Send the received packet to the main RDTSocket's recv_buffer
                        self.main_socket.recv_buffer.append(data)
                    else:
                        rdt_socket = self.connections[true_source]
                        # print("put in rdt socket ",self.main_socket.my_address, true_source)
                        with rdt_socket.recv_lock:
                            rdt_socket.recv_buffer.append(data)
        # print("while true finish")
    def stop(self):
        self.stop_event=1
        self.sock.close()