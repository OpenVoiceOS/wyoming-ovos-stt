"""Protocol-level tests for wyoming-ovos-stt.

OVOS STT plugins are non-streaming, so the handler emits a single
``Transcript`` (matching the wyoming-faster-whisper reference) rather than a
``TranscriptStart`` / ``TranscriptChunk`` / ``TranscriptStop`` envelope.
"""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest
from wyoming.asr import Transcribe, Transcript
from wyoming.audio import AudioChunk, AudioStop
from wyoming.info import AsrProgram, Attribution, Info

from wyoming_ovos_stt.handler import STTAPIEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


def _handler(return_value="test transcript"):
    reader, writer = _streams()
    fake_stt = MagicMock()
    fake_stt.execute.return_value = return_value
    fake_stt.available_languages = ["en-US"]
    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(asr=[
        AsrProgram(name="test", attribution=attr, description="test",
                   installed=True, version="1.0", models=[])
    ])
    h = STTAPIEventHandler(wyoming_info, fake_stt, reader=reader, writer=writer)
    captured = []

    async def capture(event):
        captured.append(event)

    h.write_event = capture
    return h, captured


@pytest.mark.asyncio
async def test_single_transcript_with_language():
    """AudioStop yields exactly one Transcript carrying the requested language."""
    h, captured = _handler("test transcript")

    await h.handle_event(Transcribe(language="en-US").event())
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await h.handle_event(chunk.event())
    await h.handle_event(AudioStop().event())

    transcript_events = [e for e in captured if e.type == "transcript"]
    assert len(transcript_events) == 1
    t = Transcript.from_event(transcript_events[0])
    assert t.text == "test transcript"
    assert t.language == "en-US"


@pytest.mark.asyncio
async def test_no_streaming_envelope():
    """The handler does not emit transcript-start / transcript-stop events."""
    h, captured = _handler("hello")

    await h.handle_event(Transcribe(language="en-US").event())
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await h.handle_event(chunk.event())
    await h.handle_event(AudioStop().event())

    types = [e.type for e in captured]
    assert "transcript" in types
    assert "transcript-start" not in types
    assert "transcript-stop" not in types


@pytest.mark.asyncio
async def test_empty_audio_no_crash():
    """Empty audio (no AudioChunk before AudioStop) still emits one Transcript."""
    h, captured = _handler("")

    await h.handle_event(AudioStop().event())

    transcript_events = [e for e in captured if e.type == "transcript"]
    assert len(transcript_events) == 1
    assert Transcript.from_event(transcript_events[0]).text == ""


@pytest.mark.asyncio
async def test_audio_stop_closes_connection():
    """AudioStop returns False (single-use handler, like faster-whisper)."""
    h, _ = _handler("done")
    result = await h.handle_event(AudioStop().event())
    assert result is False
