"""Command registry powering CLI and MCP integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, Iterable, Optional, Type

import click
from pydantic import BaseModel

MCPHandler = Callable[..., object]


@dataclass(frozen=True)
class CommandDescriptor:
    """Metadata describing a single command available in the toolchain."""

    name: str
    group: str
    cli_handler: click.Command
    description: str
    schema: Optional[Type[BaseModel]] = None
    mcp_handler: Optional[MCPHandler] = None


class CommandRegistry:
    """Central registry for CLI/MCP command metadata."""

    def __init__(self) -> None:
        self._commands: Dict[str, Dict[str, CommandDescriptor]] = {}
        self._group_objects: Dict[str, click.Group] = {}

    def register_group(self, group: click.Group) -> None:
        """Register a top-level command group."""

        if group.name is None:
            raise ValueError("Command groups must define a name")
        self._group_objects[group.name] = group
        self._commands.setdefault(group.name, {})

    def register(self, descriptor: CommandDescriptor) -> None:
        """Register a command descriptor under its group."""

        group_commands = self._commands.setdefault(descriptor.group, {})
        if descriptor.name in group_commands:
            raise ValueError(
                f"Command '{descriptor.name}' already registered for group '{descriptor.group}'"
            )
        group_commands[descriptor.name] = descriptor

    def iter_groups(self) -> Iterable[click.Group]:
        """Yield registered click groups with attached commands."""

        for name, group in self._group_objects.items():
            for descriptor in self._commands.get(name, {}).values():
                if descriptor.cli_handler not in group.commands.values():
                    group.add_command(descriptor.cli_handler, name=descriptor.name)
            yield group

    def get_descriptor(self, group: str, name: str) -> CommandDescriptor:
        try:
            return self._commands[group][name]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Unknown command {group}:{name}") from exc


registry = CommandRegistry()
