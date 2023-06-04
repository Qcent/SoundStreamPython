import queue
from pydub import AudioSegment
from io import BytesIO

RATE = 48000


class AudioBuffer:
    def __init__(self, frame_rate=RATE, sample_width=2, channels=2):
        self.buffer = queue.Queue()
        self.frame_rate = frame_rate
        self.sample_width = sample_width
        self.channels = channels

    def add_data(self, data):
        self.buffer.put(data)

    def retrieve_data(self):
        if not self.buffer.empty():
            return self.buffer.get()
        else:
            return None

    def clear(self):
        self.buffer.queue.clear()

    def get_size(self):
        return self.buffer.qsize()

    def truncate(self, length):
        items_to_remove = self.buffer.qsize() - length
        if items_to_remove > 1:
            for _ in range(items_to_remove):
                self.buffer.get()

    def read_buffer_as_bytes(self, length=1):
        buffer_list = []
        for _ in range(length):
            buffer_list.append(self.buffer.get())
        bytes_array = b''.join(buffer_list)
        return bytes_array

    def get_buffer_as_bytes(self, length=None):
        buffer_list = list(self.buffer.queue)
        bytes_array = b''.join(buffer_list)
        if length is not None:
            bytes_array = bytes_array[:length]
        return bytes_array

    def to_mp3_data(self, bitrate=None):
        # Create AudioSegment from buffer
        audio_segment = AudioSegment(
            self.get_buffer_as_bytes(),
            frame_rate=self.frame_rate,
            sample_width=2,
            channels=2
        )
        # Convert the WAV audio segment to MP3 format
        mp3_data = audio_segment.export(format='mp3', bitrate=bitrate)

        return mp3_data.read()

    def to_mp3_segment(self,  bitrate=None):
        # Create AudioSegment from buffer
        audio_segment = AudioSegment(
            self.get_buffer_as_bytes(),
            frame_rate=self.frame_rate,
            sample_width=2,
            channels=2
        )
        # Convert the WAV audio segment to MP3 format
        mp3_data = audio_segment.export(format='mp3', bitrate=bitrate)
        # Convert mp3 data to AudioSegment
        return AudioSegment.from_file(BytesIO(mp3_data.read()), format='wav')

    @staticmethod
    def mp3_data_to_pcm(mp3_data):
        mp3_segment = AudioSegment.from_file(BytesIO(mp3_data), format='mp3')
        return mp3_segment.raw_data

    @staticmethod
    def convert_to_audio_segment(audio_data, frame_rate=RATE, sample_width=2, channels=2):
        audio_segment = AudioSegment(
            audio_data,
            frame_rate=frame_rate,  # Replace with your sample rate
            sample_width=sample_width,  # Replace with your sample width in bytes (2 for paInt16)
            channels=channels,  # Replace with your number of channels
        )
        return audio_segment

    @staticmethod
    def mp3_segment_to_pcm(mp3_segment):
        return mp3_segment.raw_data

    @staticmethod
    def get_audio_length(audio_data, audio_format='wav'):
        audio_segment = AudioSegment.from_file(BytesIO(audio_data), format=audio_format)
        duration = audio_segment.duration_seconds
        return duration

    @staticmethod
    def speed_change(sound, speed=1.0):
        # Manually override the frame_rate to speed or slow audio segments
        sound_with_altered_frame_rate = sound._spawn(sound.raw_data, overrides={
            "frame_rate": int(sound.frame_rate * speed)
        })

        # Convert the sound with altered frame rate back to original frame rate
        return sound_with_altered_frame_rate.set_frame_rate(sound.frame_rate)
