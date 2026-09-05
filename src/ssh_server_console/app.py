from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import sys

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")
gi.require_version("Vte", "2.91")
from gi.repository import Gdk, Gio, GLib, Gtk, Pango, Vte  # noqa: E402

from .ssh_config import SSHHost, read_hosts


APP_ID = "se.haninge.SSHServerConsole"


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, application: Gtk.Application, config_path: Path) -> None:
        super().__init__(application=application, title="SSH-serverkonsol")
        self.config_path = config_path
        self.set_default_size(1100, 700)
        self.set_icon_name("utilities-terminal")

        header = Gtk.HeaderBar(title="SSH-serverkonsol", subtitle=str(config_path))
        header.set_show_close_button(True)
        self.set_titlebar(header)

        reload_button = Gtk.Button.new_from_icon_name("view-refresh-symbolic", Gtk.IconSize.BUTTON)
        reload_button.set_tooltip_text("Läs om SSH-konfigurationen")
        reload_button.connect("clicked", lambda _button: self.reload_hosts())
        header.pack_start(reload_button)

        config_button = Gtk.Button.new_from_icon_name("document-edit-symbolic", Gtk.IconSize.BUTTON)
        config_button.set_tooltip_text("Öppna ~/.ssh/config")
        config_button.connect("clicked", lambda _button: self.open_config())
        header.pack_end(config_button)

        paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        paned.set_position(300)
        self.add(paned)

        sidebar = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar.set_border_width(10)
        paned.pack1(sidebar, resize=False, shrink=False)

        self.search = Gtk.SearchEntry(placeholder_text="Filtrera servrar")
        self.search.connect("search-changed", lambda _entry: self.populate_list())
        sidebar.pack_start(self.search, False, False, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar.pack_start(scroll, True, True, 0)

        self.host_list = Gtk.ListBox()
        self.host_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.host_list.connect("row-activated", self.on_row_activated)
        scroll.add(self.host_list)

        connect_button = Gtk.Button(label="Anslut")
        connect_button.get_style_context().add_class(Gtk.STYLE_CLASS_SUGGESTED_ACTION)
        connect_button.connect("clicked", lambda _button: self.connect_selected())
        sidebar.pack_end(connect_button, False, False, 0)

        self.notebook = Gtk.Notebook()
        self.notebook.set_scrollable(True)
        paned.pack2(self.notebook, resize=True, shrink=False)

        self.welcome_page = None
        self.show_welcome()
        self.reload_hosts()
        self.connect("key-press-event", self.on_key_press)

    def show_welcome(self) -> None:
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        icon = Gtk.Image.new_from_icon_name("utilities-terminal-symbolic", Gtk.IconSize.DIALOG)
        label = Gtk.Label(label="Välj en server och klicka på Anslut")
        label.get_style_context().add_class("title")
        hint = Gtk.Label(label="Dubbelklick fungerar också · Ctrl+Shift+W stänger en flik")
        hint.get_style_context().add_class("dim-label")
        box.pack_start(icon, False, False, 0)
        box.pack_start(label, False, False, 0)
        box.pack_start(hint, False, False, 0)
        self.welcome_page = box
        self.notebook.append_page(box, Gtk.Label(label="Välkommen"))

    def reload_hosts(self) -> None:
        self.hosts = read_hosts(self.config_path)
        self.populate_list()

    def populate_list(self) -> None:
        for child in self.host_list.get_children():
            self.host_list.remove(child)

        needle = self.search.get_text().casefold().strip()
        for host in self.hosts:
            if needle and needle not in f"{host.alias} {host.details}".casefold():
                continue
            row = Gtk.ListBoxRow()
            row.host = host
            content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
            content.set_border_width(8)
            name = Gtk.Label(label=host.alias, xalign=0)
            name.set_ellipsize(Pango.EllipsizeMode.END)
            details = Gtk.Label(label=host.details, xalign=0)
            details.get_style_context().add_class("dim-label")
            details.set_ellipsize(Pango.EllipsizeMode.MIDDLE)
            content.pack_start(name, False, False, 0)
            content.pack_start(details, False, False, 0)
            row.add(content)
            self.host_list.add(row)

        if not self.hosts:
            row = Gtk.ListBoxRow()
            row.set_sensitive(False)
            label = Gtk.Label(label="Inga konkreta Host-poster hittades", xalign=0)
            label.set_line_wrap(True)
            label.set_border_width(8)
            row.add(label)
            self.host_list.add(row)
        self.host_list.show_all()

    def on_row_activated(self, _list_box: Gtk.ListBox, row: Gtk.ListBoxRow) -> None:
        if hasattr(row, "host"):
            self.open_terminal(row.host)

    def connect_selected(self) -> None:
        row = self.host_list.get_selected_row()
        if row is not None and hasattr(row, "host"):
            self.open_terminal(row.host)

    def open_terminal(self, host: SSHHost) -> None:
        ssh_path = shutil.which("ssh")
        if not ssh_path:
            self.show_error("OpenSSH-klienten kunde inte hittas", "Installera paketet openssh-client.")
            return

        if self.welcome_page is not None:
            welcome_number = self.notebook.page_num(self.welcome_page)
            if welcome_number >= 0:
                self.notebook.remove_page(welcome_number)
            self.welcome_page = None

        terminal = Vte.Terminal()
        terminal.set_scrollback_lines(10000)
        terminal.set_mouse_autohide(True)
        terminal.set_allow_hyperlink(True)
        terminal.set_font(Pango.FontDescription("Monospace 11"))

        tab = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        title = Gtk.Label(label=host.alias)
        close = Gtk.Button.new_from_icon_name("window-close-symbolic", Gtk.IconSize.MENU)
        close.set_relief(Gtk.ReliefStyle.NONE)
        close.set_focus_on_click(False)
        tab.pack_start(title, True, True, 0)
        tab.pack_start(close, False, False, 0)
        tab.show_all()

        page_number = self.notebook.append_page(terminal, tab)
        self.notebook.set_tab_reorderable(terminal, True)
        self.notebook.set_current_page(page_number)
        close.connect("clicked", lambda _button: self.close_terminal(terminal))
        terminal.connect("child-exited", lambda _terminal, status: self.on_child_exited(terminal, title, status))

        environment = [f"{key}={value}" for key, value in os.environ.items()]
        terminal.spawn_async(
            Vte.PtyFlags.DEFAULT,
            str(Path.home()),
            [ssh_path, host.alias],
            environment,
            GLib.SpawnFlags.DEFAULT,
            None,
            None,
            -1,
            None,
            None,
        )
        terminal.show()
        terminal.grab_focus()

    def close_terminal(self, terminal: Vte.Terminal) -> None:
        page = self.notebook.page_num(terminal)
        if page >= 0:
            self.notebook.remove_page(page)
        if self.notebook.get_n_pages() == 0:
            self.show_welcome()
            self.notebook.show_all()

    def on_child_exited(self, terminal: Vte.Terminal, title: Gtk.Label, status: int) -> None:
        title.set_text(f"{title.get_text()} · avslutad")
        terminal.feed(f"\r\n[SSH-sessionen avslutades med status {status}]\r\n".encode())

    def open_config(self) -> None:
        self.config_path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.config_path.touch(mode=0o600, exist_ok=True)
        Gio.AppInfo.launch_default_for_uri(self.config_path.as_uri(), None)

    def show_error(self, title: str, details: str) -> None:
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CLOSE,
            text=title,
        )
        dialog.format_secondary_text(details)
        dialog.run()
        dialog.destroy()

    def on_key_press(self, _widget: Gtk.Widget, event: Gdk.EventKey) -> bool:
        modifiers = event.state & Gtk.accelerator_get_default_mod_mask()
        if modifiers == (Gdk.ModifierType.CONTROL_MASK | Gdk.ModifierType.SHIFT_MASK):
            if event.keyval in (Gdk.KEY_w, Gdk.KEY_W):
                page = self.notebook.get_nth_page(self.notebook.get_current_page())
                if isinstance(page, Vte.Terminal):
                    self.close_terminal(page)
                    return True
            if event.keyval in (Gdk.KEY_r, Gdk.KEY_R):
                self.reload_hosts()
                return True
        return False


class SSHServerConsole(Gtk.Application):
    def __init__(self, config_path: Path) -> None:
        super().__init__(application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.config_path = config_path

    def do_activate(self) -> None:
        window = self.props.active_window
        if window is None:
            window = MainWindow(self, self.config_path)
        window.show_all()
        window.present()


def main() -> int:
    parser = argparse.ArgumentParser(description="Grafisk SSH-serverlista med inbyggda terminalflikar")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path.home() / ".ssh" / "config",
        help="sökväg till OpenSSH-konfigurationen",
    )
    args = parser.parse_args()
    return SSHServerConsole(args.config.expanduser().resolve()).run(sys.argv[:1])
