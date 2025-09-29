"""Shared helpers for command modules."""

from __future__ import annotations

import click


class DefaultCommandGroup(click.Group):
    """Click Group that allows invoking a default subcommand."""

    def __init__(self, *args, default_command: str | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_command = default_command

    def resolve_command(self, ctx: click.Context, args: list[str]):  # type: ignore[override]
        if not args and self.default_command:
            return super().resolve_command(ctx, [self.default_command])

        try:
            return super().resolve_command(ctx, args)
        except click.UsageError:
            if self.default_command:
                new_args = [self.default_command, *args]
                return super().resolve_command(ctx, new_args)
            raise
