import configparser
from pathlib import Path
from typing import Dict

from appdirs import user_config_dir

configuration_dir = Path(user_config_dir("kiosque"))
configuration_file = configuration_dir / "kiosque.conf"

if not configuration_dir.exists():
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

    configuration_dir.mkdir(parents=True)
    configuration_file.write_text(configuration_template)

config = configparser.RawConfigParser()
config.read(configuration_file.as_posix())

config_dict: Dict[str, Dict[str, str]] = dict()

for key, value in config.items():
    if key != "DEFAULT":
        config_dict[key] = dict((key, value) for key, value in value.items())
