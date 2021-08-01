# from .aviationweek import AviationWeek
import argparse

from .config import config_dict
from .courrierinternational import CourrierInternational
from .lemonde import LeMonde
from .mondediplomatique import MondeDiplomatique
from .pourlascience import PourLaScience


def main():

    newspapers = {
        "courrierinternational": CourrierInternational,
        "mondediplomatique": MondeDiplomatique,
        "pourlascience": PourLaScience,
        "lemonde": LeMonde,
    }

    for key, value in config_dict.items():
        if "alias" in value:
            for alias in value["alias"].split(","):
                newspapers[alias.strip()] = newspapers[key]
            del value["alias"]
        newspapers[key].credentials = value

    parser = argparse.ArgumentParser(description="news command-line interface")

    parser.add_argument(
        "args",
        nargs=argparse.REMAINDER,
        help="all arguments to dispatch to command",
    )

    parser.add_argument(
        "-l",
        dest="list",
        action="store_true",
        help="print the name of the latest edition without downloading",
    )

    args = parser.parse_args()

    getter = newspapers[args.args[0]]()
    getter.login()
    if len(args.args) > 1:
        getter.get_content(args.args[1])
    elif not args.list:
        getter.save_latest_issue()
