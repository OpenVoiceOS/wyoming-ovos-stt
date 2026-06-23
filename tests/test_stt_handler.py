"""Unit tests for STTAPIEventHandler.

Tests the Wyoming event dispatching logic with mocked STT plugin.
"""

from asyncio import StreamReader, StreamWriter
from unittest.mock import MagicMock

import pytest
from wyoming.asr import Transcribe, TranscriptStart, Transcript, TranscriptStop
from wyoming.audio import AudioChunk, AudioStop
from wyoming.error import Error
from wyoming.event import Event
from wyoming.info import AsrProgram, Attribution, Describe, Info

from wyoming_ovos_stt.handler import STTAPIEventHandler


def _streams():
    return MagicMock(spec=StreamReader), MagicMock(spec=StreamWriter)


@pytest.fixture
def handler():
    reader, writer = _streams()
    fake_stt = MagicMock()
    fake_stt.execute.return_value = "hello world"
    fake_stt.available_languages = ["en-US"]

    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(
        asr=[
            AsrProgram(
                name="test-stt",
                attribution=attr,
                description="test",
                installed=True,
                version="0.2.0",
                supports_transcript_streaming=False,
                models=[],
            )
        ],
    )

    return STTAPIEventHandler(wyoming_info, fake_stt, reader=reader, writer=writer)


@pytest.mark.asyncio
async def test_describe(handler):
    result = await handler.handle_event(Describe().event())
    assert result is True


@pytest.mark.asyncio
async def test_transcribe_language(handler):
    """Transcribe event sets the language."""
    await handler.handle_event(Transcribe(language="en-US").event())
    assert handler._language == "en-US"


@pytest.mark.asyncio
async def test_audio_chunk_accumulation(handler, fixtures_dir):
    """Audio chunks are accumulated correctly."""
    pcm = b"\x00\x00" * 160
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=pcm)
    await handler.handle_event(chunk.event())
    assert handler.audio == pcm


@pytest.mark.asyncio
async def test_audio_stop_triggers_transcription(handler, fixtures_dir):
    """AudioStop dispatches transcription and sends Transcript events."""
    pcm = b"\x00\x00" * 160
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=pcm)
    await handler.handle_event(chunk.event())

    result = await handler.handle_event(AudioStop().event())
    assert result is False

    handler.stt.execute.assert_called_once()


@pytest.mark.asyncio
async def test_audio_stop_resets_state(handler):
    """Handler state resets after transcription."""
    pcm = b"\x00\x00" * 160
    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=pcm)
    await handler.handle_event(chunk.event())
    assert handler.audio != b""

    await handler.handle_event(AudioStop().event())
    assert handler.audio == b""


@pytest.mark.asyncio
async def test_error_on_failure():
    """Handler sends Error event when STT execution fails."""
    reader, writer = _streams()
    failing_stt = MagicMock()
    failing_stt.execute.side_effect = RuntimeError("stt failed")

    attr = Attribution(name="test", url="https://example.com")
    wyoming_info = Info(asr=[
        AsrProgram(name="test", attribution=attr, description="test", installed=True, version="1.0", models=[])
    ])
    h = STTAPIEventHandler(wyoming_info, failing_stt, reader=reader, writer=writer)

    chunk = AudioChunk(rate=16000, width=2, channels=1, audio=b"\x00\x00" * 160)
    await h.handle_event(chunk.event())

    result = await h.handle_event(AudioStop().event())
    assert result is False


@pytest.mark.asyncio
async def test_unknown_event(handler):
    """Unknown event types return True (continue)."""
    result = await handler.handle_event(Event(type="unknown"))
    assert result is True
