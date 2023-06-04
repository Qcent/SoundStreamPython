import pyaudiowpatch as pyaudio
from AudioBuffer import AudioBuffer
import time
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO

duration = 6.9

if __name__ == "__main__":
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

        print(f"Recording from: ({default_speakers['index']}){default_speakers['name']}")
        print(f'Sample rate: {int(default_speakers["defaultSampleRate"])}')
        print(f'frames per sample: {pyaudio.get_sample_size(pyaudio.paInt16)}')

        audio_buffer = AudioBuffer(frame_rate=int(default_speakers["defaultSampleRate"]),
                                   sample_width=pyaudio.get_sample_size(pyaudio.paInt16),
                                   channels=default_speakers["maxInputChannels"]
                                   )


        def callback(in_data, frame_count, time_info, status):
            """Write frames and return PA flag"""
            audio_buffer.add_data(in_data)
            return (in_data, pyaudio.paContinue)


        with audio.open(format=pyaudio.paInt16,
                        channels=default_speakers["maxInputChannels"],
                        rate=int(default_speakers["defaultSampleRate"]),
                        frames_per_buffer=pyaudio.get_sample_size(pyaudio.paInt16),
                        input=True,
                        input_device_index=default_speakers["index"],
                        stream_callback=callback
                        ) as stream:

            print(f"The next {duration} seconds will be written to test.mp3")
            time.sleep(duration)  # Blocking execution while playing

    # Create an AudioSegment from audio_buffer
    audio_segment = AudioSegment(
        audio_buffer.get_buffer_as_bytes(),
        frame_rate=44100,  # Replace with your sample rate
        sample_width=2,  # Replace with your sample width in bytes (2 for paInt16)
        channels=2  # Replace with your number of channels
    )

    # Convert the WAV audio segment to MP3 format
    mp3_segment = audio_segment.export(out_f='test.mp3', format='mp3')

    # Get the MP3 audio data as a byte string
    mp3_data = mp3_segment.read()

    # Convert mp3 data to AudioSegment
    mp3_segment = AudioSegment.from_file(BytesIO(mp3_data), format='mp3')

    # Play the MP3 audio segment
    print('Playing MP3 DATA from memory')
    play(mp3_segment)

    # Open a PyAudio stream
    audio = pyaudio.PyAudio()
    stream = audio.open(format=audio.get_format_from_width(mp3_segment.sample_width),
                        channels=mp3_segment.channels,
                        rate=mp3_segment.frame_rate,
                        output=True)

    # Play the PCM audio data
    print('Playing PCM DATA Converted from MP3')
    stream.write(mp3_segment.raw_data)

    # Stop the stream
    stream.stop_stream()
    stream.close()

    # Terminate PyAudio
    audio.terminate()
