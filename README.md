# Wyoming OVOS STT Bridge

expose OVOS STT plugins via wyoming for usage with the voice pee

## Usage

```bash
$ wyoming-ovos-stt --help
usage: wyoming-ovos-stt [-h] --plugin-name PLUGIN_NAME --uri URI [--debug] [--log-format LOG_FORMAT] [--version]

options:
  -h, --help            show this help message and exit
  --plugin-name PLUGIN_NAME
                        OVOS STT plugin to load, corresponds to what you would put under "module" in mycroft.conf
  --uri URI             unix:// or tcp://
  --debug               Log DEBUG messages
  --log-format LOG_FORMAT
                        Format for log messages
  --version             Print version and exit

```

e.g.  to use the ovos public servers

> wyoming-ovos-stt --uri tcp://0.0.0.0:7891 --debug --plugin-name ovos-stt-plugin-server 

plugin config is read from mycroft.conf 

![image](https://github.com/user-attachments/assets/01396553-5662-49e8-a5be-58df6f758b64)

---

## Credits

Developed by [TigreGótico](https://tigregotico.pt) for
[OpenVoiceOS](https://openvoiceos.org).

[![NGI0 Commons Fund](./ngi.png)](https://nlnet.nl/project/OpenVoiceOS)

This project was funded through the [NGI0 Commons Fund](https://nlnet.nl/commonsfund),
a fund established by [NLnet](https://nlnet.nl) with financial support from the
European Commission's [Next Generation Internet](https://ngi.eu) programme, under
the aegis of [DG Communications Networks, Content and Technology](https://commission.europa.eu/about-european-commission/departments-and-executive-agencies/communications-networks-content-and-technology_en)
under grant agreement No [101135429](https://cordis.europa.eu/project/id/101135429).
