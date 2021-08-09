# from .aviationweek import AviationWeek
from __future__ import annotations

import logging
from pathlib import Path
from typing import Type

import click

from .core.config import config_dict, configuration_file  # noqa: F401
from .core.website import Website


@click.command(help="Read newspaper articles in textual format")
@click.argument("url_or_alias")
@click.argument("output", type=click.File("w"), required=False, default=None)
@click.option("-v", "--verbose", count=True, help="Verbosity level")
def main(url_or_alias: str, output: Path | None, verbose: int):
    logger = logging.getLogger()
    if verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose > 1:
        logger.setLevel(logging.DEBUG)

    if isinstance(output, str):
        output = Path(output)

    library: dict[str, Type[Website]] = dict()

    for key, value in config_dict.items():
        logging.debug(f"Parsing configuration for {key}")
        if not key.endswith("/"):
            key += "/"

        library[key] = website = Website.instance(key).__class__

        if "alias" in value:
            for alias in value["alias"].split(","):
                website.alias.append(alias)

        for alias in website.alias:
            library[alias] = website

    if url_or_alias in library:
        library[url_or_alias]().save_latest_issue()
    elif output is None or isinstance(output, Path):
        instance = Website.instance(url_or_alias)
        instance.write_text(url_or_alias, output)
    else:
        # If it should be written to -
        instance = Website.instance(url_or_alias)
        content = instance.full_text(url_or_alias)
        output.write(content)
