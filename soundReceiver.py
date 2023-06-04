import pyaudio
import networking
import threading
import time
from AudioBuffer import AudioBuffer, AudioSegment, RATE
from FPSCounter import FPSCounter

fps_counter = FPSCounter()
total_time = 0


# call do_fps_counting in main loop
def do_fps_counting(report_frequency=3):
    global total_time
    fps_counter.increment_frame_count()
    if fps_counter.frame_count > report_frequency:
        fps = fps_counter.get_elapsed_time()
        fps_counter.reset()
        total_time += fps
        return f"{fps:.2f}"


# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 2
CHUNK_SIZE = networking.CHUNK_SIZE

# Create an instance of PyAudio
audio = pyaudio.PyAudio()

# Create a buffer to store the received audio data
audio_buffer = AudioBuffer(frame_rate=RATE, channels=CHANNELS)

save_buffer = AudioBuffer(frame_rate=RATE, channels=CHANNELS)


# test function to write received audio data to an mp3 file
def save_audio(audio_data, file_name='test'):
    # Create an AudioSegment from audio_buffer
    audio_segment = AudioSegment(
        audio_data.get_buffer_as_bytes(),
        frame_rate=RATE,  # Replace with your sample rate
        sample_width=2,  # Replace with your sample width in bytes (2 for paInt16)
        channels=CHANNELS  # Replace with your number of channels
    )
    total_audio_length = audio_segment.duration_seconds
    print(f'In just {total_time:.2f} seconds')
    print(f'Decoded Audio Length of: {total_audio_length:.2f} seconds')

    # Calc time stretch factor
    # time_factor = total_audio_length / total_time
    # Stretch the audio segment while preserving pitch
    # stretched_audio = audio_segment.time_stretch(time_factor)  # Stretch by time_factor
    # stretched_audio = audio_buffer.speed_change(audio_segment, speed=time_factor)

    # Convert the WAV audio segment to MP3 format
    mp3_segment = audio_segment.export(out_f=f'{file_name}.mp3', format='mp3')


# Function to receive audio data and add it to the buffer in a threaded loop
def receive_audio_loop(conn):
    sample_length = 0
    loop_count = 0
    while conn.client_socket:
        data = conn.receive_data()

        ### # Convert received data to PCM and add to buffer
        ### audio_buffer.add_data(audio_buffer.mp3_data_to_pcm(data))

        # Convert data to mp3 segment
        ## mp3_segment = audio_buffer.mp3_data_to_segment(data)
        # print(f'audio sample length: {mp3_segment.duration_seconds:.2f} seconds')
        # Convert to PCM and add to buffer
        ## audio_buffer.add_data(audio_buffer.mp3_segment_to_pcm(mp3_segment))

        # Add received pcm data to buffer
        audio_buffer.add_data(data)

        loop_count += 1
        fps = do_fps_counting()
        # sample_length += mp3_segment.duration_seconds
        if fps:
            print(f'In {fps} seconds received {sample_length:.2f} seconds of audio')
            print(f'Samples Received: {loop_count}')
            sample_length = 0


# Function to receive audio data and add it to the buffer
def receive_audio__old(conn):
    # Receive data from the socket
    data = conn.receive_data()
    print(f'audio sample length: {audio_buffer.get_mp3_data_length(data)} seconds')
    # Return pcm audio data
    return audio_buffer.mp3_data_to_pcm(data)


def start_receiver_noThread(conn):
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=pyaudio.get_sample_size(FORMAT))
    play = False
    loop_count = 0
    current_reported_length = 0
    total_reported_length = 0
    total_produced_length = 0
    conn.receive_data()
    current_sample_time_start = time.time()
    while total_reported_length < 42:
        meta_data, sound_sample = conn.receive_data()  # receive_audio__old(conn)
        meta_length = float(meta_data['length'])
        current_reported_length += meta_length
        total_reported_length += meta_length

        sound_data = audio_buffer.convert_to_audio_segment(sound_sample)

        sound_data_length = sound_data.duration_seconds
        total_produced_length += sound_data_length
        #stretch_factor = meta_length / sound_data_length
        audio_buffer.add_data(audio_buffer.mp3_segment_to_pcm(sound_data))
        # audio_buffer.add_data(audio_buffer.speed_change(sound_data, stretch_factor).raw_data)

        loop_count += 1
        fps = do_fps_counting(36)
        if fps:
            print(f'Samples Received: {loop_count} In {fps} seconds')

        buff_size = audio_buffer.get_size()
        if buff_size < 8:
            #if play:
                #print('<< STOPPED >>')
            play = False
        if buff_size > 12:
            play = True
            #print('\t << PLAY >>')
            if buff_size > 32:
                print('\t    << TRUNCATE >>')
                audio_buffer.truncate(8)
        if play:
            pcm_sound = audio_buffer.read_buffer_as_bytes(8)
            # save_buffer.add_data(pcm_sound)
            # stream.write(pcm_sound)
            now_time = time.time()
            experienced_time = now_time - current_sample_time_start

            current_sample_time_start = now_time

            sound_seg = audio_buffer.convert_to_audio_segment(pcm_sound)

            print(f'experienced time: {experienced_time:.2f}s  \
            reported time: {current_reported_length}s \
            decoded time: {sound_seg.duration_seconds}s ')
            stretch_factor = sound_seg.duration_seconds / current_reported_length
            print(f'stretch factor: {stretch_factor:.3f}')

            current_reported_length = 0
            save_buffer.add_data(audio_buffer.speed_change(sound_seg, max(stretch_factor, .85)).raw_data)

            '''conn.client_socket.close()
            print(f'Finished Receiving, Now Saving')
            save_audio(audio_buffer, 'new_test')
            exit()
            '''
    # clear the buffer
    pcm_sound = audio_buffer.get_buffer_as_bytes()
    save_buffer.add_data(pcm_sound)
    print(f'Clearing {len(pcm_sound)/1024:.2f} Kbytes from buffer')
    print(f'Received Reported Audio Length of: {total_reported_length:.2f} seconds')
    save_audio(save_buffer, 'speed_adjust')


def start_receiver_withThread(conn):
    stream = audio.open(format=FORMAT,
                        channels=CHANNELS,
                        rate=RATE,
                        output=True,
                        frames_per_buffer=pyaudio.get_sample_size(FORMAT))

    # 3. Start the receive_audio function in a separate thread
    receive_thread = threading.Thread(target=receive_audio_loop, args=(conn,))
    receive_thread.start()

    play = False
    while True:
        buff_size = audio_buffer.get_size()
        if buff_size < 3:
            play = False
        if buff_size > 256:
            play = True
            if buff_size > 130:
                True
                # audio_buffer.truncate(64)
        if play:
            # sound = audio_buffer.read_buffer_as_bytes(8)
            # stream.write(sound)
            conn.client_socket.close()
            print(f'Finished Receiving, Now Saving')
            save_audio('new_test')
            exit()
