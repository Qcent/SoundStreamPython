import argparse
import networking
from soundSender import capture_and_send_audio, capture_and_send_audio_withThread
from soundReceiver import start_receiver_noThread, start_receiver_withThread
import sys
import threading

import cProfile


def prompt_user_to_continue(timeout=10, mode=1):
    print("Would you like to restart? Press 'Y' or 'N':")
    sys.stdout.flush()

    user_input = None
    input_event = threading.Event()

    def get_user_input():
        nonlocal user_input
        user_input = sys.stdin.readline().strip().upper()
        input_event.set()

    input_thread = threading.Thread(target=get_user_input)
    input_thread.start()

    # Wait for user input or timeout
    input_event.wait(timeout)

    if input_event.is_set():
        user_input = user_input or 'N'
    else:
        if mode == 1 or mode == 3:
            return True
        return False

    if user_input == 'Y':
        return True
    elif user_input == 'N':
        return False



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


if __name__ == "__main__":
    args = get_parsed_args()
    PORT, HOST, OPS_MODE = get_arg_settings(args)
    PROTOCOL = 'TCP'
    RUNNING = True
    while RUNNING:
        if OPS_MODE == 4:
            # Connects and Sends data
            network = networking.NetworkConnection(host_address=HOST, port=PORT, protocol=PROTOCOL)
            network.establish_connection()
            capture_and_send_audio(network)
        if OPS_MODE == 3:
            # Listens for Connection and Receives data
            network = networking.NetworkConnection(port=PORT, protocol=PROTOCOL)
            network.start_server()
            client_socket = network.await_connection()
            start_receiver_noThread(network)
        if OPS_MODE == 1:
            # Listens for Connection and Sends data
            network = networking.NetworkConnection(port=PORT, protocol=PROTOCOL, blocking=False)
            network.start_server()
            client_socket = network.await_connection()
            cProfile.run('capture_and_send_audio(network)')
        else:
            # Connects and Receives data
            network = networking.NetworkConnection(host_address=HOST, port=PORT, protocol=PROTOCOL, blocking=False)
            network.establish_connection()
            start_receiver_noThread(network)

        print('Connection has ended...')
        RUNNING = prompt_user_to_continue(timeout=5, mode=OPS_MODE)
