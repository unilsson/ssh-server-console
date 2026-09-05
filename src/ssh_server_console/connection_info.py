from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class ConnectionInfo:
    address: str = ""
    port: str = ""
    remote_version: str = ""
    kex_algorithm: str = ""
    host_key_algorithm: str = ""
    host_key_fingerprint: str = ""
    cipher_client_to_server: str = ""
    cipher_server_to_client: str = ""
    mac_client_to_server: str = ""
    mac_server_to_client: str = ""
    compression_client_to_server: str = ""
    compression_server_to_client: str = ""
    authentication: str = ""

    def has_details(self) -> bool:
        return any(self.__dict__.values())


def parse_connection_log(text: str) -> ConnectionInfo:
    values: dict[str, str] = {}

    for raw in text.splitlines():
        line = raw.strip()

        match = re.search(r"Connecting to .*?\[([^]]+)\] port (\d+)", line)
        if match:
            values["address"], values["port"] = match.groups()
            continue

        match = re.search(r"Remote protocol version \S+, remote software version (.+)$", line)
        if match:
            values["remote_version"] = match.group(1).strip()
            continue

        match = re.search(r"kex: algorithm: (.+)$", line)
        if match:
            values["kex_algorithm"] = match.group(1).strip()
            continue

        match = re.search(r"kex: host key algorithm: (.+)$", line)
        if match:
            values["host_key_algorithm"] = match.group(1).strip()
            continue

        match = re.search(r"Server host key: \S+ (SHA256:\S+)", line)
        if match:
            values["host_key_fingerprint"] = match.group(1)
            continue

        match = re.search(
            r"client->server cipher: (\S+) MAC: (\S+) compression: (\S+)", line
        )
        if match:
            values["cipher_client_to_server"] = match.group(1)
            values["mac_client_to_server"] = match.group(2)
            values["compression_client_to_server"] = match.group(3)
            continue

        match = re.search(
            r"server->client cipher: (\S+) MAC: (\S+) compression: (\S+)", line
        )
        if match:
            values["cipher_server_to_client"] = match.group(1)
            values["mac_server_to_client"] = match.group(2)
            values["compression_server_to_client"] = match.group(3)
            continue

        match = re.search(r'Authenticated to .* using "([^"]+)"', line)
        if match:
            values["authentication"] = match.group(1)

    return ConnectionInfo(**values)


def read_connection_log(path: Path) -> ConnectionInfo:
    try:
        return parse_connection_log(path.read_text(encoding="utf-8", errors="replace"))
    except OSError:
        return ConnectionInfo()
