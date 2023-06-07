import pyaudiowpatch as pyaudio
import threading
import networking
import time
from AudioBuffer import AudioBuffer, RATE
from FPSCounter import FPSCounter

fps_counter = FPSCounter()


# call do_fps_counting in main loop
def do_fps_counting(freq=30):
    fps_counter.increment_frame_count()
    if fps_counter.frame_count > freq:
        fps = fps_counter.get_fps()
        tt = fps_counter.get_elapsed_time()
        fps_counter.reset()
        return f"Sending {fps:.2f} samples per second \n\t In {tt:.4f} seconds"


# Audio settings
FORMAT = pyaudio.paInt16
CHUNK_SIZE = networking.CHUNK_SIZE
BITRATE = '128'

payload_size = networking.PAYLOAD_SIZE


# Function to capture and send audio data
def capture_and_send_audio(conn):
    sound_device = find_loopback_device()

    print(f"Recording from: ({sound_device['index']}){sound_device['name']}")
    print(f'Sample rate: {int(sound_device["defaultSampleRate"])}')
    print(f'frames per sample: {pyaudio.get_sample_size(FORMAT)}')

    audio_buffer = AudioBuffer(frame_rate=RATE,
                               sample_width=pyaudio.get_sample_size(FORMAT),
                               channels=1 # sound_device["maxInputChannels"]
                               )

    def audio_capture_callback(in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        audio_buffer.add_data(in_data)
        return in_data, pyaudio.paContinue

    def send_audio(data, sound_length):
        return conn.send_data(data, header={
            "length": f"{sound_length:.5f}",
        })

    # Create an instance of PyAudio
    audio = pyaudio.PyAudio()

    with audio.open(format=FORMAT,
                    channels=sound_device["maxInputChannels"],
                    rate=RATE,  # int(sound_device["defaultSampleRate"]),
                    frames_per_buffer=pyaudio.get_sample_size(FORMAT),
                    input=True,
                    input_device_index=sound_device["index"],
                    stream_callback=audio_capture_callback
                    ) as stream:
        running_sample_length = 0
        sound_start = time.time()
        fps_counter.reset()
        while True:
            # Read audio data from the stream
            #  #audio_capture_callback() will add audio data to buffer

            # Send the audio data over the socket
            if audio_buffer.length >= CHUNK_SIZE * 12:
                # timing stuff
                time_now = time.time()
                sound_length = time_now - sound_start
                sound_start = time_now
                # grab the audio buffer
                out = audio_buffer.retrieve_data(audio_buffer.length)
                # Convert to mp3
                # mp3_data, sound_seg = audio_buffer.convert_pcm_to_mp3(out, BITRATE)

                if not send_audio(out, sound_length):
                    break

                sound_seg = audio_buffer.convert_to_audio_segment(out)
                running_sample_length += sound_seg.duration_seconds

                fps = do_fps_counting(15)
                if fps:
                    print(fps)
                    print(f'produced an audio sample of {running_sample_length:.4f}s')
                    running_sample_length = 0

        conn.close_connection()
        audio.close(stream)


# Function to capture and send audio data with separate threads for each
def capture_and_send_audio_withThread(conn):
    sound_device = find_loopback_device()

    print(f"Recording from: ({sound_device['index']}){sound_device['name']}")
    print(f'Sample rate: {int(sound_device["defaultSampleRate"])}')
    print(f'frames per sample: {pyaudio.get_sample_size(FORMAT)}')

    audio_buffer = AudioBuffer(frame_rate=RATE,
                               sample_width=pyaudio.get_sample_size(FORMAT),
                               channels=sound_device["maxInputChannels"]
                               )

    capture_thread = threading.Thread(target=capture_loop, args=(audio_buffer, sound_device))
    capture_thread.start()

    while True:
        # Read audio data from the stream
        #  #capture_thread will add audio data to buffer
        audio_buffer_size = audio_buffer.get_size()
        # Send the audio data over the socket
        if audio_buffer_size * payload_size >= CHUNK_SIZE:
            # print(f'Compressing {audio_buffer_size*payload_size / 1024:.2f} kB')
            ##out = audio_buffer.to_mp3_data(bitrate=BITRATE)
            ##audio_buffer.clear()
            out = audio_buffer.read_buffer_as_bytes(audio_buffer_size)
            # audio_buffer.truncate((audio_buffer.get_size()-audio_buffer_size))
            # print(f'Compressed size:{len(out)}')
            conn.send_data(out)
            fps = do_fps_counting()
            if fps:
                print(fps)


def capture_loop(audio_buffer, device):
    def audio_capture_callback(in_data, frame_count, time_info, status):
        """Write frames and return PA flag"""
        audio_buffer.add_data(in_data)
        return in_data, pyaudio.paContinue

    # Create an instance of PyAudio
    audio = pyaudio.PyAudio()

    with audio.open(format=FORMAT,
                    channels=device["maxInputChannels"],
                    rate=RATE,
                    frames_per_buffer=pyaudio.get_sample_size(FORMAT),
                    input=True,
                    input_device_index=device["index"],
                    stream_callback=audio_capture_callback
                    ) as stream:
        while True:
            True


def find_loopback_device():
    with pyaudio.PyAudio() as audio:
        try:
            # Get default WASAPI info
            wasapi_info = audio.get_host_api_info_by_type(pyaudio.paWASAPI)
        except OSError:
            print("Looks like WASAPI is not available on the system. Exiting...")
            exit()

        # Get default WASAPI speakers
        default_speakers = audio.get_device_info_by_index(wasapi_info["defaultOutputDevice"])
        if not default_speakers["isLoopbackDevice"]:
            for loopback in audio.get_loopback_device_info_generator():
                """
                Try to find loopback device with same name(and [Loopback suffix]).
                Unfortunately, this is the most adequate way at the moment.
                """
                if default_speakers["name"] in loopback["name"]:
                    default_speakers = loopback
                    break
            else:
                print("Default loopback output device not found.\nRun this to check available devices.\nExiting...\n")
                exit()
    return default_speakers


'''
# Example usage:
# 1. Set up the socket connection (socket creation and connection)...
server_socket = networking.start_server(port=5000)
client_socket, client_address = networking.await_connection(server_socket)

# 2. Start the capture_and_send_audio function in a separate thread
send_audio_thread = threading.Thread(target=capture_and_send_audio, args=(client_socket,))
send_audio_thread.start()

# 3. Continue with other tasks or input capturing...

# 4. When finished, join the threads to wait for their completion
send_audio_thread.join()

# Close the PyAudio instance
# audio.terminate()
'''
