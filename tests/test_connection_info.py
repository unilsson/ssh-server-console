import unittest

from ssh_server_console.connection_info import parse_connection_log


class ConnectionInfoTests(unittest.TestCase):
    def test_parses_negotiated_connection_details(self):
        log = """
debug1: Connecting to monitor [192.0.2.20] port 2222.
debug1: Remote protocol version 2.0, remote software version OpenSSH_9.6p1 Ubuntu-3ubuntu13
debug1: kex: algorithm: sntrup761x25519-sha512@openssh.com
debug1: kex: host key algorithm: ssh-ed25519
debug1: Server host key: ssh-ed25519 SHA256:abcdefghijklmnopqrstuvwxyz0123456789
debug1: kex: client->server cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
debug1: kex: server->client cipher: chacha20-poly1305@openssh.com MAC: <implicit> compression: none
Authenticated to monitor ([192.0.2.20]:2222) using "publickey".
"""
        info = parse_connection_log(log)
        self.assertEqual(info.address, "192.0.2.20")
        self.assertEqual(info.port, "2222")
        self.assertEqual(info.remote_version, "OpenSSH_9.6p1 Ubuntu-3ubuntu13")
        self.assertEqual(info.kex_algorithm, "sntrup761x25519-sha512@openssh.com")
        self.assertEqual(info.host_key_algorithm, "ssh-ed25519")
        self.assertEqual(info.host_key_fingerprint, "SHA256:abcdefghijklmnopqrstuvwxyz0123456789")
        self.assertEqual(info.cipher_client_to_server, "chacha20-poly1305@openssh.com")
        self.assertEqual(info.cipher_server_to_client, "chacha20-poly1305@openssh.com")
        self.assertEqual(info.mac_client_to_server, "<implicit>")
        self.assertEqual(info.compression_server_to_client, "none")
        self.assertEqual(info.authentication, "publickey")
        self.assertTrue(info.has_details())

    def test_empty_or_partial_log_is_safe(self):
        info = parse_connection_log("debug1: Connecting to host [203.0.113.8] port 22.\n")
        self.assertEqual(info.address, "203.0.113.8")
        self.assertEqual(info.port, "22")
        self.assertEqual(info.authentication, "")
        self.assertTrue(info.has_details())


if __name__ == "__main__":
    unittest.main()
