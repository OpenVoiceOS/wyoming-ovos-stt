# Home Assistant integration

The bridge speaks the Wyoming protocol, so Home Assistant talks to it through the
[Wyoming integration](https://www.home-assistant.io/integrations/wyoming/).

## Add the service

1. Run the bridge on a TCP URI reachable from Home Assistant:

   ```bash
   wyoming-ovos-stt --uri tcp://0.0.0.0:7891 \
                    --plugin-name ovos-stt-plugin-server
   ```

2. In Home Assistant: **Settings → Devices & Services → Add Integration →
   Wyoming Protocol**, and enter the bridge host and port (`7891` above).

3. The new entry exposes a speech-to-text engine. Select it in your
   [Assist pipeline](https://www.home-assistant.io/voice_control/) under
   **Speech-to-text**.

There is no zeroconf announcement for STT — add it by host/port. (The wake-word
bridge does support zeroconf discovery.)

## Notes

- Each transcription uses one connection: the bridge sends the `Transcript` and
  closes, matching the `wyoming-faster-whisper` reference. Home Assistant
  reconnects per utterance automatically.
- Audio is converted to 16 kHz / 16-bit / mono internally, so HA's microphone
  format does not need to match the plugin.
- Run one bridge process per STT plugin/port if you want to offer several engines.
