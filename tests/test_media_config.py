"""Platform destination defaults and media configuration validation."""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kiosque.core import config


def test_macos_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(config.sys, "platform", "darwin")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    assert config.MediaConfig().download_dir == tmp_path / "Movies/kiosque"


def test_linux_xdg_destination(tmp_path, monkeypatch):
    monkeypatch.setattr(config.sys, "platform", "linux")
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    dirs = tmp_path / "user-dirs.dirs"
    dirs.write_text('XDG_VIDEOS_DIR="$HOME/Custom Videos"\n')
    assert (
        config.MediaConfig().download_dir == tmp_path / "Custom Videos/kiosque"
    )
    dirs.write_text('XDG_VIDEOS_DIR="$(run-command)/Videos"\n')
    assert config.MediaConfig().download_dir == tmp_path / "Videos/kiosque"


def test_media_config_override(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setitem(
        config.config_dict,
        "media",
        {
            "download_dir": "~/Video Archive",
            "cache_ttl": "60",
        },
    )
    settings = config.validate_media_config()
    assert settings.download_dir == tmp_path / "Video Archive"
    assert settings.cache_ttl == 60


def test_negative_cache_ttl_rejected():
    with pytest.raises(ValidationError):
        config.MediaConfig(cache_ttl=-1)
