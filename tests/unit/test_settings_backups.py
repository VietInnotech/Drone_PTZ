from __future__ import annotations

import os
from pathlib import Path

from src.api.settings_routes import _list_config_backups, _prune_config_backups


def _touch(path: Path, mtime: float) -> None:
    path.write_text(path.name, encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_prune_config_backups_keeps_latest(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("base", encoding="utf-8")

    backups = []
    for idx in range(5):
        backup = tmp_path / f"config.yaml.backup.20260101_00000{idx}"
        _touch(backup, mtime=1000 + idx)
        backups.append(backup)

    removed = _prune_config_backups(config_path, keep_last=2)

    remaining = _list_config_backups(config_path)
    remaining_names = {path.name for path in remaining}
    assert len(remaining) == 2
    assert {backups[-1].name, backups[-2].name} == remaining_names
    assert {path.name for path in removed} == {b.name for b in backups[:-2]}


def test_prune_config_backups_ignores_non_matching_files(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("base", encoding="utf-8")

    backup = tmp_path / "config.yaml.backup.20260101_000000"
    _touch(backup, mtime=2000)

    unrelated = tmp_path / "config.yaml.bak"
    _touch(unrelated, mtime=3000)

    _prune_config_backups(config_path, keep_last=1)

    assert backup.exists()
    assert unrelated.exists()
