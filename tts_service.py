"""
SeeRPG Text-To-Speech (TTS) Service
Provides discrete in-ear voice feedback using Windows SAPI5 / pyttsx3.
"""
import threading
import queue
import pyttsx3
import logging

logger = logging.getLogger(__name__)

class TTSService:
    def __init__(self, rate: int = 175, volume: float = 0.9):
        self.rate = rate
        self.volume = volume
        self.enabled = True
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def set_enabled(self, enabled: bool):
        self.enabled = enabled

    def set_volume(self, volume: float):
        self.volume = max(0.0, min(1.0, volume))

    def set_rate(self, rate: int):
        self.rate = max(100, min(300, rate))

    def speak(self, text: str):
        if not self.enabled or not text:
            return
        # Put into queue
        self._queue.put(text)

    def _worker(self):
        try:
            engine = pyttsx3.init()
            # Try to find Hungarian voice if available
            voices = engine.getProperty('voices')
            hu_voice = None
            for v in voices:
                if "hungary" in v.name.lower() or "hungarian" in v.name.lower() or "szabolcs" in v.name.lower():
                    hu_voice = v.id
                    break
            if hu_voice:
                engine.setProperty('voice', hu_voice)

            while not self._stop_event.is_set():
                try:
                    text = self._queue.get(timeout=0.5)
                except queue.Empty:
                    continue

                try:
                    engine.setProperty('rate', self.rate)
                    engine.setProperty('volume', self.volume)
                    engine.say(text)
                    engine.runAndWait()
                except Exception as e:
                    logger.error(f"Error in TTS playback: {e}")
                finally:
                    self._queue.task_done()
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3 engine: {e}")

    def shutdown(self):
        self._stop_event.set()
