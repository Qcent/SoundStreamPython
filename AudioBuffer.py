from pydub import AudioSegment
from io import BytesIO

RATE = 48000


class AudioBuffer:
    def __init__(self, frame_rate=RATE, sample_width=2, channels=2):
        self.buffer = b""
        self.frame_rate = frame_rate
        self.sample_width = sample_width
        self.channels = channels
        self.length = 0

    def add_data(self, data):
        self.buffer += data
        self.length += len(data)

    def retrieve_data(self, length=None):
        if length is None:
            data = self.buffer
            self.buffer = b""
            self.length = 0
        else:
            data = self.buffer[:length]
            self.buffer = self.buffer[length:]
            self.length -= length

        return data

    def clear(self):
        self.buffer = b""
        self.length = 0

    def get_size(self):
        return self.length

    def truncate(self, length):
        self.buffer = self.buffer[:length]
        self.length = length

    def get_buffer_as_bytes(self, length=None):
        if length is None:
            bytes_array = self.buffer
        else:
            bytes_array = self.buffer[:length]
        return bytes_array

    def convert_pcm_to_mp3(self, pcm_data, bitrate='320'):
        # Create AudioSegment from buffer
        audio_segment = AudioSegment(
            pcm_data,
            frame_rate=self.frame_rate,
            sample_width=self.sample_width,
            channels=self.channels
        )
        # Convert the WAV audio segment to MP3 format
        mp3_data = audio_segment.export(format='mp3', bitrate=bitrate)

        return mp3_data.read(), audio_segment

    @staticmethod
    def mp3_data_to_pcm(mp3_data):
        mp3_segment = AudioSegment.from_file(BytesIO(mp3_data), format='mp3')
        return mp3_segment.raw_data

    @staticmethod
    def convert_to_audio_segment(audio_data, frame_rate=RATE, sample_width=2, channels=2):
        audio_segment = AudioSegment(
            audio_data,
            frame_rate=frame_rate,
            sample_width=sample_width,
            channels=channels
        )
        return audio_segment

    @staticmethod
    def segment_to_pcm(segment):
        return segment.raw_data

    @staticmethod
    def get_audio_length(audio_data, audio_format='wav'):
        audio_segment = AudioSegment.from_file(BytesIO(audio_data), format=audio_format)
        duration = audio_segment.duration_seconds
        return duration

    @staticmethod
    def speed_change(segment, speed=1.0):
        # Manually override the frame_rate to speed or slow audio segments
        sound_with_altered_frame_rate = segment._spawn(segment.raw_data, overrides={
            "frame_rate": int(segment.frame_rate * speed)
        })

        # Convert the sound with altered frame rate back to original frame rate
        return sound_with_altered_frame_rate.set_frame_rate(segment.frame_rate)
