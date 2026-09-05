from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex


@dataclass(frozen=True)
class SSHHost:
    alias: str
    hostname: str = ""
    user: str = ""
    port: str = ""

    @property
    def details(self) -> str:
        destination = self.hostname or self.alias
        if self.user:
            destination = f"{self.user}@{destination}"
        if self.port and self.port != "22":
            destination = f"{destination}:{self.port}"
        return destination


def _clean_line(raw_line: str) -> str:
    lexer = shlex.shlex(raw_line, posix=True)
    lexer.whitespace_split = True
    lexer.commenters = "#"
    return " ".join(lexer)


def read_hosts(config_path: Path) -> list[SSHHost]:
    """Read concrete Host entries from an OpenSSH client config.

    Wildcard/negated patterns are intentionally excluded because they are
    configuration rules rather than destinations a user can connect to.
    Includes still affect ssh itself but are not recursively enumerated here.
    """
    if not config_path.exists():
        return []

    hosts: list[SSHHost] = []
    current_aliases: list[str] = []
    current: dict[str, str] = {}

    def flush() -> None:
        nonlocal current_aliases, current
        for alias in current_aliases:
            hosts.append(
                SSHHost(
                    alias=alias,
                    hostname=current.get("hostname", ""),
                    user=current.get("user", ""),
                    port=current.get("port", ""),
                )
            )
        current_aliases = []
        current = {}

    for raw_line in config_path.read_text(encoding="utf-8", errors="replace").splitlines():
        line = _clean_line(raw_line).strip()
        if not line:
            continue
        key, _, value = line.partition(" ")
        key = key.lower()
        value = value.strip()
        if key == "host":
            flush()
            aliases = [
                alias
                for alias in value.split()
                if not any(character in alias for character in "*!?")
            ]
            # A Host line may contain several aliases for the same target.
            # Keep only the first concrete name in the graphical server list.
            current_aliases = aliases[:1]
        elif current_aliases and key in {"hostname", "user", "port"}:
            # OpenSSH uses the first obtained value for each parameter.
            current.setdefault(key, value)

    flush()
    return sorted({host.alias: host for host in hosts}.values(), key=lambda host: host.alias.casefold())
