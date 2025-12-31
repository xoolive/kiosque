# Agent development guide

## Setup commands

- Run `uv sync --dev`

## Coding style

- Run `uv run ruff check` and `uv run ruff format` to check and format code
- Run `uvx ty check kiosque/ tests/` to check types
- Use `prettier` to format markdown files

## Commit rules

- **NEVER COMMIT ANYTHING WITHOUT EXPLICIT APPROVAL**: encourage the developer to check the code before committing
- **DO NOT COMMIT DIRECTLY TO THE MAIN BRANCH**
- Create a feature branch from main for your changes

## Project structure

- kiosque/core/ - Core functionality (client, website base class, config)
- kiosque/website/ - Individual website scrapers (30+ files)
- kiosque/api/ - API integrations (Raindrop.io, Pocket - deprecated)
- kiosque/tui/ - Terminal UI with Textual

