# Wyoming OVOS STT Bridge

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](pyproject.toml)
[![Wyoming](https://img.shields.io/badge/wyoming-1.9+-blueviolet.svg)](https://github.com/OHF-voice/wyoming)
[![OVOS](https://img.shields.io/badge/OVOS-plugin--manager-ff69b4.svg)](https://github.com/OpenVoiceOS/ovos-plugin-manager)

Expose any [OpenVoiceOS](https://openvoiceos.org) STT plugin as a [Wyoming protocol](https://github.com/OHF-voice/wyoming) ASR server for use with Home Assistant, Rhasspy, and other Wyoming-compatible voice pipelines.

```
                         ┌──────────────────────────────────────┐
  Wyoming client         │         wyoming-ovos-stt              │
  (Home Assistant,       │                                      │
   Rhasspy, etc.)        │  ┌────────────────────────────────┐  │
                         │  │   STTAPIEventHandler           │  │
  Transcribe ───────────►│  │                                │  │
  AudioChunk* ──────────►│  │  AudioChunkConverter           │  │
                         │  │  (→ 16kHz/16-bit/mono)         │  │
  AudioStop  ───────────►│  │  asyncio.to_thread() ──────────►│  OVOSSTTFactory
                         │  │  STT.execute(AudioData)        │  └──> STT plugin
  Transcript ◄───────────│  │                                │
  Describe ─────────────►│  │  Info(asr=[AsrProgram(...)])    │
  Info ◄─────────────────│  │                                │
                         │  └────────────────────────────────┘  │
                         └──────────────────────────────────────┘
```

## Features

- **Single `Transcript` response** — OVOS STT plugins are non-streaming, so the full text is returned in one `Transcript` (matching the `wyoming-faster-whisper` reference)
- **Automatic audio conversion** — All incoming audio is converted to 16 kHz / 16-bit / mono PCM via `AudioChunkConverter`
- **Thread-safe** — Blocking `stt.execute()` is offloaded via `asyncio.to_thread()` so the event loop stays responsive
- **Language propagation** — Reads `language` from `Transcribe` event and populates it on `Transcript`
- **Error reporting** — Failures are sent back as Wyoming `Error` events
- **Signal handling** — Graceful shutdown on SIGINT/SIGTERM

## Installation

### From PyPI

```bash
pip install wyoming-ovos-stt
```

You also need to install the OVOS STT plugin you intend to bridge, e.g.:

```bash
pip install ovos-stt-plugin-server
pip install ovos-stt-plugin-whisper
pip install ovos-stt-plugin-vosk
```

### From source

```bash
git clone https://github.com/OpenVoiceOS/wyoming-ovos-stt.git
cd wyoming-ovos-stt
pip install -e .
```

## Configuration

Plugin configuration is read from `mycroft.conf` under `stt.<plugin-name>`:

```json
{
  "lang": "en-US",
  "stt": {
    "ovos-stt-plugin-server": {
      "url": "https://stt.openvoiceos.com/stt"
    },
    "ovos-stt-plugin-whisper": {
      "model": "base",
      "language": "en"
    },
    "ovos-stt-plugin-vosk": {
      "model": "vosk-model-small-en-us-0.15"
    }
  }
}
```

The language is taken from `stt.<plugin-name>.lang` if set, otherwise from `lang` at the root level.

## Usage

```bash
# TCP server using public OVOS STT servers
wyoming-ovos-stt --uri tcp://0.0.0.0:7891 \
                 --plugin-name ovos-stt-plugin-server \
                 --debug

# Local Whisper STT
wyoming-ovos-stt --uri tcp://0.0.0.0:7891 \
                 --plugin-name ovos-stt-plugin-whisper

# Unix socket
wyoming-ovos-stt --uri unix:///run/wyoming-stt.sock \
                 --plugin-name ovos-stt-plugin-vosk
```

## CLI Reference

| Argument | Required | Default | Description |
|---|---|---|---|
| `--plugin-name` | Yes | — | OVOS STT plugin module name (e.g. `ovos-stt-plugin-server`) |
| `--uri` | **Yes** | — | `tcp://HOST:PORT` or `unix:///path` |
| `--debug` | No | `False` | Enable DEBUG-level logging |
| `--log-format` | No | `%(levelname)s:%(name)s:%(message)s` | Python log format string |
| `--version` | No | — | Print version and exit |

> **Note:** `--uri` is required (unlike the TTS and wake-word bridges which default to `stdio://`) because the STT bridge is designed for persistent TCP connections.

## Wyoming Protocol

### Transcription flow

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

The connection is closed after each transcription (single-use handler pattern, matching the upstream `wyoming-faster-whisper` reference). Audio must be 16 kHz / 16-bit / mono PCM; the bridge converts automatically.

## Supported Plugin Types

Any OVOS STT plugin implementing `STT` from `ovos_plugin_manager.templates.stt`:

- `ovos-stt-plugin-server` — proxy to remote STT servers
- `ovos-stt-plugin-whisper` — OpenAI Whisper (local)
- `ovos-stt-plugin-vosk` — Vosk offline speech recognition
- `ovos-stt-plugin-chromium` — Chrome/Chromium's Web Speech API
- `ovos-stt-plugin-pocketsphinx` — CMU PocketSphinx
- `ovos-stt-plugin-whispercpp` — Whisper.cpp binding
- `ovos-stt-plugin-faster-whisper` — CTranslate2-accelerated Whisper
- `ovos-stt-plugin-google` — Google Cloud Speech-to-Text
- `ovos-stt-plugin-azure` — Microsoft Azure Speech
- `ovos-stt-plugin-amazon` — Amazon Transcribe

## Credits

Developed by [TigreGótico](https://tigregotico.pt) for [OpenVoiceOS](https://openvoiceos.org).

[![NGI0 Commons Fund](./ngi.png)](https://nlnet.nl/project/OpenVoiceOS)

This project was funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) programme, under
the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en)
under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429).
