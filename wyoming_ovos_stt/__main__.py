#!/usr/bin/env python3
import argparse
import asyncio
import logging
import signal
from functools import partial

from ovos_config import Configuration
from ovos_plugin_manager.stt import OVOSSTTFactory
from wyoming.info import AsrModel, AsrProgram, Attribution, Info
from wyoming.server import AsyncServer

from wyoming_ovos_stt.handler import STTAPIEventHandler
from wyoming_ovos_stt.version import __version__

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--plugin-name",
        required=True,
        help="OVOS STT plugin to load (matches 'module' in mycroft.conf)",
    )
    parser.add_argument("--uri", required=True, help="unix:// or tcp://")
    parser.add_argument("--debug", action="store_true", help="Log DEBUG messages")
    parser.add_argument(
        "--log-format", default=logging.BASIC_FORMAT,
        help="Format for log messages",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=__version__,
        help="Print version and exit",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format=args.log_format,
    )
    _LOGGER.debug(args)

    cfg = Configuration().get("stt", {}).get(args.plugin_name, {})
    lang = cfg.get("lang") or Configuration().get("lang")
    stt = OVOSSTTFactory.create(
        {"module": args.plugin_name, args.plugin_name: cfg}
    )
    languages = list(stt.available_languages or [lang])

    wyoming_info = Info(
        asr=[
            AsrProgram(
                name=args.plugin_name,
                description="STT via OpenVoiceOS plugins",
                attribution=Attribution(
                    name="OpenVoiceOS",
                    url="https://github.com/OpenVoiceOS/ovos-plugin-manager",
                ),
                installed=True,
                version=__version__,
                supports_transcript_streaming=False,
                models=[
                    AsrModel(
                        name=args.plugin_name,
                        description=f"OVOS STT Plugin: {args.plugin_name}",
                        attribution=Attribution(
                            name="OpenVoiceOS",
                            url="https://github.com/OpenVoiceOS/ovos-plugin-manager",
                        ),
                        installed=True,
                        languages=languages,
                        version=__version__,
                    )
                ],
            )
        ],
    )

    server = AsyncServer.from_uri(args.uri)
    _LOGGER.info("Ready")

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.ensure_future(server.stop()))

    try:
        await server.run(partial(STTAPIEventHandler, wyoming_info, stt))
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass


# -----------------------------------------------------------------------------


def run() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    run()
