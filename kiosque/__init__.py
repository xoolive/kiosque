# from .aviationweek import AviationWeek
from __future__ import annotations

import logging
from pathlib import Path
from typing import Type

import click

from .core.config import config_dict
from .core.website import Website


@click.command()
@click.argument("url_or_alias")
@click.option("--output", "-o", type=click.Path(), default=None)
@click.option("-v", "--verbose", count=True, help="Verbosity level")
def main(url_or_alias: str, output: Path | None, verbose: int):
    logger = logging.getLogger()
    if verbose == 1:
        logger.setLevel(logging.INFO)
    elif verbose > 1:
        logger.setLevel(logging.DEBUG)

    if output is not None:
        output = Path(output)

    library: dict[str, Type[Website]] = dict()

    for key, value in config_dict.items():
        library[key] = website = Website.instance(key).__class__

        if "alias" in value:
            for alias in value["alias"].split(","):
                website.alias.append(alias)

        for alias in website.alias:
            library[alias] = website

    if url_or_alias in library:
        library[url_or_alias]().save_latest_issue()
    else:
        instance = Website.instance(url_or_alias)
        instance.write_text(url_or_alias, output)
