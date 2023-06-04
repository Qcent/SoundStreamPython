import pyaudio
import threading
import networking
from AudioBuffer import AudioBuffer

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 48000
CHUNK_SIZE = networking.CHUNK_SIZE

# Create an instance of PyAudio
audio = pyaudio.PyAudio()

# Create a buffer to store the received audio data
audio_buffer = AudioBuffer(frame_rate=RATE, channels=CHANNELS)

buffer_lock = threading.Lock()


# Function to play audio from the buffer
def play_audio():
    # Open an audio stream for output
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=CHUNK_SIZE)

    while True:
        # Get audio data from the buffer
        # print(f'Buffer Size: {audio_buffer.get_size()}')
        if audio_buffer.get_size() > 2:
            '''
            print(f'Buffer Size: {audio_buffer.get_size()}')
            mp3_data = audio_buffer.retrieve_data()
            print(f'Buffer Size after: {audio_buffer.get_size()}')
            #print(f'mp3 bytes:')
            #print(mp3_data)
            pcm_data = audio_buffer.mp3_data_to_pcm(mp3_data)
            #print(f'pcm bytes:')
            #print(pcm_data[-10:])
            # Play the audio data
            '''
            buffer_lock.acquire()
            mp3_data = audio_buffer.get_buffer_as_bytes()
            audio_buffer.clear()
            buffer_lock.release()

            stream.write(audio_buffer.mp3_data_to_pcm(mp3_data))

    # Stop and close the audio stream
    stream.stop_stream()
    stream.close()


# Function to receive audio data and add it to the buffer
def receive_audio(sock):
    while True:
        # Receive data from the socket
        # data = sock.recv(CHUNK_SIZE)
        data = networking.receive_over_network(sock)
        # Add the received data to the buffer

        buffer_lock.acquire()
        # print('lockout tagout: receive audio')
        audio_buffer.add_data(data)
        buffer_lock.release()


def start_receiver(conn):
    # 1. Start the audio playback in a separate thread
    playback_thread = threading.Thread(target=play_audio)
    playback_thread.start()

    # 2. Set up the socket connection (socket creation and connection)...
    ### Emily client_socket = networking.establish_client_connection('76.68.117.20', 5000)
    ### client_socket = networking.establish_client_connection('127.0.0.1', 5000)

    # 3. Start the receive_audio function in a separate thread
    receive_thread = threading.Thread(target=receive_audio, args=(conn,))
    receive_thread.start()

    # 3. Continue with other tasks or input capturing...

    # 4. When finished, join the threads to wait for their completion
    receive_thread.join()
    playback_thread.join()

    # Close the PyAudio instance
    audio.terminate()


# start_receiver()
