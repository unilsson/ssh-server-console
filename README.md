# SSH-serverkonsol

En liten lokal Ubuntu-app som visar konkreta `Host`-poster från
`~/.ssh/config` och öppnar vanliga OpenSSH-sessioner i inbyggda terminalflikar.

Appen lagrar inga lösenord eller nycklar. Den kör systemets `/usr/bin/ssh`, så
befintliga inställningar för nycklar, ssh-agent, YubiKey, ProxyJump, portar,
known_hosts och algoritmer används oförändrade.

## Funktioner i version 0.1

- Serverlista från `~/.ssh/config`
- Sökfält
- Anslut med dubbelklick eller knappen **Anslut**
- Flera flyttbara terminalflikar
- Knapp för att öppna och redigera SSH-konfigurationen
- Omladdning av serverlistan
- `Ctrl+Shift+W` stänger aktuell terminalflik
- `Ctrl+Shift+R` läser om serverlistan

Wildcard-poster som `Host *` visas inte som servrar, men OpenSSH tillämpar dem
fortfarande när en anslutning öppnas. `Include`-filer läses av OpenSSH vid
anslutning men deras alias listas ännu inte av appen.

Om en rad innehåller flera namn, exempelvis `Host server server.local 10.0.0.5`,
visas endast det första namnet (`server`) i listan.

## Exempel på SSH-konfiguration

```sshconfig
Host monitor
    HostName 192.0.2.20
    User admin

Host proxmox-1
    HostName 192.0.2.10
    User root

Host gitea
    HostName git.example.com
    User git
    Port 2222
```

## Installation på Ubuntu

Packa upp projektet, öppna en terminal i katalogen och kör:

```bash
chmod +x install.sh uninstall.sh
./install.sh
```

Starta därefter **SSH-serverkonsol** från programmenyn eller kör:

```bash
~/.local/bin/ssh-server-console
```

Om din SSH-konfiguration ligger på en annan plats:

```bash
~/.local/bin/ssh-server-console --config /annan/sökväg/config
```

## Köra utan installation

Installera systemberoendena:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-vte-2.91 openssh-client
```

Kör sedan från projektkatalogen:

```bash
PYTHONPATH=src python3 -m ssh_server_console
```

## Tester

Parsertesterna kräver inte GTK:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

## Avinstallation

```bash
./uninstall.sh
```

Avinstallationen rör aldrig `~/.ssh`.
