# SSH-serverkonsol

En liten lokal Ubuntu-app som visar konkreta `Host`-poster från
`~/.ssh/config` och öppnar vanliga OpenSSH-sessioner i inbyggda terminalflikar.

Appen lagrar inga lösenord eller nycklar. Den kör systemets `/usr/bin/ssh`, så
befintliga inställningar för nycklar, ssh-agent, YubiKey, ProxyJump, portar,
known_hosts och algoritmer används oförändrade.

## Funktioner i version 0.2

- Serverlista från `~/.ssh/config`
- Sökfält
- Anslut med dubbelklick eller knappen **Anslut**
- Flera flyttbara terminalflikar
- Knapp för att öppna och redigera SSH-konfigurationen
- Omladdning av serverlistan
- `Ctrl+Shift+W` stänger aktuell terminalflik
- `Ctrl+Shift+R` läser om serverlistan
- Kopiera med `Ctrl+Shift+C`, klistra in med `Ctrl+Shift+V`
- Högerklicksmeny för kopiera, klistra in, textstorlek och återanslutning
- `A+`/`A−` ändrar textstorleken i alla flikar; valet sparas mellan starter
- Pilknapp på fliken återansluter en avslutad session, utan automatisk återanslutning
- Bekräftelse före stängning av pågående sessioner och hela programmet
- Startfel visas i dialog och på fliken; avslutade sessioners utskrift ligger kvar

Textstorleken sparas i `$XDG_CONFIG_HOME/ssh-server-console/settings.json`
(normalt `~/.config/ssh-server-console/settings.json`). Inga anslutningshemligheter
sparas där. Fliktexten ”SSH körs” betyder att processen har startat, inte att
autentiseringen är färdig. Inloggningsstatus framgår av terminalen.

Wildcard-poster som `Host *` visas inte som servrar, men OpenSSH tillämpar dem
fortfarande när en anslutning öppnas. `Include` stöds med jokertecken, flera
filer och rekursion (loopar ger felmeddelande). Relativa Include-sökvägar
utgår från `~/.ssh`, även med `--config`, enligt OpenSSH:s användarkonfiguration.
Listan är en syntaktisk inventering: villkorliga Include-filer kan ge poster
som inte är aktiva för en viss anslutning. `Match exec` körs aldrig av listläsaren.
Visade adress-/användaruppgifter är endast värden från respektive Host-block,
inte fullständigt utvärderade globala eller villkorliga inställningar.
OpenSSH avgör alltid den verkliga konfigurationen vid anslutning.

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

Den alternativa konfigurationen skickas också till SSH via `-F`.
Precis som för vanlig `ssh -F` ersätter den då standardkonfigurationsfilerna.

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

GUI-tester med verkliga VTE-processer men utan nätverksanslutning:

```bash
sudo apt install xvfb xauth
xvfb-run -a env PYTHONPATH=src /usr/bin/python3 -m unittest discover -s tests -v
```

GitHub Actions kör båda kontrollerna. GUI-testerna hoppas över utan `DISPLAY`.

## Uppgradera från GitHub

Stäng appen (avsluta sessioner först) och kör i projektkatalogen:

```bash
git pull --ff-only
./install.sh
```

## Avinstallation

```bash
./uninstall.sh
```

Avinstallationen rör aldrig `~/.ssh`.
