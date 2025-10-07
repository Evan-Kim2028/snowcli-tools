"""Command group registrations for SnowCLI tools."""

from __future__ import annotations

from typing import Sequence

import click

from .registry import registry


def register_cli_groups(root: click.Group) -> None:
    """Attach registered command groups to the CLI root."""

    for group in registry.iter_groups():
        root.add_command(group)


def get_registered_groups() -> Sequence[str]:
    return tuple(name for name in registry._group_objects)  # type: ignore[attr-defined]
