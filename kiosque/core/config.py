import configparser
import logging
import os
import sys
from pathlib import Path

from appdirs import user_config_dir
from pydantic import BaseModel, Field, ValidationError, field_validator


class WebsiteCredentials(BaseModel):
    """Model for website credentials."""

    username: str = Field(..., min_length=1, description="Website username")
    password: str = Field(..., min_length=1, description="Website password")
    alias: str | None = Field(
        None, description="Comma-separated list of aliases"
    )


class RaindropConfig(BaseModel):
    """Model for Raindrop.io configuration."""

    token: str = Field(..., min_length=1, description="Raindrop.io API token")

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Raindrop.io token cannot be empty")
        return v.strip()


class ProxyConfig(BaseModel):
    """Model for proxy configuration."""

    url: str = Field(
        ...,
        min_length=1,
        description="Proxy URL (e.g., socks5://localhost:1080, http://proxy:8080)",
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Proxy URL cannot be empty")
        # Basic validation that it looks like a URL
        if not any(
            v.startswith(proto)
            for proto in ["http://", "https://", "socks4://", "socks5://"]
        ):
            raise ValueError(
                "Proxy URL must start with http://, https://, socks4://, or socks5://"
            )
        return v


class GitHubConfig(BaseModel):
    """Model for GitHub configuration."""

    token: str = Field(
        ..., min_length=1, description="GitHub Personal Access Token"
    )

    @field_validator("token")
    @classmethod
    def validate_token(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("GitHub token cannot be empty")
        return v.strip()


def default_media_directory() -> Path:
    """Use the platform's video directory without executing shell config."""
    if sys.platform == "darwin":
        return Path.home() / "Movies" / "kiosque"
    if sys.platform.startswith("linux"):
        xdg = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config"))
        try:
            for line in (xdg / "user-dirs.dirs").read_text().splitlines():
                if line.startswith("XDG_VIDEOS_DIR="):
                    value = line.split("=", 1)[1].strip().strip('"')
                    value = value.replace("${HOME}", str(Path.home()))
                    value = value.replace("$HOME", str(Path.home()))
                    if "$" not in value and Path(value).is_absolute():
                        return Path(value) / "kiosque"
        except OSError:
            pass
    return Path.home() / "Videos" / "kiosque"


class MediaConfig(BaseModel):
    """Download destination and format-list cache freshness."""

    download_dir: Path = Field(default_factory=default_media_directory)
    cache_ttl: int = Field(default=21600, ge=0)

    @field_validator("download_dir")
    @classmethod
    def expand_download_dir(cls, value: Path) -> Path:
        return value.expanduser().resolve()


class TUIConfig(BaseModel):
    """Model for TUI configuration."""

    refresh_interval: int = Field(
        default=600,
        ge=60,
        description="Auto-refresh interval in seconds (minimum 60)",
    )

    @field_validator("refresh_interval")
    @classmethod
    def validate_refresh_interval(cls, v: int) -> int:
        if v < 60:
            raise ValueError("Refresh interval must be at least 60 seconds")
        return v


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
#
# Raindrop.io configuration (for TUI mode)
# Get your token from https://app.raindrop.io/settings/integrations
# [raindrop.io]
# token =
#
# GitHub configuration (for TUI mode - view starred repos)
# Get your token from https://github.com/settings/tokens
# Create a classic token with 'public_repo' or 'repo' scope
# [github]
# token =
#
# TUI configuration (optional)
# [tui]
# refresh_interval = 600  # Auto-refresh interval (default: 10 min)
#
# Media downloads (optional)
# [media]
# download_dir = ~/Movies/kiosque
# cache_ttl = 21600
#
# Proxy configuration (optional, for geo-blocked websites)
# Supports HTTP, HTTPS, SOCKS4, and SOCKS5 proxies
# [proxy]
# url = socks5://localhost:1080
# or
# url = http://proxy.example.com:8080

    """

    config_dir.mkdir(parents=True)
    configuration_file.write_text(configuration_template)
    logging.info(f"Configuration template created at {configuration_file}")

config = configparser.RawConfigParser()
config.read(configuration_file.as_posix())

config_dict: dict[str, dict[str, str]] = dict()

for key, value in config.items():
    if key != "DEFAULT":
        config_dict[key] = dict((key, value) for key, value in value.items())


def validate_raindrop_config() -> RaindropConfig | None:
    """Validate Raindrop.io configuration if present.

    Returns:
        RaindropConfig if configuration is valid, None if not present.

    Raises:
        ValidationError: If configuration is present but invalid.
    """
    raindrop_data = config_dict.get("raindrop.io")
    if raindrop_data is None:
        return None

    try:
        return RaindropConfig(**raindrop_data)
    except ValidationError as e:
        logging.error(f"Invalid Raindrop.io configuration: {e}")
        raise


def validate_github_config() -> GitHubConfig | None:
    """Validate GitHub configuration if present.

    Returns:
        GitHubConfig if configuration is valid, None if not present.

    Raises:
        ValidationError: If configuration is present but invalid.
    """
    github_data = config_dict.get("github")
    if github_data is None:
        return None

    try:
        return GitHubConfig(**github_data)
    except ValidationError as e:
        logging.error(f"Invalid GitHub configuration: {e}")
        raise


def validate_website_credentials(url: str) -> WebsiteCredentials | None:
    """Validate website credentials if present.

    Args:
        url: The website URL to validate credentials for.

    Returns:
        WebsiteCredentials if configuration is valid, None if not present.

    Raises:
        ValidationError: If configuration is present but invalid.
    """
    creds_data = config_dict.get(url)
    if creds_data is None:
        return None

    try:
        return WebsiteCredentials(**creds_data)
    except ValidationError as e:
        logging.error(f"Invalid credentials for {url}: {e}")
        raise


def validate_proxy_config() -> ProxyConfig | None:
    """Validate proxy configuration if present.

    Returns:
        ProxyConfig if configuration is valid, None if not present.

    Raises:
        ValidationError: If configuration is present but invalid.
    """
    proxy_data = config_dict.get("proxy")
    if proxy_data is None:
        return None

    try:
        return ProxyConfig(**proxy_data)
    except ValidationError as e:
        logging.error(f"Invalid proxy configuration: {e}")
        raise


def validate_media_config() -> MediaConfig:
    """Return configured media settings, or platform defaults."""
    return MediaConfig.model_validate(config_dict.get("media", {}))


def validate_tui_config() -> TUIConfig:
    """Validate TUI configuration if present.

    Returns:
        TUIConfig with default values if not present, or configured
        values if present.

    Raises:
        ValidationError: If configuration is present but invalid.
    """
    tui_data = config_dict.get("tui")
    if tui_data is None:
        return TUIConfig()  # Use defaults

    try:
        return TUIConfig.model_validate(tui_data)
    except ValidationError as e:
        logging.error(f"Invalid TUI configuration: {e}")
        raise
