import argparse
import networking
from soundSender import capture_and_send_audio, capture_and_send_audio_withThread
from soundReceiver import start_receiver_noThread, start_receiver_withThread


def get_parsed_args():
    # Create an argument parser
    parser = argparse.ArgumentParser(description='Send video data to a computer over tcp/ip')

    # Add arguments to the parser
    parser.add_argument('-n', '--host', type=str, help='IP address of host/server')
    parser.add_argument('-p', '--port', type=str, help='Port to run on')
    parser.add_argument('-m', '--mode', type=int, help='Operational Mode: 1: Server/TX, 2: Client/RX, 3: Server/RX, 4: Client/TX')

    # Parse and return the arguments
    return parser.parse_args()


def get_arg_settings(args):
    # set port
    if args.port:
        PORT = int(args.port)
    else:
        PORT = 5000
    # set fps

    # set host address
    if args.host:
        HOST = args.host
    else:
        HOST = '127.0.0.1'

    # OPS_MODE 1:Sender 2:Receiver
    if args.mode:
        OPS_MODE = args.mode
    elif args.host:
        OPS_MODE = 2
    else:
        OPS_MODE = 1

    return PORT, HOST, OPS_MODE


args = get_parsed_args()
PORT, HOST, OPS_MODE = get_arg_settings(args)
PROTOCOL = 'TCP'

if OPS_MODE == 4:
    # Connects and Sends data
    network = networking.NetworkConnection(host_address=HOST, port=PORT, protocol=PROTOCOL)
    network.establish_connection()
    ##client_socket = networking.establish_client_connection(HOST, PORT)
    capture_and_send_audio(network)
if OPS_MODE == 3:
    # Listens for Connection and Receives data
    ##server_socket = networking.start_server(port=PORT)
    ##client_socket, client_address = networking.await_connection(server_socket)
    network = networking.NetworkConnection(port=PORT, protocol=PROTOCOL)
    network.start_server()
    client_socket = network.await_connection()
    start_receiver_noThread(network)
if OPS_MODE == 1:
    # Listens for Connection and Sends data
    ##server_socket = networking.start_server(port=PORT, protocol=PROTOCOL)
    ##client_socket, client_address = networking.await_connection(server_socket)
    network = networking.NetworkConnection(port=PORT, protocol=PROTOCOL)
    network.start_server()
    client_socket = network.await_connection()
    capture_and_send_audio(network)
else:
    # Connects and Receives data
    ##client_socket = networking.establish_client_connection(HOST, PORT)
    network = networking.NetworkConnection(host_address=HOST, port=PORT, protocol=PROTOCOL)
    network.establish_connection()
    start_receiver_noThread(network)
