import socket
import struct

CHUNK_SIZE = 4096
PAYLOAD_SIZE = struct.calcsize("Q")

'''
def establish_client_connection(ip_address='127.0.0.1', port=None, protocol=socket.SOCK_STREAM):
    # Establish protocol
    protocol = parse_protocol(protocol)
    # establish client socket
    client_socket = socket.socket(socket.AF_INET, protocol)
    server_address = (ip_address, port)
    try:
        client_socket.connect(server_address)
        # client_socket.sendall(str(f'{TARGET_FPS}:{op_mode}').encode())
        # response = client_socket.recv(1024)
    except Exception:
        print("<< Connection Failed >>")
        return False

    print("Connected!")

    return client_socket


def parse_protocol(protocol):
    if protocol == 'udp' or protocol == 'UDP':
        return socket.SOCK_DGRAM
    if protocol == 'tcp' or protocol == 'TCP':
        return socket.SOCK_STREAM
    if protocol == socket.SOCK_DGRAM or \
            protocol == socket.SOCK_STREAM:
        return protocol
    else:
        return None


def start_server(address='0.0.0.0', port=None, protocol=socket.SOCK_STREAM):
    # Establish protocol
    protocol = parse_protocol(protocol)
    # Establish server socket
    server_socket = socket.socket(socket.AF_INET, protocol)
    server_socket.bind((address, port))
    server_socket.listen(1)
    print(f'Server listening on: {address}:{port} : {protocol}')
    return server_socket


def await_connection(server_socket):
    # accept client connection
    client_socket, client_address = server_socket.accept()
    print(f'Connection from {client_address} established')
    return client_socket, client_address


def send_over_network(conn, data):
    message = struct.pack("Q", len(data)) + data
    conn.sendall(message)


def receive_over_network(client_socket, payload_size=default_payload_size, data_holder={"data": b""}):
    """
    # data_holder: should be provided as:  data_holder = {"data": b""}
    """
    while len(data_holder["data"]) < payload_size:
        packet = client_socket.recv(CHUNK_SIZE)
        if not packet:
            return None
        data_holder["data"] += packet

    packed_msg_size = data_holder["data"][:payload_size]
    data_holder["data"] = data_holder["data"][payload_size:]
    msg_size = struct.unpack("Q", packed_msg_size)[0]

    while len(data_holder["data"]) < msg_size:
        data_holder["data"] += client_socket.recv(CHUNK_SIZE)

    received_data = data_holder["data"][:msg_size]
    data_holder["data"] = data_holder["data"][msg_size:]

    print(f'received {msg_size / 1024:.2f} kb')
    return received_data

'''


class NetworkConnection:
    def __init__(self, host_address='127.0.0.1', port='5000', protocol='TCP', listen_address='0.0.0.0'):
        self.host_address = host_address
        self.listen_address = listen_address
        self.port = port
        self.protocol = parse_protocol(protocol)
        self.server_socket = None
        self.client_socket = None
        self.udp_socket = None
        self.recv_buf = b""

    def establish_connection(self):
        self.client_socket = socket.socket(socket.AF_INET, self.protocol)
        if self.protocol == socket.SOCK_STREAM:
            self.client_socket.connect((self.host_address, self.port))
        else:
            self.udp_socket = self.client_socket
            self.udp_socket.bind((self.host_address, self.port))

    def start_server(self):
        self.server_socket = socket.socket(socket.AF_INET, self.protocol)
        self.server_socket.bind((self.listen_address, self.port))
        if self.protocol == socket.SOCK_STREAM:
            self.server_socket.listen(1)
        else:
            self.udp_socket = self.server_socket
        print(f'Server listening on: {self.listen_address}:{self.port} : {self.protocol}')

    def await_connection(self):
        if self.protocol == socket.SOCK_STREAM:
            client_socket, client_address = self.server_socket.accept()
            self.client_socket = client_socket
            print(f'Connection from {client_address} established')
            return client_socket, client_address

    # Define a function to pack the header data into bytes
    @staticmethod
    def pack_header(header):
        header_data = b''
        for name, value in header.items():
            name_bytes = name.encode()
            value_bytes = value.encode()
            header_data += struct.pack("I", len(name_bytes))
            header_data += name_bytes
            header_data += struct.pack("I", len(value_bytes))
            header_data += value_bytes
        return header_data

    # Define a function to unpack the header data from bytes
    @staticmethod
    def unpack_header(header_data):
        header = {}
        while len(header_data) > 0:
            name_length = struct.unpack("I", header_data[:4])[0]
            header_data = header_data[4:]
            name = header_data[:name_length].decode()
            header_data = header_data[name_length:]
            value_length = struct.unpack("I", header_data[:4])[0]
            header_data = header_data[4:]
            value = header_data[:value_length].decode()
            header_data = header_data[value_length:]
            header[name] = value
        return header

    # Modify the send_data function to include the header
    def send_data(self, data, header=None):
        if header is None:
            header = {}

        header_data = self.pack_header(header)
        message = struct.pack("Q", len(header_data)) + header_data + struct.pack("Q", len(data)) + data

        if self.protocol == socket.SOCK_STREAM:
            self.client_socket.sendall(message)
        elif self.protocol == socket.SOCK_DGRAM:
            self.udp_socket.sendto(message, (self.host_address, self.port))

    # Modify the receive_data function to retrieve the header and data
    def receive_data(self):
        while len(self.recv_buf) < PAYLOAD_SIZE:
            if self.protocol == socket.SOCK_STREAM:
                packet = self.client_socket.recv(CHUNK_SIZE)
            elif self.protocol == socket.SOCK_DGRAM:
                packet = self.udp_socket.recvfrom(CHUNK_SIZE)[0]
            if not packet:
                return None
            self.recv_buf += packet

        header_size = struct.unpack("Q", self.recv_buf[:PAYLOAD_SIZE])[0]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]
        header_data = self.recv_buf[:header_size]
        self.recv_buf = self.recv_buf[header_size:]

        header = self.unpack_header(header_data)

        data_size = struct.unpack("Q", self.recv_buf[:PAYLOAD_SIZE])[0]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]

        while len(self.recv_buf) < data_size:
            if self.protocol == socket.SOCK_STREAM:
                self.recv_buf += self.client_socket.recv(CHUNK_SIZE)
            if self.protocol == socket.SOCK_DGRAM:
                self.recv_buf += self.udp_socket.recvfrom(CHUNK_SIZE)[0]

        received_data = self.recv_buf[:data_size]
        self.recv_buf = self.recv_buf[data_size:]

        return header, received_data

    def send_data__old(self, data):
        message = struct.pack("Q", len(data)) + data
        if self.protocol == socket.SOCK_STREAM:
            self.client_socket.sendall(message)
        elif self.protocol == socket.SOCK_DGRAM:
            self.udp_socket.sendto(message, (self.host_address, self.port))

    def receive_data__old(self):
        while len(self.recv_buf) < PAYLOAD_SIZE:
            if self.protocol == socket.SOCK_STREAM:
                packet = self.client_socket.recv(CHUNK_SIZE)
            elif self.protocol == socket.SOCK_DGRAM:
                packet = self.udp_socket.recvfrom(CHUNK_SIZE)[0]
            if not packet:
                return None
            self.recv_buf += packet

        packed_msg_size = self.recv_buf[:PAYLOAD_SIZE]
        self.recv_buf = self.recv_buf[PAYLOAD_SIZE:]
        msg_size = struct.unpack("Q", packed_msg_size)[0]

        while len(self.recv_buf) < msg_size:
            if self.protocol == socket.SOCK_STREAM:
                self.recv_buf += self.client_socket.recv(CHUNK_SIZE)
            if self.protocol == socket.SOCK_DGRAM:
                self.recv_buf += self.udp_socket.recvfrom(CHUNK_SIZE)[0]

        received_data = self.recv_buf[:msg_size]
        self.recv_buf = self.recv_buf[msg_size:]

        # print(f'received {msg_size / 1024:.2f} kB')

        return received_data

    def close_connection(self):
        if self.server_socket:
            self.server_socket.close()
        if self.client_socket:
            self.client_socket.close()


def parse_protocol(protocol):
    if protocol == 'udp' or protocol == 'UDP':
        return socket.SOCK_DGRAM
    elif protocol == 'tcp' or protocol == 'TCP':
        return socket.SOCK_STREAM
    elif protocol == socket.SOCK_DGRAM or protocol == socket.SOCK_STREAM:
        return protocol
    else:
        return None


def get_external_ip():
    import urllib.request
    return urllib.request.urlopen('https://ident.me').read().decode('utf8')
