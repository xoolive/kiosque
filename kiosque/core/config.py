import configparser
import os
from pathlib import Path
from typing import Dict

from appdirs import user_config_dir

config_dir = Path(user_config_dir("kiosque"))
if xdg_config := os.getenv("XDG_CONFIG_HOME"):
    config_dir = Path(xdg_config) / "kiosque"
configuration_file = config_dir / "kiosque.conf"

if not config_dir.exists():
    configuration_template = """
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
    configuration_file.write_text(configuration_template)

config = configparser.RawConfigParser()
config.read(configuration_file.as_posix())

config_dict: Dict[str, Dict[str, str]] = dict()

for key, value in config.items():
    if key != "DEFAULT":
        config_dict[key] = dict((key, value) for key, value in value.items())
