"""
SeeRPG Audio Recorder
Records microphone input using sounddevice, applies auto-gain normalization, and exports WAV bytes.
"""
import io
import wave
import numpy as np
import sounddevice as sd
import threading
import logging

logger = logging.getLogger(__name__)

class AudioRecorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self.is_recording = False
        self._frames = []
        self._lock = threading.Lock()
        self._stream = None

    def start_recording(self, device_index=None):
        with self._lock:
            if self.is_recording:
                return
            self._frames = []
            self.is_recording = True

            def callback(indata, frames, time_info, status):
                if status:
                    logger.warning(f"Audio stream status: {status}")
                if self.is_recording:
                    self._frames.append(indata.copy())

            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
                device=device_index,
                callback=callback
            )
            self._stream.start()
            logger.info("Recording started.")

    def stop_recording(self) -> bytes:
        with self._lock:
            if not self.is_recording:
                return b""
            self.is_recording = False
            if self._stream:
                try:
                    self._stream.stop()
                    self._stream.close()
                except Exception as e:
                    logger.error(f"Error stopping audio stream: {e}")
                self._stream = None

            if not self._frames:
                return b""

            audio_data = np.concatenate(self._frames, axis=0)

            # Auto-gain normalization: felerositi a halk mikrofonhangot, hogy a beszed tiszta legyen
            max_amp = np.max(np.abs(audio_data))
            if max_amp > 100:
                target_peak = 25000.0
                gain = min(15.0, max(1.0, target_peak / float(max_amp)))
                audio_data = np.clip(audio_data * gain, -32767, 32767).astype(np.int16)
                logger.info(f"Audio normalized with gain: {gain:.2f}x (original max: {max_amp})")

            # Convert to WAV in memory
            wav_io = io.BytesIO()
            with wave.open(wav_io, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2) # 16-bit
                wf.setframerate(self.sample_rate)
                wf.writeframes(audio_data.tobytes())

            wav_bytes = wav_io.getvalue()
            logger.info(f"Recording stopped. Total size: {len(wav_bytes)} bytes.")
            return wav_bytes

    @staticmethod
    def get_input_devices():
        devices = []
        try:
            for i, dev in enumerate(sd.query_devices()):
                if dev.get("max_input_channels", 0) > 0:
                    devices.append((i, dev.get("name", f"Eszköz {i}")))
        except Exception as e:
            logger.error(f"Error querying audio devices: {e}")
        return devices
