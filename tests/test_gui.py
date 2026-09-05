"""Headless GTK/VTE integration tests. Never connect to an SSH server."""
import os
from pathlib import Path
import tempfile
import time
import unittest
import uuid
from unittest.mock import patch

if not os.environ.get("DISPLAY"):
    raise unittest.SkipTest("GUI tests require xvfb-run and system PyGObject")

from ssh_server_console.app import MainWindow, SSHServerConsole, Gtk, GLib, Vte, Gdk
from ssh_server_console.ssh_config import SSHHost


class GuiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.config = Path(self.temp.name) / 'config'
        self.config.write_text('Host alpha beta\nHostName example.com\n')
        self.app = SSHServerConsole(self.config)
        self.app.set_application_id('se.haninge.Test' + uuid.uuid4().hex)
        self.app.register(None)
        self.window = MainWindow(self.app, self.config)
        self.window.settings_path = Path(self.temp.name) / 'settings.json'
        self.errors = []
        self.window.show_error = lambda *args: self.errors.append(args)
        self.window.show_all()
        self.drain()

    def drain(self):
        context = GLib.MainContext.default()
        while context.pending():
            context.iteration(False)

    def wait_for(self, condition):
        deadline = time.monotonic() + 5
        while not condition() and time.monotonic() < deadline:
            self.drain()
            time.sleep(0.01)
        self.assertTrue(condition(), 'Timed out waiting for VTE lifecycle')

    def tearDown(self):
        self.window.confirm_close = lambda *_: True
        self.window.on_delete()
        self.window.destroy()
        self.drain()
        self.temp.cleanup()

    def open_fake(self, command=None):
        command = command or ['/bin/sh', '-c', 'exit 7']
        with patch('ssh_server_console.ssh_config.ssh_command', return_value=command):
            self.window.open_terminal(SSHHost('alpha'))
        return next(iter(self.window.sessions))

    def test_start_window_and_filter(self):
        self.assertEqual(Gdk._version, '3.0')
        self.assertEqual(len(self.window.host_list.get_children()), 1)
        self.window.search.set_text('no-match')
        self.window.populate_list()
        self.assertEqual(len(self.window.host_list.get_children()), 0)

    def test_real_vte_spawn_exit_and_reconnect(self):
        terminal = self.open_fake()
        self.wait_for(lambda: not self.window.sessions[terminal]['active'])
        session = self.window.sessions[terminal]
        self.assertTrue(session['reconnect'].get_sensitive())
        self.assertIn('avslutad', session['title'].get_text())
        with patch('ssh_server_console.ssh_config.ssh_command', return_value=['/bin/true']):
            self.window.reconnect(terminal)
        self.wait_for(lambda: not session['active'])
        self.assertFalse(self.errors)
        self.window.close_terminal(terminal)
        self.assertEqual(self.window.notebook.get_n_pages(), 1)
        self.assertFalse(self.window.sessions)

    def test_spawn_error_is_reported(self):
        terminal = self.open_fake(['/nonexistent/ssh-console-test'])
        self.wait_for(lambda: not self.window.sessions[terminal]['active'])
        self.assertTrue(self.errors)
        self.assertTrue(self.window.sessions[terminal]['reconnect'].get_sensitive())

    def test_close_confirmation_and_font(self):
        with patch.object(MainWindow, 'start_session'):
            self.window.open_terminal(SSHHost('alpha'))
        terminal = next(iter(self.window.sessions))
        self.window.sessions[terminal]['active'] = True
        self.window.confirm_close = lambda *_: False
        self.window.close_terminal(terminal)
        self.assertIn(terminal, self.window.sessions)
        self.assertTrue(self.window.on_delete())
        self.window.font_size = 11
        self.window.change_font(1)
        self.assertEqual(self.window.font_size, 12)
        self.assertTrue(self.window.settings_path.exists())
        self.assertIn('12', terminal.get_font().to_string())
        self.window.confirm_close = lambda *_: True
        self.window.close_terminal(terminal)
        self.assertFalse(self.window.sessions)

    def test_keyboard_copy_paste(self):
        with patch.object(MainWindow, 'start_session'):
            self.window.open_terminal(SSHHost('alpha'))
        terminal = next(iter(self.window.sessions))
        self.window.sessions[terminal]['active'] = True
        event = Gdk.Event.new(Gdk.EventType.KEY_PRESS)
        event.state = Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK
        with patch.object(Vte.Terminal, 'copy_clipboard_format') as copy:
            event.keyval = Gdk.KEY_C
            self.assertTrue(self.window.on_key_press(self.window, event))
            copy.assert_called_once_with(Vte.Format.TEXT)
        with patch.object(Vte.Terminal, 'paste_clipboard') as paste:
            event.keyval = Gdk.KEY_V
            self.assertTrue(self.window.on_key_press(self.window, event))
            paste.assert_called_once()
