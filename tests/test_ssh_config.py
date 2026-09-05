from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ssh_server_console.ssh_config import read_hosts, ssh_command


class SSHConfigTests(unittest.TestCase):
    def parse(self, content):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config"
            path.write_text(content)
            return read_hosts(path)

    def test_equals_comments_and_first_alias(self):
        hosts = self.parse('Host=alpha beta # alias\nHostName = example.com\nUser=admin\n')
        self.assertEqual(len(hosts), 1)
        self.assertEqual(hosts[0].alias, "alpha")
        self.assertEqual(hosts[0].details, "admin@example.com")

    def test_match_does_not_change_previous_host(self):
        hosts = self.parse('Host alpha\nMatch exec "never execute me"\nUser wrong\nHost beta\nUser admin')
        self.assertEqual(hosts[0].user, "")
        self.assertEqual(hosts[1].user, "admin")

    def test_first_duplicate_wins(self):
        hosts = self.parse('Host alpha\nUser first\nHost alpha\nUser second')
        self.assertEqual(hosts[0].user, "first")

    def test_bad_quote_has_line_number(self):
        with self.assertRaisesRegex(ValueError, 'config:2'):
            self.parse('Host alpha\nUser "unterminated')

    def test_include_glob_spaces_relative_and_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            sshdir = home / '.ssh'
            sshdir.mkdir()
            includes = sshdir / 'hosts folder'
            includes.mkdir()
            (includes / 'a.conf').write_text('Host alpha alpha.local\nUser admin')
            (includes / 'b.conf').write_text('Host beta\nPort 2222')
            root = home / 'custom-config'
            root.write_text('Include "hosts folder/*.conf"\nInclude missing/*.conf')
            with patch('pathlib.Path.home', return_value=home):
                self.assertEqual([h.alias for h in read_hosts(root)], ['alpha', 'beta'])
                (includes / 'b.conf').write_text(f'Include {root}')
                with self.assertRaisesRegex(ValueError, 'Include-loop'):
                    read_hosts(root)

    def test_custom_config_is_forwarded_without_shell(self):
        config = Path('/tmp/config with spaces')
        self.assertEqual(ssh_command('/usr/bin/ssh', 'alpha', config),
                         ['/usr/bin/ssh', '-F', str(config), '--', 'alpha'])

    def test_default_config_preserves_system_config(self):
        self.assertEqual(ssh_command('/usr/bin/ssh', 'alpha', Path.home() / '.ssh/config'),
                         ['/usr/bin/ssh', '--', 'alpha'])

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
