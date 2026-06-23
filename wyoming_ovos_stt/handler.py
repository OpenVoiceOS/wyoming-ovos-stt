import asyncio
import logging

from speech_recognition import AudioData
from wyoming.asr import Transcribe, Transcript, TranscriptStart, TranscriptStop
from wyoming.audio import AudioChunk, AudioChunkConverter, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import Describe, Info
from wyoming.server import AsyncEventHandler
from ovos_plugin_manager.templates.stt import STT

from wyoming_ovos_stt.version import __version__

_LOGGER = logging.getLogger(__name__)


class STTAPIEventHandler(AsyncEventHandler):
    """Wyoming event handler for STT.

    Accumulates audio chunks, runs transcription on AudioStop,
    and sends back a Transcript event (with streaming protocol
    envelope: TranscriptStart / Transcript / TranscriptStop).

    The blocking ``stt.execute()`` call is offloaded to a thread
    to avoid stalling the event loop.
    """

    def __init__(
            self,
            wyoming_info: Info,
            stt: STT,
            *args,
            **kwargs,
    ) -> None:
        super().__init__(*args, **kwargs)
        self.stt = stt
        self.wyoming_info_event = wyoming_info.event()
        self.audio = bytes()
        self.audio_converter = AudioChunkConverter(
            rate=16000,
            width=2,
            channels=1,
        )
        self._language: str | None = None

    # ------------------------------------------------------------------
    # Audio chunk handling
    # ------------------------------------------------------------------

    def handle_audio_chunk(self, event: Event) -> None:
        chunk = AudioChunk.from_event(event)
        chunk = self.audio_converter.convert(chunk)
        self.audio += chunk.audio

    # ------------------------------------------------------------------
    # Core transcription (runs in executor to avoid blocking the loop)
    # ------------------------------------------------------------------

    async def handle_stt(self, audio: bytes) -> str:
        audio_data = AudioData(
            audio,
            sample_rate=self.audio_converter.rate,
            sample_width=self.audio_converter.width,
        )
        text = await asyncio.to_thread(self.stt.execute, audio_data)
        return text

    async def handle_audio_end(self, text: str) -> None:
        # Streaming protocol envelope
        await self.write_event(
            TranscriptStart(language=self._language).event()
        )
        await self.write_event(Transcript(text=text, language=self._language).event())
        await self.write_event(TranscriptStop().event())
        _LOGGER.debug("Completed request: %r", text[:80])
        self.audio = bytes()
        self._language = None

    # ------------------------------------------------------------------
    # Wyoming event dispatch
    # ------------------------------------------------------------------

    async def handle_event(self, event: Event) -> bool:
        try:
            if AudioChunk.is_type(event.type):
                if not self.audio:
                    _LOGGER.debug("Receiving audio")
                self.handle_audio_chunk(event)
                return True

            if AudioStop.is_type(event.type):
                text = await self.handle_stt(self.audio)
                _LOGGER.info(text)
                await self.handle_audio_end(text)
                return False  # single-use handler per faster-whisper pattern

            if Transcribe.is_type(event.type):
                transcribe = Transcribe.from_event(event)
                self._language = transcribe.language
                _LOGGER.debug("Transcribe event (lang=%s)", self._language)
                return True

            if Describe.is_type(event.type):
                await self.write_event(self.wyoming_info_event)
                _LOGGER.debug("Sent info")
                return True

            _LOGGER.debug("Unexpected event: type=%s", event.type)
            return True

        except Exception as err:
            _LOGGER.exception("STT handler error")
            await self.write_event(
                Error(text=str(err), code=err.__class__.__name__).event()
            )
            return False
