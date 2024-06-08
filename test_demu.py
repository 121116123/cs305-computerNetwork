import socket
import time
from RDT import RDTSocket, Server


def sender(sender_address, receiver_address):
    sender_sock = RDTSocket()
    sender_sock.server = Server(sender_address, sender_sock.proxy_server_addr)

    sender_sock.bind(sender_address)
    sender_sock.connect(receiver_address)
    data = "Test message"
    sender_sock.send_pipelined(data=data, test_case=0)
    print("Message sent from", sender_address)
    sender_sock.close()

if __name__ == '__main__':
    receiver_address = ("127.0.0.1", 12349)  # 你的接收方地址
    sender_address1 = ("127.0.0.1", 12344)  # 第一个发送方地址
    sender_address2 = ("127.0.0.1", 12345)  # 第二个发送方地址

    receiver_sock = RDTSocket()
    receiver_sock.bind(receiver_address)
    receiver_sock.accept()

    # 启动第一个发送方发送消息
    sender(sender_address1, receiver_address)
    # 启动第二个发送方发送消息
    sender(sender_address2, receiver_address)

    # 接收消息
    client_sock, _ = receiver_sock.accept()
    received_data = client_sock.recv_pipelined()
    print("Received data:", received_data)
    client_sock.close()

    receiver_sock.close()
