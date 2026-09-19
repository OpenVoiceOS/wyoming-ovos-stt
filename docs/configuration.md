# Configuration

CLI flags configure the bridge itself. `mycroft.conf` (the standard OVOS config
stack) configures the **STT plugin**, and the bridge reads it at startup.

## CLI

| Argument | Required | Default | Meaning |
| --- | --- | --- | --- |
| `--plugin-name` | Yes | none | OVOS STT plugin module name (e.g. `ovos-stt-plugin-server`) |
| `--uri` | Yes | none | `tcp://HOST:PORT` or `unix:///path` |
| `--debug` | No | `False` | DEBUG-level logging |
| `--log-format` | No | `%(levelname)s:%(name)s:%(message)s` | Python log format |
| `--version` | No | none | print version and exit |

`--uri` is required (unlike the TTS and wake-word bridges, which default to
`stdio://`) because the STT bridge is meant for a persistent TCP/Unix endpoint.

## Plugin configuration

Plugin settings are read from `mycroft.conf` under `stt.<plugin-name>`. The
section key must match the value passed to `--plugin-name`:

```json
{
  "lang": "en-US",
  "stt": {
    "ovos-stt-plugin-server": {
      "url": "https://stt.openvoiceos.com/stt"
    },
    "ovos-stt-plugin-fasterwhisper": {
      "model": "base",
      "language": "en"
    }
  }
}
```

## Language resolution

For each request, the bridge takes the language from, in order:

1. the `language` field of the Wyoming `Transcribe` event (sent by the client)
2. `stt.<plugin-name>.lang` in `mycroft.conf`
3. the top-level `lang`

The resolved language is advertised in the `Info` response and echoed back on the
`Transcript`.

## Supported plugins

Any plugin implementing `STT` from `ovos_plugin_manager.templates.stt`, e.g.
`ovos-stt-plugin-server`, `ovos-stt-plugin-fasterwhisper`,
`ovos-stt-plugin-vosk`, `ovos-stt-plugin-chromium`. Install the plugin alongside
the bridge. It is not pulled in automatically.

---
[Home](index.md) · [Home Assistant →](home_assistant.md)
