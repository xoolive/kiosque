# Installation

## Requirements

- Python 3.12 or higher
- Internet connection
- Optional: Raindrop.io account, GitHub account

---

## Installation Methods

=== "uv (Recommended)"

    [uv](https://github.com/astral-sh/uv) is the fastest Python package installer.

    ```bash
    # Install uv if you don't have it
    curl -LsSf https://astral.sh/uv/install.sh | sh

    # Install kiosque as a tool
    uv tool install kiosque

    # Or install in a virtual environment
    uv venv
    source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
    uv pip install kiosque
    ```

=== "pip"

    ```bash
    # Install globally
    pip install kiosque

    # Or in a virtual environment (recommended)
    python -m venv .venv
    source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
    pip install kiosque
    ```

=== "pipx"

    [pipx](https://github.com/pypa/pipx) installs CLI tools in isolated environments.

    ```bash
    # Install pipx if you don't have it
    python -m pip install --user pipx
    python -m pipx ensurepath

    # Install kiosque
    pipx install kiosque
    ```

=== "From Source"

    ```bash
    # Clone the repository
    git clone https://github.com/xoolive/kiosque.git
    cd kiosque

    # Install with uv
    uv sync

    # Or with pip
    pip install -e .
    ```

---

## Verify Installation

```bash
# Check version
kiosque --version

# Test CLI
kiosque --help

# Test TUI (requires configuration)
kiosque tui
```

---

## Optional Dependencies

### For Development

```bash
# Install with dev dependencies
uv sync --dev

# Includes:
# - pytest (testing)
# - ruff (linting/formatting)
# - textual-dev (TUI development)
# - mkdocs-material (documentation)
```

### For Geo-Blocked Sites

Some sites require proxies. Install proxy support:

```bash
pip install httpx-socks
# or
uv pip install httpx-socks
```

This is included by default in kiosque.

---

## Configuration File Location

Kiosque looks for configuration at:

- **Linux/macOS**: `~/.config/kiosque/kiosque.conf`
- **Windows**: `%APPDATA%\kiosque\kiosque.conf`

You can also set a custom location:

```bash
export XDG_CONFIG_HOME=/path/to/config
```

The configuration file will be created automatically on first run.

---

## Next Steps

- **[Configuration Guide](configuration.md)** - Set up authentication
- **[Quick Start](../index.md)** - First steps with kiosque
- **[TUI Guide](../features/tui-guide.md)** - Master the terminal interface
