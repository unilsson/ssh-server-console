from pathlib import Path
import tempfile
import unittest

from ssh_server_console.ssh_config import read_hosts


class SSHConfigTests(unittest.TestCase):
    def test_reads_concrete_hosts_and_skips_patterns(self) -> None:
        contents = """
        Host *
            ServerAliveInterval 30

        Host monitor
            HostName 192.0.2.20
            User admin

        Host proxmox-1 proxmox-2
            User root
            Port 2222

        Host *.example.test !blocked.example.test
            User ignored
        """
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config"
            path.write_text(contents)
            hosts = read_hosts(path)

        self.assertEqual([host.alias for host in hosts], ["monitor", "proxmox-1"])
        self.assertEqual(hosts[0].details, "admin@192.0.2.20")
        self.assertEqual(hosts[1].details, "root@proxmox-1:2222")

    def test_missing_config_is_empty(self) -> None:
        self.assertEqual(read_hosts(Path("/definitely/missing/ssh-config")), [])


if __name__ == "__main__":
    unittest.main()
