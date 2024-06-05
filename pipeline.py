import threading
import time
import random
from Header import RDTHeader

INITIAL_SSTHRESH = 16
CHUNK_SIZE = 536

class test():
    def __init__(self):
        self.base_seq_num = 0
        self.ssthresh = INITIAL_SSTHRESH
        self.cwnd = 1
        self.last_ack_id = 0
        self.send_tim = []
        self.send_lock = threading.Lock()
        self.timeout = 1
        self.send_seq_num = 0

    def send_single(self, data=None, test_case=0):
        # TODO: send a single pack and check the ACK.
        pass

    def send_chunk(self, idx, chunk, test_case):
        # TODO: send a single pack WITHOUT checking ACK.
        # SEQ_num should be self.base_seq_num + idx.

        print(f"send chunk: {idx}")
        pass

    def recv_ack(self) -> RDTHeader | None:
        # TODO: receive an ACK. [NON-BLOCKING]
        # return None immediately if there is no packet.

        if random.random() < 0.02 and self.send_seq_num > self.last_ack_id + 1:
            res = RDTHeader()
            res.ACK = 1
            res.ACK_num = self.last_ack_id + 1
            print(f"ack {self.last_ack_id + 1}")
            return res
        return None
        pass

    def recv_single(self) -> RDTHeader:
        # TODO: receive a packet. [BLOCKING]
        pass

    def reply_ack(self, ack_num, test_case):
        # TODO: reply an ACK pack with ack_num.
        pass

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
                        self.ssthresh = max(self.ssthresh // 2, 2)
                        self.cwnd = self.ssthresh
                        self.send_chunk(ack_id + 1, data[ack_id + 1], test_case)
                        with self.send_lock:
                            self.send_tim[ack_id + 1] = time.time()
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
                        self.cwnd += 1/self.cwnd
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
                            print(f"timeout: {i}")
                            self.send_tim.remove((i, t))
                            if i <= self.last_ack_id:
                                continue
                            self.ssthresh = max(self.ssthresh // 2, 2)
                            self.cwnd = 1
                            self.send_chunk(i, data[i], test_case)
                            self.send_tim.append((i, time.time()))

                time.sleep(0.01)

    def send_init_header(self, chunk_cnt, test_case=0):
        print("Sending init header")
        self.send_single(int.to_bytes(chunk_cnt), test_case)

    def send_pipelined(self, data: bytes = None, test_case=0):
        # could be sent by a single chunk.
        if len(data) < CHUNK_SIZE - 5:
            self.send_single(data + b'     ', test_case)
            return

        # segmentation
        chunks = [data[i:i + CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
        self.send_init_header(len(chunks), test_case)

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
        header = self.recv_single()
        test_case = header.test_case
        if header.LEN >= 5:
            self.reply_ack(header.SEQ_num, test_case)
            return header.PAYLOAD[:-5]

        if header.LEN == 4:
            self.reply_ack(header.SEQ_num, test_case)
            res = b""
            chunk_siz = int.from_bytes(header.PAYLOAD, byteorder='big')
            self.base_seq_num = header.SEQ_num + 1
            cur = 0
            while cur < chunk_siz:
                header = self.recv_single()
                if header is None:
                    continue
                if cur + self.base_seq_num == header.SEQ_num:
                    cur += 1
                    res += header.PAYLOAD
                self.reply_ack(header.SEQ_num + cur - 1, test_case)

            return res
        else:
            return None

if __name__ == '__main__':
    a = test()

    data_blocks = []
    with open('transmit.txt', 'rb') as file:
        while True:
            block = file.read(1024)
            if not block:
                break
            data_blocks.append(block.decode())
            # all_data = b''.join(data_blocks)
    all_data = ''.join(data_blocks)
    a.send_pipelined(all_data.encode())