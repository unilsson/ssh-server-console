from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
import glob
import re


def ssh_command(
    executable: str,
    alias: str,
    config_path: Path,
    debug_log: Path | None = None,
) -> list[str]:
    command = [executable]
    if debug_log is not None:
        command.extend(["-v", "-E", str(debug_log)])
    if config_path.resolve() != (Path.home() / ".ssh" / "config").resolve():
        command.extend(["-F", str(config_path)])
    return command + ["--", alias]


def config_lines(path: Path, stack: tuple = ()):
    """Expand includes for discovery only; never execute Match exec commands.

    OpenSSH resolves relative user Include paths against ~/.ssh, even with -F.
    """
    path = path.resolve()
    if path in stack or len(stack) >= 16:
        raise ValueError(f"Include-loop eller för stort inkluderingsdjup: {path}")
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        match = re.match(r"^\s*([^\s=#]+)(?:\s*=\s*|\s+)?(.*)$", raw)
        if not match:
            continue
        key = match.group(1).lower()
        try:
            values = shlex.split(match.group(2), comments=True)
        except ValueError as error:
            raise ValueError(f"{path}:{number}: {error}") from error
        if key == "include":
            for pattern in values:
                target = Path(pattern).expanduser()
                if not target.is_absolute():
                    target = Path.home() / ".ssh" / target
                for included in sorted(glob.glob(str(target))):
                    yield from config_lines(Path(included), stack + (path,))
        else:
            yield key, values


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
    Includes are enumerated syntactically; OpenSSH evaluates matching rules.
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

    for key, values in config_lines(config_path):
        value = " ".join(values)
        if key == "host":
            flush()
            aliases = [
                alias
                for alias in values
                if not any(character in alias for character in "*!?")
            ]
            # A Host line may contain several aliases for the same target.
            # Keep only the first concrete name in the graphical server list.
            current_aliases = aliases[:1]
        elif key == "match":
            flush()
        elif current_aliases and key in {"hostname", "user", "port"}:
            # OpenSSH uses the first obtained value for each parameter.
            current.setdefault(key, value)

    flush()
    unique = {}
    for host in hosts:
        unique.setdefault(host.alias, host)
    return sorted(unique.values(), key=lambda host: host.alias.casefold())
