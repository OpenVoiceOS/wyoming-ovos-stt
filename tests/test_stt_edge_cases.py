"""Edge-case tests for STT handler (audio formats, errors, non-ASCII)."""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest
from wyoming.asr import Transcribe
from wyoming.audio import AudioChunk, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import AsrProgram, Attribution, Info

from wyoming_ovos_stt.handler import STTAPIEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


def _handler(stt=None):
    reader, writer = _streams()
    if stt is None:
        stt = MagicMock()
        stt.execute.return_value = "test"
        stt.available_languages = ["en-US"]
    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(asr=[
        AsrProgram(name="test", attribution=attr, description="test",
                   installed=True, version="1.0", models=[])
    ])
    return STTAPIEventHandler(wyoming_info, stt, reader=reader, writer=writer)


@pytest.mark.asyncio
async def test_audio_at_different_sample_rates():
    """Audio at 8 kHz is converted to 16 kHz."""
    handler = _handler()
    pcm_8k = b"\x00\x00" * 80  # 80 samples at 8 kHz = 10 ms
    chunk = AudioChunk(rate=8000, width=2, channels=1, audio=pcm_8k)
    await handler.handle_event(chunk.event())
    assert len(handler.audio) > 0
    assert handler.audio != pcm_8k


@pytest.mark.asyncio
async def test_audio_with_different_width():
    """Audio at 8-bit width is converted to 16-bit."""
    handler = _handler()
    pcm_8bit = b"\x80" * 160  # 8-bit samples
    chunk = AudioChunk(rate=16000, width=1, channels=1, audio=pcm_8bit)
    await handler.handle_event(chunk.event())
    assert len(handler.audio) == 320  # doubled by width conversion
    assert handler.audio != pcm_8bit


@pytest.mark.asyncio
async def test_stereo_to_mono_conversion():
    """Stereo audio is converted to mono."""
    handler = _handler()
    stereo = b"\x00\x00\x01\x00" * 160  # interleaved L/R
    chunk = AudioChunk(rate=16000, width=2, channels=2, audio=stereo)
    await handler.handle_event(chunk.event())
    assert len(handler.audio) == 320  # half the interleaved stereo


@pytest.mark.asyncio
async def test_empty_audio_bytes_no_crash():
    """Empty audio bytes in a chunk does not crash."""
    handler = _handler()
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"")
    result = await handler.handle_event(chunk.event())
    assert result is True
    assert handler.audio == b""


@pytest.mark.asyncio
async def test_non_ascii_transcript():
    """Handler passes non-ASCII text through unchanged."""
    fake_stt = MagicMock()
    fake_stt.execute.return_value = "café français 中文 русский"
    fake_stt.available_languages = ["en-US"]
    handler = _handler(fake_stt)

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await handler.handle_event(chunk.event())
    await handler.handle_event(AudioStop().event())

    transcript_events = [e for e in captured if e.type == "transcript"]
    assert len(transcript_events) == 1
    assert "café" in str(transcript_events[0].data)


@pytest.mark.asyncio
async def test_error_on_stt_failure():
    """Handler sends Error event when STT execution raises."""
    failing_stt = MagicMock()
    failing_stt.execute.side_effect = RuntimeError("boom")
    failing_stt.available_languages = ["en-US"]
    handler = _handler(failing_stt)

    captured = []

    async def capture(event):
        captured.append(event)

    handler.write_event = capture

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await handler.handle_event(chunk.event())
    result = await handler.handle_event(AudioStop().event())
    assert result is False
    error_events = [e for e in captured if e.type == "error"]
    assert len(error_events) == 1  # handler sends Error event on failure
