# GitHub Repository Manager

Ein PyQt6-Desktop-Tool für Linux, mit dem sich GitHub-Repositories und lokale Git-Repositories verwalten lassen – ganz ohne Terminal. Login per Personal Access Token, Repositories erstellen/löschen/klonen, lokale Ordner verknüpfen, committen, pushen und pullen.

![GitHub Repository Manager – Screenshot](screenshot.png)

## Features

- **GitHub-Login** per Personal Access Token (PAT), inkl. Token-Prüfung und Komfort-Link zum Erstellen eines neuen Tokens
- **Repository-Verwaltung**: GitHub-Repositories auflisten, neu erstellen, löschen und die Liste aktualisieren
- **Lokale Repositories**:
  - Bestehendes GitHub-Repository klonen
  - Neues lokales Repository erstellen (`git init`) und automatisch mit einem GitHub-Repository verknüpfen
  - Beliebigen vorhandenen Ordner als Git-Repository laden
  - Nachträgliches Verknüpfen eines Ordners ohne Remote über **„Mit GitHub verknüpfen“**
- **Commit / Push / Pull** direkt aus der GUI
  - Erkennt leere Commits (keine Änderungen gefunden) und abgelehnte Pushes, statt fälschlich „Erfolg“ zu melden
  - Fragt bei abweichendem Branch-Namen (z. B. lokal `master`, GitHub-Standard `main`) aktiv nach, wohin gepusht werden soll
- **Standardordner** für alle lokalen Repositories konfigurierbar
- Automatische Erkennung der Linux-Distribution (Arch, Debian/Ubuntu, Fedora/RHEL/CentOS, openSUSE) und automatische Installation fehlender Abhängigkeiten

## Voraussetzungen

- Python 3.10+
- Linux (getestet unter Arch / Manjaro)
- Ein GitHub Personal Access Token mit dem Scope `repo`

### Abhängigkeiten

- [PyQt6](https://pypi.org/project/PyQt6/)
- [PyGithub](https://pypi.org/project/PyGithub/)
- [GitPython](https://pypi.org/project/GitPython/)

Fehlende Pakete werden beim ersten Start automatisch erkannt; das Skript bietet an, sie über den Systempaketmanager oder per `pip --user` zu installieren.

## Installation

```bash
git clone https://github.com/<dein-benutzername>/<repo-name>.git
cd <repo-name>
python3 github_manager.py
```

Alternativ manuell installieren:

```bash
pip install --user PyQt6 PyGithub GitPython
```

## Verwendung

1. **Verbinden**: Benutzername und Personal Access Token eingeben, auf „Verbinden“ klicken.
2. **Repository wählen**: In der Liste ein GitHub-Repository auswählen.
3. **Lokal einrichten**:
   - *Repository klonen* – lädt das ausgewählte Repository in den Standardordner
   - *Neues Repo init* – erstellt einen neuen lokalen Ordner und verknüpft ihn mit dem ausgewählten Repository
   - *Ordner auswählen* – lädt einen bereits vorhandenen lokalen Ordner (bei fehlendem Remote über „Mit GitHub verknüpfen“ nachträglich verbinden)
4. **Änderungen übertragen**: Commit-Nachricht eingeben → „Commit“ → „Push zu GitHub“.
5. **Änderungen holen**: „Pull von GitHub“.

## Konfigurationsdateien

Zugangsdaten und Einstellungen werden lokal unter `~/.config/github_manager/` gespeichert:

| Datei | Inhalt |
|---|---|
| `config.json` | Benutzername und Token (Dateirechte `600`) |
| `settings.json` | Standardordner für lokale Repositories |

## Sicherheitshinweis

Der Personal Access Token wird lokal im Klartext in `config.json` gespeichert (mit restriktiven Dateirechten). Verwende nach Möglichkeit einen Fine-grained Token mit minimalen Berechtigungen und beschränkter Repository-Auswahl.

## Lizenz

Dieses Projekt ist unter der **GNU General Public License v3.0** lizenziert. Sie
dürfen dieses Programm frei verwenden, verändern und weitergeben, solange
abgeleitete Werke ebenfalls unter der GPL v3 veröffentlicht werden. Siehe die
Datei [LICENSE](LICENSE) für den vollständigen Lizenztext oder besuchen Sie 
<https://www.gnu.org/licenses/gpl-3.0.html>.
