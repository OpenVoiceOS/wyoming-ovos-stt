"""Protocol-level tests for wyoming-ovos-stt.

Tests the Wyoming streaming transcript envelope (TranscriptStart/Transcript/TranscriptStop)
without an actual STT plugin by exercising the handler's output events.
"""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock, AsyncMock

import pytest
from wyoming.asr import Transcribe, Transcript, TranscriptStart, TranscriptStop
from wyoming.audio import AudioChunk, AudioStop
from wyoming.event import Event
from wyoming.info import AsrProgram, Attribution, Info

from wyoming_ovos_stt.handler import STTAPIEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


@pytest.mark.asyncio
async def test_transcript_envelope():
    """Handler sends TranscriptStart, Transcript, TranscriptStop on AudioStop."""
    reader, writer = _streams()
    fake_stt = MagicMock()
    fake_stt.execute.return_value = "test transcript"
    fake_stt.available_languages = ["en-US"]
    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(asr=[
        AsrProgram(name="test", attribution=attr, description="test", installed=True, version="1.0", models=[])
    ])

    h = STTAPIEventHandler(wyoming_info, fake_stt, reader=reader, writer=writer)

    captured = []

    async def capture(event):
        captured.append(event)

    h.write_event = capture

    await h.handle_event(Transcribe(language="en-US").event())
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await h.handle_event(chunk.event())
    await h.handle_event(AudioStop().event())

    types = [e.type for e in captured]
    assert "transcript-start" in types
    assert "transcript" in types
    assert "transcript-stop" in types

    transcript_events = [e for e in captured if e.type == "transcript"]
    assert len(transcript_events) == 1
    t = Transcript.from_event(transcript_events[0])
    assert t.text == "test transcript"
    assert t.language == "en-US"


@pytest.mark.asyncio
async def test_empty_audio_no_crash():
    """Empty audio (no AudioChunk before AudioStop) returns empty transcript."""
    reader, writer = _streams()
    fake_stt = MagicMock()
    fake_stt.execute.return_value = ""
    fake_stt.available_languages = ["en-US"]
    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(asr=[
        AsrProgram(name="test", attribution=attr, description="test", installed=True, version="1.0", models=[])
    ])

    h = STTAPIEventHandler(wyoming_info, fake_stt, reader=reader, writer=writer)

    captured = []

    async def capture(event):
        captured.append(event)

    h.write_event = capture

    await h.handle_event(AudioStop().event())
    types = [e.type for e in captured]
    assert "transcript-start" in types
    assert "transcript" in types
    assert "transcript-stop" in types
