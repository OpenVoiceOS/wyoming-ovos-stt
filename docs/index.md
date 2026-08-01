# wyoming-ovos-stt documentation

Expose any [OpenVoiceOS](https://openvoiceos.org) STT plugin as a
[Wyoming protocol](https://github.com/OHF-voice/wyoming) ASR server, for use with
Home Assistant, Rhasspy, and other Wyoming-compatible voice pipelines.

The bridge loads one OVOS `STT` plugin (selected with `--plugin-name`), converts
incoming Wyoming audio to 16 kHz / 16-bit / mono, runs the plugin's blocking
`execute()` off the event loop, and returns a single `Transcript`.

## Pages

- **[Configuration](configuration.md)**: selecting a plugin and its
  `mycroft.conf` settings, and how the bridge resolves the language.
- **[Home Assistant](home_assistant.md)**: adding the bridge as a Wyoming STT
  service.
- **[Wyoming protocol](protocol.md)**: the event flow and why the bridge sends
  a single `Transcript` (matching `wyoming-faster-whisper`).

## Quickstart

```bash
pip install wyoming-ovos-stt ovos-stt-plugin-server

# TCP server backed by the public OVOS STT servers
wyoming-ovos-stt --uri tcp://0.0.0.0:7891 \
                 --plugin-name ovos-stt-plugin-server
```

Point Home Assistant's Wyoming integration at `host:7891`. See
[Home Assistant](home_assistant.md) for details.

## Docker

```bash
docker build -t wyoming-ovos-stt .
docker run --rm -p 7891:7891 wyoming-ovos-stt \
    --uri tcp://0.0.0.0:7891 --plugin-name ovos-stt-plugin-server
```

The image installs the package (and its dependencies) from `pyproject.toml`; add
any extra STT plugin you intend to load to the image or mount its config.
