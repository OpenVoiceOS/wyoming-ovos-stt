# Wyoming protocol

## Event flow

```
Client → Describe
Server → Info(asr=[AsrProgram(name="ovos-stt-plugin-server", ...)])

Client → Transcribe(language="en-US")
Client → AudioStart(rate=16000, width=2, channels=1)
       → AudioChunk (PCM bytes)
       → AudioChunk ...
       → AudioStop
Server → Transcript(text="hello world", language="en-US")
```

The connection is closed after each transcription (single-use handler, like
`wyoming-faster-whisper`). Audio is converted to 16 kHz / 16-bit / mono PCM
automatically, so any input format works.

## A single Transcript, not a streaming envelope

OVOS STT plugins are **non-streaming**: `STT.execute()` returns the full text
once, with no partial hypotheses. The bridge therefore:

- advertises `supports_transcript_streaming=False` in the `Info` response, and
- sends one `Transcript(text, language)` — **not** a
  `TranscriptStart` / `TranscriptChunk` / `TranscriptStop` envelope.

This matches the upstream `wyoming-faster-whisper` server. A degenerate envelope
(a `TranscriptStart`/`TranscriptStop` pair with no `TranscriptChunk`) would
contradict the advertised non-streaming flag and offers no benefit.

## Threading

`STT.execute()` is blocking, so it is run via `asyncio.to_thread()`; the event
loop stays responsive while a slow plugin transcribes.

## Errors

If an exception occurs while handling an event, the bridge reports it to the
client as a Wyoming `Error(text, code)` event and closes the connection.

---
[← Home Assistant](home_assistant.md) · [Home](index.md)
