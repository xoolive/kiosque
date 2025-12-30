# from .aviationweek import AviationWeek
from __future__ import annotations

import logging
from pathlib import Path

import click

from .core.config import config_dict, configuration_file  # noqa: F401
from .core.website import Website
from .tui.tui import main as tui_main


def list_websites() -> None:
    """List all supported websites with their authentication status."""
    website_dir = Path(__file__).parent / "website"
    websites_info = []

    for module_file in sorted(website_dir.glob("*.py")):
        if module_file.stem.startswith("_"):
            continue

        content = module_file.read_text()

        # Extract base_url
        base_url = None
        for line in content.split("\n"):
            if "base_url = " in line and "http" in line:
                # Extract URL from string
                base_url = (
                    line.split('"')[1] if '"' in line else line.split("'")[1]
                )
                break

        # Check if login_url is defined (indicates auth required)
        needs_auth = "login_url = " in content

        # Extract class name for display
        class_name = None
        for line in content.split("\n"):
            if line.startswith("class ") and "(Website)" in line:
                class_name = line.split("class ")[1].split("(")[0]
                break

        if base_url and class_name:
            websites_info.append(
                {
                    "name": class_name,
                    "url": base_url,
                    "auth": "Yes" if needs_auth else "No",
                }
            )

    # Print header
    click.echo("\nSupported Websites:")
    click.echo("=" * 80)
    click.echo(f"{'Website':<30} {'Authentication':<15} {'URL':<35}")
    click.echo("-" * 80)

    # Print websites
    for info in websites_info:
        click.echo(f"{info['name']:<30} {info['auth']:<15} {info['url']:<35}")

    click.echo("=" * 80)
    click.echo(f"\nTotal: {len(websites_info)} websites supported\n")


@click.command(help="Read newspaper articles in textual format")
@click.argument("url_or_alias", required=False)
@click.argument("output", type=click.File("w"), required=False, default=None)
@click.option("-v", "--verbose", count=True, help="Verbosity level")
@click.option(
    "--list-websites",
    "show_list",
    is_flag=True,
    help="List all supported websites",
)
def main(
    url_or_alias: str | None,
    output: Path | None,
    verbose: int,
    show_list: bool,
) -> None:
    # Handle --list-websites flag
    if show_list:
        list_websites()
        return

    # url_or_alias is required if not using --list-websites
    if url_or_alias is None:
        raise click.UsageError("Missing argument 'URL_OR_ALIAS'")

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
