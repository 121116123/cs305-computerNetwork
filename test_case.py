import socket
import time
from RDT import RDTSocket, Server
from multiprocessing import Process
import signal

# connect proxy server
# #
proxy_server_address = ('10.16.52.172', 12234)   # ProxyServerAddress
fromSenderAddr = ('10.16.52.172', 12345)         # FromSender
toReceiverAddr = ('10.16.52.172', 12346)         # ToSender
fromReceiverAddr = ('10.16.52.172', 12347)       # FromReceiver
toSenderAddr = ('10.16.52.172', 12348)           # ToReceiver
resultAddr = ('10.16.52.172', 12230)
# #
#TODO change the address to your address
sender_address = ("10.25.64.142", 12344)         # Your sender address
receiver_address = ("10.25.64.142", 12349)       # Your receiver address
# sender_address1=("10.25.64.142", 12350)


# connect locally server
# # #
# proxy_server_address = ('127.0.0.1', 12234)
# fromSenderAddr = ('127.0.0.1', 12345)
# toReceiverAddr = ('127.0.0.1', 12346)
# fromReceiverAddr = ('127.0.0.1', 12347)
# toSenderAddr = ('127.0.0.1', 12348)
#
# sender_address = ("127.0.0.1", 12244)
# sender_address1 = ("127.0.0.1", 12250)
# receiver_address = ("127.0.0.1", 12249)
# resultAddr = ("127.0.0.1", 12230)

num_test_case = 16


class TimeoutException(Exception):
    pass


def handler(signum, frame):
    raise TimeoutException


# signal.signal(signal.SIGALRM, handler)

def test_case():
    sender_sock = None
    reciever_sock = None
    # sender_sock1 = None

    # TODO: You could change the range of this loop to test specific case(s) in local test.

    for i in range(7, num_test_case):
        if sender_sock:
            del sender_sock
        if reciever_sock:
            del reciever_sock
        # if sender_sock1:
        #     del sender_sock1
        sender_sock = RDTSocket()  # You can change the initialize RDTSocket()
        reciever_sock = RDTSocket()  # You can change the initialize RDTSocket()
        # sender_sock1 = RDTSocket()
        print(f"Start test case : {i}")

        try:
            result = RDT_start_test(sender_sock,  reciever_sock, sender_address,
                                    receiver_address, i)
        except Exception as e:
            print(e)
        finally:
            client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_sock.connect(resultAddr)

            client_sock.sendall(f"{sender_address}-{receiver_address}:{i}".encode())

            response = client_sock.recv(1024)

            client_sock.close()

            print(f"proxy result for test case {i} {response.decode()}")

            if response.decode() == 'True' and result:
                print(f"test case {i} pass")
            else:
                print(f"test case {i} fail")

            #############################################################################
            # TODO you should close your socket, and release the resource, this code just a
            # demo. you should make some changes based on your code implementation or you can
            # close them in the other places.

            # sender_sock.close()
            # reciever_sock.close()

            #############################################################################
            time.sleep(5)

            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.sendto(f"{sender_address}-{receiver_address}".encode(), proxy_server_address)

            time.sleep(10)


def RDT_start_test(sender_sock,reciever_sock, sender_address, receiver_address,
                   test_case):
    sender = Process(target=RDT_send, args=(sender_sock, sender_address, receiver_address, test_case))
    receiver = Process(target=RDT_receive, args=(reciever_sock, receiver_address, test_case))
    # sender1 = Process(target=RDT_send, args=(sender_sock1, sender_address1, receiver_address, test_case))

    receiver.start()
    time.sleep(5)
    sender.start()
    # sender1.start()

    # if test_case < 5:
    #     signal.alarm(20)
    # else:
    #     signal.alarm(120)

    sender.join()
    # sender1.join()
    receiver.join()

    time.sleep(1)

    # signal.alarm(0)
    if test_case < 5:
        return True
    else:
        # TODO you may need to change the path, if you want.
        return test_file_integrity('original.txt', 'transmit.txt')


def RDT_send(sender_sock: RDTSocket, source_address, target_address, test_case):
    """
        You should refer to your own implementation to implement this code. the sender should specify the Source_address, Target_address, and test_case in the Header of all packets sent by the receiver.
        params:
            target_address:    Target IP address and its port
            source_address:    Source IP address and its port
            test_case:         The rank of test case
    """
    data_blocks = []
    file_path = 'original.txt'  # You can modify the path of file. Howerver, if you change this file, you need to modify the input for function test_file_integrity()

    sock = sender_sock
    sock.proxy_server_addr = fromSenderAddr
    print("send want bind ", source_address)
    sock.server = Server(sock.header.src, sock.proxy_server_addr)
    sock.bind(source_address)
    sock.connect(target_address)

    if test_case >= 5:
        #############################################################################
        # TODO: you need to send a files. Here you need to write the code according to your own implementation.
        try:
            with open(file_path, 'rb') as file:
                while True:
                    block = file.read(1024)
                    if not block:
                        break
                    data_blocks.append(block.decode())
                    # all_data = b''.join(data_blocks)
            all_data = ''.join(data_blocks)
            # return all_data
        except IOError as e:
            print(f"An error occurred: {e}")
        print("Sender: Sending data...")
        sock.send_pipelined(data=all_data, test_case=test_case)
        print("Sender: Data sent")
        sock.close()
        # raise NotImplementedError
        #############################################################################

    else:

        #############################################################################
        # TODO: you need to send a short message. May be you can use:
        data = "Short Message test"
        sock.send_pipelined(data=data, test_case=test_case)

        # # 多次发送
        # data="short message test 2"
        # sock.send_single(data=data, test_case=test_case)

        sock.close()
        print("send finish")

        # raise NotImplementedError
    #############################################################################


def RDT_receive(reciever_sock: RDTSocket, source_address, test_case):
    """
        You should refer to your own implementation to implement this code. the receiver should specify the Source_address, Target_address, and test_case in the Header of all packets sent by the receiver.
        params:
            source_address:    Source IP address and its port
            test_case:         The rank of test case
    """
    sock = reciever_sock
    sock.proxy_server_addr = fromReceiverAddr
    print("recv want bind", source_address)
    sock.server = Server(sock.header.src, sock.proxy_server_addr)
    sock.bind(source_address)
    server_sock = sock.accept()
    # server_sock1 = sock.accept()

    if test_case >= 5:
        #############################################################################
        # TODO: you need to receive original.txt from sender. Here you need to write the code according to your own implementation.
        with open('transmit.txt', 'w') as file:
            # while True:
            data = server_sock.recv_pipelined()
            file.write(data)
        print("Receiver: File received and saved as transmit.txt")
        if test_file_integrity('original.txt', 'transmit.txt'):
            print("These two files are same. Verified passed.")
            # you should Save all data to the file (transmit.txt), and stop this loop when the client close the connection.
            # After that, you need to use the following function to verify the file that you received. When test_case >= 5, the test is passed only when test_file_integrity is verified and the proxy is verified.
            # raise NotImplementedError
        #############################################################################

    else:
        #############################################################################
        # TODO: you need to receive a short message. May be you can use:
        data = server_sock.recv_pipelined()
        # data1=server_sock.recv_pipelined()
        # while True:
        #     data, finished = server_sock.recv_single()
        #     # data1,finished1=server_sock1.recv_single()
        #     if finished :
        #         sock.server.stop()
        #         break
        # print("Receiver: Received message:", data)
        print("finished recv pip data", data)
        # if finished:
        #     print("recv finish")
        # #     # Connection closed by sender
        #     sock.server.stop()
        #     server_sock.server.stop()
        #     break
        # server_sock.recv()
        # raise NotImplementedError
    #############################################################################


# def test_file_integrity(original_path, transmit_path):
#     with open(original_path, 'rb') as file1, open(transmit_path, 'rb') as file2:
#         while True:
#             block1 = file1.read(4096)
#             block2 = file2.read(4096)
#
#             if block1 != block2:
#                 return False
#
#             if not block1:
#                 break
#
#     return True
def test_file_integrity(original_path, transmit_path):
    def normalize_line_endings(block):
        return block.replace(b'\n', b'').replace(b'\r', b'')

    with open(original_path, 'rb') as file1, open(transmit_path, 'rb') as file2:
        while True:
            block1 = file1.read(4096)
            block2 = file2.read(4096)

            # Normalize line endings
            block1 = normalize_line_endings(block1)
            block2 = normalize_line_endings(block2)

            if block1 != block2:
                print("block1: ",block1)
                print("block2: ",block2)
                return False

            if not block1:
                break

    return True



if __name__ == '__main__':
    test_case()
