import configparser
from pathlib import Path
from typing import Dict

from appdirs import user_config_dir

config_dir = Path(user_config_dir("kiosque"))
config_file = config_dir / "kiosque.conf"

if not config_dir.exists():
    config_template = """
# [https://www.nytimes.com/]
# username =
# password =
#
# Add more newspapers as you wish below
# [https://www.lemonde.fr/]
# username =
# password =

    """

    config_dir.mkdir(parents=True)
    config_file.write_text(config_template)

config = configparser.RawConfigParser()
config.read(config_file.as_posix())

config_dict: Dict[str, Dict[str, str]] = dict()

for key, value in config.items():
    if key != "DEFAULT":
        config_dict[key] = dict((key, value) for key, value in value.items())
