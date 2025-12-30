# from .aviationweek import AviationWeek
from __future__ import annotations

import logging
from pathlib import Path

import click

from .core.config import config_dict, configuration_file  # noqa: F401
from .core.website import Website
from .tui.tui import main as tui_main


@click.command(help="Read newspaper articles in textual format")
@click.argument("url_or_alias")
@click.argument("output", type=click.File("w"), required=False, default=None)
@click.option("-v", "--verbose", count=True, help="Verbosity level")
def main(url_or_alias: str, output: Path | None, verbose: int) -> None:
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    logger = logging.getLogger()

    if verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose > 1:
        logger.setLevel(logging.DEBUG)

    if isinstance(output, str):
        output = Path(output)

    library: dict[str, type[Website]] = dict()

    for key, value in config_dict.items():
        if not key.startswith("http"):
            continue

        logging.debug(f"Parsing configuration for {key}")
        if not key.endswith("/"):
            key += "/"

        library[key] = website = Website.instance(key).__class__

        if "alias" in value:
            for alias in value["alias"].split(","):
                logging.debug(f"Setting alias '{alias}' for {website}")
                website.alias.append(alias)

            for alias in website.alias:
                library[alias] = website

    logging.debug(f"List of aliases: {library}")

    try:
        if url_or_alias == "tui":
            tui_main()
        elif url_or_alias in library:
            library[url_or_alias]().save_latest_issue()
        elif output is None or isinstance(output, Path):
            instance = Website.instance(url_or_alias)
            instance.write_text(url_or_alias, output)
        else:
            # If it should be written to -
            instance = Website.instance(url_or_alias)
            content = instance.full_text(url_or_alias)
            output.write(content)
    except ValueError as e:
        logging.error(str(e))
        raise click.ClickException(str(e))
    except NotImplementedError as e:
        logging.error(str(e))
        raise click.ClickException(str(e))
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
        if verbose > 0:
            raise
        else:
            raise click.ClickException(
                f"An error occurred. Use -v for more details: {e}"
            )
