#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Repository Manager
Mit korrekter Remote-URL-Behandlung: Entfernt doppelte Token.
Mit Push-Ergebnis-Prüfung: Erkennt von GitHub abgelehnte oder
folgenlose Pushes, statt fälschlich "Erfolg" zu melden.
Mehrsprachig (DE/EN, erweiterbar über translations.py).
"""

import sys
import subprocess
import os
import json
import time
import datetime
import webbrowser
import re
import fnmatch
import shutil
import traceback

from translations import tr, AVAILABLE_LANGUAGES, get_current_language, set_language

# ----------------------------------------------------------------------
# 1. Abhängigkeiten prüfen und ggf. installieren
# ----------------------------------------------------------------------
def detect_distro():
    """Ermittelt die Linux-Distribution."""
    if os.path.exists('/etc/arch-release'):
        return 'arch'
    if os.path.exists('/etc/debian_version'):
        return 'debian'
    if os.path.exists('/etc/fedora-release'):
        return 'fedora'
    if os.path.exists('/etc/redhat-release'):
        with open('/etc/redhat-release') as f:
            content = f.read().lower()
            if 'centos' in content:
                return 'centos'
            if 'fedora' in content:
                return 'fedora'
            return 'rhel'
    if os.path.exists('/etc/SuSE-release') or os.path.exists('/etc/os-release'):
        try:
            with open('/etc/os-release') as f:
                for line in f:
                    if 'opensuse' in line.lower():
                        return 'opensuse'
        except:
            pass
    try:
        output = subprocess.check_output(['lsb_release', '-i'], stderr=subprocess.DEVNULL)
        if b'Ubuntu' in output or b'Debian' in output:
            return 'debian'
        if b'Fedora' in output:
            return 'fedora'
    except:
        pass
    return 'unknown'

def install_packages(distro, missing_modules):
    system_cmd = None
    if distro == 'arch':
        system_cmd = ['sudo', 'pacman', '-S', '--noconfirm', 'python-pygithub', 'python-pyqt6', 'python-gitpython']
    elif distro in ('debian', 'ubuntu'):
        system_cmd = ['sudo', 'apt-get', 'install', '-y', 'python3-pygithub', 'python3-pyqt6', 'python3-git']
    elif distro in ('fedora', 'rhel', 'centos'):
        system_cmd = ['sudo', 'dnf', 'install', '-y', 'python3-pygithub', 'python3-pyqt6', 'python3-gitpython']
    elif distro == 'opensuse':
        system_cmd = ['sudo', 'zypper', 'install', '-y', 'python3-pygithub', 'python3-pyqt6', 'python3-gitpython']
    pip_cmd = [sys.executable, '-m', 'pip', 'install', '--user', 'PyQt6', 'PyGithub', 'GitPython']

    if system_cmd:
        print(tr("deps_try_system_pkg", cmd=' '.join(system_cmd)))
        try:
            subprocess.check_call(system_cmd)
            print(tr("deps_system_success"))
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(tr("deps_system_failed_try_pip"))
    else:
        print(tr("deps_no_system_mgr"))

    print(tr("deps_running", cmd=' '.join(pip_cmd)))
    try:
        subprocess.check_call(pip_cmd)
        print(tr("deps_pip_success"))
        return True
    except subprocess.CalledProcessError:
        print(tr("deps_pip_failed"))
        return False

def check_and_install_dependencies():
    missing = []
    try:
        import PyQt6
    except ImportError:
        missing.append('PyQt6')
    try:
        import github
    except ImportError:
        missing.append('PyGithub')
    try:
        import git
    except ImportError:
        missing.append('GitPython')

    if not missing:
        return

    print("\n" + "="*60)
    print("  " + tr("deps_header"))
    print("="*60)
    print(tr("deps_needed", modules=', '.join(missing)))
    distro = detect_distro()
    print(tr("deps_distro", distro=distro))

    answer = input(tr("deps_prompt")).strip().lower()
    if answer not in ('j', 'ja', 'y', 'yes'):
        print(tr("deps_declined"))
        sys.exit(1)

    success = install_packages(distro, missing)
    if success:
        print(tr("deps_install_done_restart"))
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print(tr("deps_install_failed_manual"))
        sys.exit(1)

check_and_install_dependencies()

# ----------------------------------------------------------------------
# 2. Module importieren
# ----------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QCheckBox, QStatusBar, QGroupBox, QFileDialog, QInputDialog,
    QScrollArea, QTabWidget, QStackedWidget, QComboBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup
from github import Github, Auth
from github.Repository import Repository
import git
from git import Repo, InvalidGitRepositoryError, GitCommandError

# ----------------------------------------------------------------------
# 3. Konfigurationsverwaltung
# ----------------------------------------------------------------------
CONFIG_DIR = os.path.expanduser("~/.config/github_manager")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Regex für die relevanten PKGBUILD-Felder (einfache Skalarwerte,
# keine Bash-Arrays - deckt den weit überwiegenden Regelfall ab)
PKGNAME_RE = re.compile(r'^pkgname=(.*)$', re.MULTILINE)
PKGVER_RE = re.compile(r'^pkgver=(.*)$', re.MULTILINE)
PKGREL_RE = re.compile(r'^pkgrel=(.*)$', re.MULTILINE)

# Erkennt eine gängige "X.Y.Z"-Versionsnummer, optional mit führendem 'v'
# und einem beliebigen Suffix (z.B. '-beta', '.1'). Wird vom
# Versions-Assistenten benutzt, um Patch/Minor/Major automatisch
# hochzuzählen; alles, was nicht passt, muss manuell eingegeben werden.
SEMVER_RE = re.compile(r'^(v)?(\d+)\.(\d+)\.(\d+)(.*)$')


def parse_semver(text):
    """Zerlegt 'v1.2.3-beta' in (hat_v_prefix, major, minor, patch, suffix).
    Gibt None zurück, wenn der Text nicht diesem einfachen Schema folgt."""
    if not text:
        return None
    m = SEMVER_RE.match(text.strip())
    if not m:
        return None
    has_v, major, minor, patch, suffix = m.groups()
    return (bool(has_v), int(major), int(minor), int(patch), suffix)


def bump_semver(text, part):
    """Erhöht 'part' ('major', 'minor' oder 'patch') einer erkannten
    Versionsnummer und setzt niedrigere Stellen auf 0 zurück. Ein
    eventuelles Suffix (z.B. '-beta') wird dabei verworfen, da es sich
    i.d.R. nicht auf die neue Version übertragen lässt. Gibt None zurück,
    wenn 'text' nicht als X.Y.Z erkannt wurde."""
    parsed = parse_semver(text)
    if not parsed:
        return None
    has_v, major, minor, patch, _suffix = parsed
    if part == "major":
        major, minor, patch = major + 1, 0, 0
    elif part == "minor":
        minor, patch = minor + 1, 0
    elif part == "patch":
        patch += 1
    prefix = "v" if has_v else ""
    return f"{prefix}{major}.{minor}.{patch}"


def version_as_tag(version):
    """Formt eine Versionsnummer als GitHub-Tag (mit führendem 'v'), z.B.
    '1.2.3' -> 'v1.2.3'. Ein bereits vorhandenes 'v' bleibt erhalten."""
    version = version.strip()
    if not version:
        return version
    return version if version.lower().startswith("v") else f"v{version}"


def version_as_pkgver(version):
    """Formt eine Versionsnummer für die PKGBUILD (ohne führendes 'v' und
    ohne Bindestriche, da pacman diese im pkgver nicht erlaubt), z.B.
    'v1.2.3' -> '1.2.3'."""
    version = version.strip()
    if version[:1] in ("v", "V"):
        version = version[1:]
    return version.replace("-", "_")


# Erlaubte Zeichen für einen AUR-Paketnamen (siehe AUR-Regeln): Kleinbuchstaben,
# Ziffern und @ . _ + -, muss mit einem alphanumerischen Zeichen beginnen.
AUR_PKGNAME_RE = re.compile(r'^[a-z0-9][a-z0-9@._+-]*$')


def build_pkgbuild_template(data):
    """Erzeugt ein einfaches PKGBUILD-Grundgerüst für ein neues, an ein
    GitHub-Repository gekoppeltes AUR-Paket. Quelle ist bewusst ein
    Git-Tag-Archiv (statt eines Branches), da nur so reproduzierbare,
    versionsfeste Prüfsummen möglich sind - dafür muss auf GitHub aber
    ein passender Tag/Release existieren, bevor 'updpkgsums' läuft."""
    depends = " ".join(f"'{d}'" for d in data["depends"])
    arch = " ".join(f"'{a}'" for a in data["arch"])
    return f"""# Maintainer: {data.get('maintainer', 'DEIN NAME <DEINE@EMAIL.ADRESSE>')}
pkgname={data['pkgname']}
pkgver={data['pkgver']}
pkgrel=1
pkgdesc="{data['pkgdesc']}"
arch=({arch})
url="{data['url']}"
license=('{data['license']}')
depends=({depends})
source=("$pkgname-$pkgver.tar.gz::{data['url']}/archive/refs/tags/v$pkgver.tar.gz")
sha256sums=('SKIP')

# TODO: an das jeweilige Projekt anpassen (Build-Schritt bei Bedarf ergänzen,
# Installationspfade korrigieren).
package() {{
    cd "$pkgname-$pkgver"
    install -Dm755 "$pkgname.py" "$pkgdir/usr/bin/$pkgname"
}}
"""

# Typische von makepkg/updpkgsums erzeugte Build-Artefakte, die NICHT ins
# AUR-Git-Repo gehören (nur PKGBUILD/.SRCINFO/.install-Dateien etc. sollen
# versioniert werden). Wird genutzt, um solche Dateien im 'git status'
# von echten neuen/zu committenden Dateien zu unterscheiden.
AUR_BUILD_ARTIFACT_PATTERNS = (
    "*.tar.gz", "*.tar.xz", "*.tar.zst", "*.tar.bz2", "*.tgz", "*.zip",
    "*.pkg.tar.*", "*.log", "*.sig", "*.asc",
)
AUR_BUILD_ARTIFACT_DIRS = {"pkg", "src"}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {}
    try:
        with open(CONFIG_FILE, 'r') as f:
            data = json.load(f)
        valid_keys = ('username', 'token', 'saved_at')
        return {k: v for k, v in data.items() if k in valid_keys}
    except (json.JSONDecodeError, IOError):
        return {}

def save_config(username, token):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    data = {
        'username': username,
        'token': token,
        'saved_at': datetime.datetime.now().isoformat()
    }
    with open(CONFIG_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)

def clear_config():
    if os.path.exists(CONFIG_FILE):
        os.remove(CONFIG_FILE)

# Settings für Standardordner (und Sprache, siehe translations.py)
def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    try:
        with open(SETTINGS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_settings(settings):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=2)

# ----------------------------------------------------------------------
# 4. GUI-Klassen
# ----------------------------------------------------------------------
class NewRepoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_newrepo_title"))
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("dlg_newrepo_name_placeholder"))
        form.addRow(tr("dlg_newrepo_name_label"), self.name_edit)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText(tr("dlg_newrepo_desc_placeholder"))
        self.desc_edit.setMaximumHeight(100)
        form.addRow(tr("dlg_newrepo_desc_label"), self.desc_edit)
        self.private_check = QCheckBox(tr("dlg_newrepo_private_checkbox"))
        form.addRow(tr("dlg_newrepo_visibility_label"), self.private_check)
        layout.addLayout(form)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_repo_data(self):
        return {
            "name": self.name_edit.text().strip(),
            "description": self.desc_edit.toPlainText().strip(),
            "private": self.private_check.isChecked()
        }


# Gängige SPDX-Lizenzkennungen für das "Neues AUR-Paket"-Formular. Arch
# verlangt seit RFC 0016 SPDX-Identifier im PKGBUILD-license-Array statt der
# frueheren Kurzformen wie "GPL2"/"GPL3" - siehe
# https://rfc.archlinux.page/0016-spdx-license-identifiers/. Jeder Eintrag
# ist (Anzeigetext, SPDX-ID). Der "Benutzerdefiniert"-Eintrag (SPDX-ID None)
# wird separat über tr() ergänzt, da er wie der Rest der UI übersetzt ist.
AUR_LICENSE_CHOICES = (
    ("MIT", "MIT"),
    ("GNU General Public License v2.0 (GPL-2.0-or-later)", "GPL-2.0-or-later"),
    ("GNU General Public License v3.0 (GPL-3.0-or-later)", "GPL-3.0-or-later"),
    ("GNU Lesser GPL v2.1 (LGPL-2.1-or-later)", "LGPL-2.1-or-later"),
    ("GNU Lesser GPL v3.0 (LGPL-3.0-or-later)", "LGPL-3.0-or-later"),
    ("Apache License 2.0 (Apache-2.0)", "Apache-2.0"),
    ("BSD 3-Clause (BSD-3-Clause)", "BSD-3-Clause"),
    ("ISC License (ISC)", "ISC"),
    ("The Unlicense (Unlicense)", "Unlicense"),
)


class NewAurPackageDialog(QDialog):
    """Sammelt die Eckdaten für ein neues, noch nicht existierendes
    AUR-Paket (PKGBUILD-Grundgerüst)."""

    def __init__(self, parent=None, suggested_pkgname="", suggested_url="", suggested_desc=""):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_newaur_title"))
        self.setModal(True)
        self.resize(460, 420)

        layout = QVBoxLayout(self)

        intro = QLabel(tr("dlg_newaur_intro"))
        intro.setWordWrap(True)
        layout.addWidget(intro)

        form = QFormLayout()

        self.pkgname_edit = QLineEdit(suggested_pkgname)
        self.pkgname_edit.setPlaceholderText(tr("dlg_newaur_pkgname_placeholder"))
        form.addRow(tr("dlg_newaur_pkgname_label"), self.pkgname_edit)

        self.pkgver_edit = QLineEdit("1.0.0")
        form.addRow(tr("dlg_newaur_pkgver_label"), self.pkgver_edit)

        self.pkgdesc_edit = QLineEdit(suggested_desc)
        self.pkgdesc_edit.setPlaceholderText(tr("dlg_newaur_pkgdesc_placeholder"))
        form.addRow(tr("dlg_newaur_pkgdesc_label"), self.pkgdesc_edit)

        self.url_edit = QLineEdit(suggested_url)
        self.url_edit.setToolTip(tr("dlg_newaur_url_tooltip"))
        form.addRow(tr("dlg_newaur_url_label"), self.url_edit)

        self.license_combo = QComboBox()
        for label, spdx_id in AUR_LICENSE_CHOICES:
            self.license_combo.addItem(label, spdx_id)
        self.license_combo.addItem(tr("dlg_newaur_license_custom_option"), None)
        self.license_combo.currentIndexChanged.connect(self._on_license_choice_changed)
        form.addRow(tr("dlg_newaur_license_label"), self.license_combo)

        self.license_custom_edit = QLineEdit()
        self.license_custom_edit.setPlaceholderText(tr("dlg_newaur_license_custom_placeholder"))
        self.license_custom_edit.setEnabled(False)
        form.addRow("", self.license_custom_edit)

        self.arch_edit = QLineEdit("x86_64")
        self.arch_edit.setPlaceholderText(tr("dlg_newaur_arch_placeholder"))
        form.addRow(tr("dlg_newaur_arch_label"), self.arch_edit)

        self.depends_edit = QLineEdit()
        self.depends_edit.setPlaceholderText(tr("dlg_newaur_depends_placeholder"))
        form.addRow(tr("dlg_newaur_depends_label"), self.depends_edit)

        layout.addLayout(form)

        hint = QLabel(tr("dlg_newaur_hint"))
        hint.setWordWrap(True)
        hint.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(hint)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _on_license_choice_changed(self, index):
        is_custom = self.license_combo.itemData(index) is None
        self.license_custom_edit.setEnabled(is_custom)
        if is_custom:
            self.license_custom_edit.setFocus()

    def get_package_data(self):
        depends = [d.strip() for d in self.depends_edit.text().split(",") if d.strip()]
        arch = [a.strip() for a in self.arch_edit.text().split(",") if a.strip()] or ["x86_64"]
        chosen_license = self.license_combo.currentData()
        if chosen_license is None:
            chosen_license = self.license_custom_edit.text().strip()
        return {
            "pkgname": self.pkgname_edit.text().strip(),
            "pkgver": self.pkgver_edit.text().strip(),
            "pkgdesc": self.pkgdesc_edit.text().strip(),
            "url": self.url_edit.text().strip(),
            "license": chosen_license or "MIT",
            "arch": arch,
            "depends": depends,
        }


class NewReleaseDialog(QDialog):
    def __init__(self, parent=None, suggested_tag=""):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_newrelease_title"))
        self.setModal(True)
        self.resize(420, 380)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.tag_edit = QLineEdit()
        self.tag_edit.setPlaceholderText(tr("dlg_newrelease_tag_placeholder"))
        if suggested_tag:
            self.tag_edit.setText(suggested_tag)
        form.addRow(tr("dlg_newrelease_tag_label"), self.tag_edit)

        self.target_branch_edit = QLineEdit()
        self.target_branch_edit.setPlaceholderText(tr("dlg_newrelease_target_placeholder"))
        form.addRow(tr("dlg_newrelease_target_label"), self.target_branch_edit)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText(tr("dlg_newrelease_reltitle_placeholder"))
        form.addRow(tr("dlg_newrelease_reltitle_label"), self.title_edit)

        layout.addLayout(form)

        notes_label = QLabel(tr("dlg_newrelease_notes_label"))
        layout.addWidget(notes_label)
        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText(tr("dlg_newrelease_notes_placeholder"))
        layout.addWidget(self.notes_edit)

        self.prerelease_check = QCheckBox(tr("dlg_newrelease_prerelease_checkbox"))
        layout.addWidget(self.prerelease_check)

        self.draft_check = QCheckBox(tr("dlg_newrelease_draft_checkbox"))
        layout.addWidget(self.draft_check)

        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_release_data(self):
        return {
            "tag": self.tag_edit.text().strip(),
            "target_branch": self.target_branch_edit.text().strip(),
            "title": self.title_edit.text().strip(),
            "notes": self.notes_edit.toPlainText().strip(),
            "prerelease": self.prerelease_check.isChecked(),
            "draft": self.draft_check.isChecked(),
        }


class GithubWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            # str(e) allein wirft den Traceback weg und macht es bei nicht
            # offensichtlichen Fehlern (z.B. AttributeError an ungewohnter
            # Stelle) fast unmöglich, die genaue Codezeile zu finden. Der
            # volle Traceback wird deshalb mitgeschickt; alle .error-Handler
            # zeigen ihn aktuell 1:1 in der Fehlermeldung an.
            self.error.emit(f"{e}\n\n{traceback.format_exc()}")


class UpdateAssistantDialog(QDialog):
    """Geführter Assistent für den kompletten Update-Ablauf.

    Führt Schritt für Schritt durch: Commit -> Push (GitHub) -> optional
    Release erstellen -> optional AUR-Version aktualisieren -> Commit &&
    Push zum AUR. Jeder Schritt muss erledigt sein (oder erkennbar
    nichts zu tun haben), bevor "Weiter" aktiviert wird - so ist eine
    falsche Reihenfolge strukturell ausgeschlossen.

    Ruft bewusst dieselben Methoden auf, die auch die Buttons in den
    Tabs benutzen (on_commit/on_push/_open_release_dialog/
    on_aur_update_version/on_aur_commit_push), um Git-Logik nicht
    doppelt zu pflegen. Läuft modal, damit die main-window-Attribute
    'worker'/'aur_worker' währenddessen nicht durch andere Klicks
    überschrieben werden können."""

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle(tr("wizard_title"))
        self.setModal(True)
        self.resize(560, 480)

        self._order = []      # Reihenfolge der Schritt-Keys für diesen Lauf
        self._pos = -1        # Index in self._order, -1 = Intro-Seite
        self._done = set()    # bereits erfolgreich abgeschlossene Schritt-Keys
        self.new_version = ""  # von der Intro-Seite gewählte neue Version

        outer = QVBoxLayout(self)

        self.progress_label = QLabel()
        self.progress_label.setWordWrap(True)
        outer.addWidget(self.progress_label)

        self.stack = QStackedWidget()
        outer.addWidget(self.stack, 1)

        nav_layout = QHBoxLayout()
        self.back_btn = QPushButton(tr("wizard_btn_back"))
        self.back_btn.clicked.connect(self._go_back)
        nav_layout.addWidget(self.back_btn)
        nav_layout.addStretch(1)
        self.close_btn = QPushButton(tr("wizard_btn_close"))
        self.close_btn.clicked.connect(self.reject)
        nav_layout.addWidget(self.close_btn)
        self.next_btn = QPushButton(tr("wizard_btn_next"))
        self.next_btn.clicked.connect(self._go_next)
        nav_layout.addWidget(self.next_btn)
        outer.addLayout(nav_layout)

        self.page_index = {}  # Schritt-Key -> Index im QStackedWidget
        self._build_intro_page()
        self._build_commit_page()
        self._build_push_page()
        self._build_release_page()
        self._build_aur_version_page()
        self._build_aur_commit_push_page()
        self._build_summary_page()

        self._show_intro()

    # ------------------------------------------------------------------
    # Hilfsfunktionen
    # ------------------------------------------------------------------
    def _add_page(self, key, widget):
        idx = self.stack.addWidget(widget)
        self.page_index[key] = idx
        return idx

    def _invoke_and_hook(self, method, worker_attr, on_success, on_error, *args, **kwargs):
        """Ruft 'method' (eine bestehende Aktions-Methode des Hauptfensters)
        auf und hängt sich an den dabei neu erzeugten Worker (identifiziert
        über den Attributnamen 'worker'/'aur_worker') dran. Gibt False
        zurück, wenn die Methode aus Validierungsgründen (z.B. leere
        Commit-Nachricht) gar keinen neuen Worker gestartet hat."""
        before = getattr(self.main_window, worker_attr, None)
        method(*args, **kwargs)
        after = getattr(self.main_window, worker_attr, None)
        if after is None or after is before:
            return False
        after.finished.connect(on_success)
        after.error.connect(on_error)
        return True

    def _update_progress_label(self):
        if self._pos < 0:
            self.progress_label.setText(tr("wizard_progress_intro"))
        else:
            self.progress_label.setText(
                tr("wizard_progress_step", current=self._pos + 1, total=len(self._order))
            )

    # ------------------------------------------------------------------
    # Intro-Seite: Auswahl, welche Teile der Assistent ausführen soll
    # ------------------------------------------------------------------
    def _build_intro_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        intro_label = QLabel(tr("wizard_intro_text"))
        intro_label.setWordWrap(True)
        layout.addWidget(intro_label)

        self.wizard_has_github = self.main_window.repo_obj is not None
        self.wizard_has_aur = self.main_window.aur_repo_obj is not None

        if not self.wizard_has_github:
            layout.addWidget(self._info_label(tr("wizard_intro_no_github")))

        self.release_check = QCheckBox(tr("wizard_check_release"))
        self.release_check.setEnabled(
            self.wizard_has_github and self.main_window.selected_repo is not None
        )
        layout.addWidget(self.release_check)

        self.aur_check = QCheckBox(tr("wizard_check_aur"))
        self.aur_check.setEnabled(self.wizard_has_aur)
        self.aur_check.setChecked(self.wizard_has_aur)
        if not self.wizard_has_aur:
            layout.addWidget(self._info_label(tr("wizard_intro_no_aur")))
        layout.addWidget(self.aur_check)

        # ---- Neue Version wählen (füttert Release-Tag & AUR-pkgver) ----
        self.current_github_version = None
        self.current_aur_version = (
            self.main_window.aur_version_edit.text().strip() if self.wizard_has_aur else None
        )
        version_relevant = (
            self.wizard_has_aur or (self.wizard_has_github and self.main_window.selected_repo)
        )
        if version_relevant:
            version_group = QGroupBox(tr("wizard_version_group_title"))
            v_layout = QVBoxLayout(version_group)

            self.github_version_label = QLabel()
            self.github_version_label.setWordWrap(True)
            if self.wizard_has_github and self.main_window.selected_repo:
                v_layout.addWidget(self.github_version_label)

            self.aur_version_label = QLabel()
            self.aur_version_label.setWordWrap(True)
            if self.wizard_has_aur:
                self.aur_version_label.setText(
                    tr("wizard_version_current_aur", version=self.current_aur_version)
                )
                v_layout.addWidget(self.aur_version_label)

            field_row = QHBoxLayout()
            field_row.addWidget(QLabel(tr("wizard_new_version_label")))
            self.new_version_edit = QLineEdit()
            self.new_version_edit.setPlaceholderText(tr("wizard_new_version_placeholder"))
            field_row.addWidget(self.new_version_edit)
            v_layout.addLayout(field_row)

            bump_row = QHBoxLayout()
            self.bump_patch_btn = QPushButton(tr("wizard_btn_bump_patch"))
            self.bump_patch_btn.clicked.connect(lambda: self._apply_bump("patch"))
            bump_row.addWidget(self.bump_patch_btn)
            self.bump_minor_btn = QPushButton(tr("wizard_btn_bump_minor"))
            self.bump_minor_btn.clicked.connect(lambda: self._apply_bump("minor"))
            bump_row.addWidget(self.bump_minor_btn)
            self.bump_major_btn = QPushButton(tr("wizard_btn_bump_major"))
            self.bump_major_btn.clicked.connect(lambda: self._apply_bump("major"))
            bump_row.addWidget(self.bump_major_btn)
            v_layout.addLayout(bump_row)

            self.version_hint_label = self._info_label("")
            v_layout.addWidget(self.version_hint_label)

            layout.addWidget(version_group)
        else:
            self.new_version_edit = None

        layout.addStretch(1)
        self._add_page("intro", page)

        if version_relevant:
            self._update_version_suggestion()
        if self.wizard_has_github and self.main_window.selected_repo:
            self._fetch_current_github_version()

    def _info_label(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setStyleSheet("color: gray; font-style: italic;")
        return label

    def _fetch_current_github_version(self):
        self.github_version_label.setText(tr("wizard_version_checking"))
        worker = GithubWorker(self._get_latest_release_tag)
        worker.finished.connect(self._on_github_version_fetched)
        worker.error.connect(lambda _e: self._on_github_version_fetched(None))
        self._version_check_worker = worker  # Referenz halten
        worker.start()

    def _get_latest_release_tag(self):
        try:
            release = self.main_window.selected_repo.get_latest_release()
            return release.tag_name
        except Exception:
            return None

    def _on_github_version_fetched(self, tag):
        self.current_github_version = tag
        if tag:
            self.github_version_label.setText(tr("wizard_version_current_github", version=tag))
        else:
            self.github_version_label.setText(tr("wizard_version_no_releases"))
        self._update_version_suggestion()

    def _version_baseline(self):
        """Die Version, von der aus Patch/Minor/Major hochgezählt wird:
        bevorzugt der letzte GitHub-Release-Tag, sonst die aktuelle
        AUR-pkgver."""
        return self.current_github_version or self.current_aur_version

    def _update_version_suggestion(self):
        if self.new_version_edit is None:
            return
        baseline = self._version_baseline()
        parseable = baseline is not None and parse_semver(baseline) is not None
        self.bump_patch_btn.setEnabled(parseable)
        self.bump_minor_btn.setEnabled(parseable)
        self.bump_major_btn.setEnabled(parseable)
        if not self.new_version_edit.text().strip():
            if parseable:
                self.new_version_edit.setText(bump_semver(baseline, "patch"))
            elif baseline:
                self.new_version_edit.setText(baseline)
        if baseline and not parseable:
            self.version_hint_label.setText(tr("wizard_version_manual_hint"))
        else:
            self.version_hint_label.setText("")

    def _apply_bump(self, part):
        baseline = self._version_baseline()
        bumped = bump_semver(baseline, part) if baseline else None
        if bumped:
            self.new_version_edit.setText(bumped)

    def _show_intro(self):
        self._pos = -1
        self.stack.setCurrentIndex(self.page_index["intro"])
        self.back_btn.setEnabled(False)
        self.next_btn.setEnabled(self.wizard_has_github or self.wizard_has_aur)
        self.next_btn.setText(tr("wizard_btn_next"))
        try:
            self.next_btn.clicked.disconnect()
        except TypeError:
            pass
        self.next_btn.clicked.connect(self._start_flow)
        self._update_progress_label()

    def _start_flow(self):
        self.new_version = self.new_version_edit.text().strip() if self.new_version_edit else ""
        needs_version = self.release_check.isChecked() or self.aur_check.isChecked()
        if needs_version and not self.new_version:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_wizard_version_required"))
            return

        order = []
        if self.wizard_has_github:
            order.append("commit")
            order.append("push")
            if self.release_check.isChecked():
                order.append("release")
        if self.aur_check.isChecked():
            order.append("aur_version")
            order.append("aur_commit_push")
        order.append("summary")
        self._order = order
        self._pos = 0

        self.next_btn.clicked.disconnect()
        self.next_btn.clicked.connect(self._go_next)
        self.back_btn.setEnabled(True)
        self._show_step()

    # ------------------------------------------------------------------
    # Navigation zwischen den Schritten
    # ------------------------------------------------------------------
    def _show_step(self):
        key = self._order[self._pos]
        self.stack.setCurrentIndex(self.page_index[key])
        self.back_btn.setEnabled(True)
        self._update_progress_label()
        refresh = getattr(self, f"_refresh_{key}", None)
        if refresh:
            refresh()
        if key == "summary":
            self.next_btn.setText(tr("wizard_btn_finish"))
            self.next_btn.setEnabled(True)
        else:
            self.next_btn.setText(tr("wizard_btn_next"))
            self.next_btn.setEnabled(key in self._done)

    def _go_next(self):
        if self._pos == len(self._order) - 1:
            self.accept()
            return
        self._pos += 1
        self._show_step()

    def _go_back(self):
        if self._pos <= 0:
            self._show_intro()
            return
        self._pos -= 1
        self._show_step()

    def _mark_done(self, key):
        self._done.add(key)
        if self._order[self._pos] == key:
            self.next_btn.setEnabled(True)

    def reject(self):
        """Warnt beim Schließen, solange der Ablauf gestartet ist und noch
        Schritte offen sind - genau das Szenario, das dazu führt, dass z.B.
        die AUR-Version lokal aktualisiert, aber nie gepusht wird."""
        pending = [
            key for key in self._order
            if key != "summary" and key not in self._done
        ]
        if self._pos >= 0 and pending:
            reply = QMessageBox.question(
                self,
                tr("wizard_close_confirm_title"),
                tr("wizard_close_confirm_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return
        super().reject()

    # ------------------------------------------------------------------
    # Schritt: GitHub Commit
    # ------------------------------------------------------------------
    def _build_commit_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_commit_title")))

        self.commit_status_label = QLabel()
        self.commit_status_label.setWordWrap(True)
        layout.addWidget(self.commit_status_label)

        layout.addWidget(QLabel(tr("aur_commit_msg_label")))
        self.wizard_commit_msg_edit = QLineEdit()
        self.wizard_commit_msg_edit.setPlaceholderText(tr("local_commit_msg_placeholder"))
        layout.addWidget(self.wizard_commit_msg_edit)

        self.commit_run_btn = QPushButton(tr("wizard_btn_run_commit"))
        self.commit_run_btn.clicked.connect(self._do_commit)
        layout.addWidget(self.commit_run_btn)
        layout.addStretch(1)
        self._add_page("commit", page)

    def _refresh_commit(self):
        if not self.main_window.repo_obj:
            self.commit_status_label.setText(tr("wizard_no_local_repo"))
            self.commit_run_btn.setEnabled(False)
            return
        status_output = self.main_window.repo_obj.git.status(porcelain=True)
        dirty = len([l for l in status_output.splitlines() if l.strip()])
        if dirty == 0:
            self.commit_status_label.setText(tr("wizard_step_nothing_to_do"))
            self.commit_run_btn.setEnabled(False)
            self.wizard_commit_msg_edit.setEnabled(False)
            self._mark_done("commit")
        else:
            self.commit_status_label.setText(
                tr("wizard_commit_dirty_count", count=dirty)
            )
            self.commit_run_btn.setEnabled(True)
            self.wizard_commit_msg_edit.setEnabled(True)

    def _do_commit(self):
        msg = self.wizard_commit_msg_edit.text().strip()
        if not msg:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_commit_msg_required"))
            return
        self.main_window.commit_msg_edit.setText(msg)
        self.commit_run_btn.setEnabled(False)
        started = self._invoke_and_hook(
            self.main_window.on_commit, "worker",
            self._on_commit_step_success, self._on_commit_step_error
        )
        if not started:
            self.commit_run_btn.setEnabled(True)

    def _on_commit_step_success(self, _result):
        self.commit_status_label.setText(tr("wizard_step_done"))
        self.wizard_commit_msg_edit.clear()
        self._mark_done("commit")

    def _on_commit_step_error(self, error_msg):
        self.commit_run_btn.setEnabled(True)
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_commit_error", error=error_msg))

    # ------------------------------------------------------------------
    # Schritt: GitHub Push
    # ------------------------------------------------------------------
    def _build_push_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_push_title")))

        self.push_status_label = QLabel()
        self.push_status_label.setWordWrap(True)
        layout.addWidget(self.push_status_label)

        self.push_run_btn = QPushButton(tr("wizard_btn_run_push"))
        self.push_run_btn.clicked.connect(self._do_push)
        layout.addWidget(self.push_run_btn)
        layout.addStretch(1)
        self._add_page("push", page)

    def _refresh_push(self):
        if not self.main_window.repo_obj:
            self.push_status_label.setText(tr("wizard_no_local_repo"))
            self.push_run_btn.setEnabled(False)
            return
        self.push_status_label.setText(tr("status_checking_repo_state"))
        self.push_run_btn.setEnabled(False)
        worker = GithubWorker(self.main_window._analyze_repo_state)
        worker.finished.connect(self._on_push_state_checked)
        worker.error.connect(lambda e: self.push_status_label.setText(tr("wizard_check_failed", error=e)))
        self._push_check_worker = worker  # Referenz halten, sonst wird der Thread evtl. zerstört
        worker.start()

    def _on_push_state_checked(self, result):
        kind = result.get("state")
        if kind == "up_to_date" or kind == "pull_needed":
            # Nichts (mehr) zu pushen. Bei 'pull_needed' fehlen zwar neuere
            # Remote-Commits lokal, das ändert aber nichts daran, was schon
            # auf GitHub liegt - für ein Release ist das unkritisch.
            self.push_status_label.setText(tr("wizard_step_nothing_to_do"))
            self.push_run_btn.setEnabled(False)
            self._mark_done("push")
        elif kind == "diverged":
            # Lokale UND entfernte Commits weichen voneinander ab - ein
            # einfacher Push würde abgelehnt. Das muss erst im GitHub-Tab
            # per Pull/Merge aufgelöst werden, bevor der Assistent sinnvoll
            # weitermachen kann.
            self.push_status_label.setText(tr("wizard_push_diverged"))
            self.push_run_btn.setEnabled(False)
        elif kind == "merge_pending":
            self.push_status_label.setText(tr("wizard_push_merge_pending"))
            self.push_run_btn.setEnabled(False)
        elif kind == "push_needed":
            self.push_status_label.setText(
                tr("wizard_push_ahead_count", ahead=result.get("ahead", 0))
            )
            self.push_run_btn.setEnabled(True)
        elif kind == "commit_needed":
            # Sollte dank der Commit-Seite eigentlich nicht mehr vorkommen -
            # zur Sicherheit trotzdem nicht stillschweigend als "fertig"
            # markieren, sondern zurück zum Commit-Schritt verweisen.
            self.push_status_label.setText(tr("wizard_push_commit_needed"))
            self.push_run_btn.setEnabled(False)
        elif kind in ("no_remote", "no_auth"):
            self.push_status_label.setText(tr("wizard_push_blocked", state=kind))
            self.push_run_btn.setEnabled(False)
        else:
            self.push_status_label.setText(tr("wizard_step_nothing_to_do"))
            self.push_run_btn.setEnabled(False)
            self._mark_done("push")

    def _do_push(self):
        self.push_run_btn.setEnabled(False)
        started = self._invoke_and_hook(
            self.main_window.on_push, "worker",
            self._on_push_step_success, self._on_push_step_error
        )
        if not started:
            # Nutzer hat z.B. den Branch-Abgleich-Dialog abgebrochen
            self.push_run_btn.setEnabled(True)

    def _on_push_step_success(self, _result):
        self.push_status_label.setText(tr("wizard_step_done"))
        self._mark_done("push")

    def _on_push_step_error(self, error_msg):
        self.push_run_btn.setEnabled(True)
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_push_error", error=error_msg))

    # ------------------------------------------------------------------
    # Schritt: GitHub Release (optional)
    # ------------------------------------------------------------------
    def _build_release_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_release_title")))

        info = QLabel(tr("wizard_release_info"))
        info.setWordWrap(True)
        layout.addWidget(info)

        self.release_run_btn = QPushButton(tr("wizard_btn_run_release"))
        self.release_run_btn.clicked.connect(self._do_release)
        layout.addWidget(self.release_run_btn)

        self.release_status_label = QLabel()
        self.release_status_label.setWordWrap(True)
        layout.addWidget(self.release_status_label)

        skip_btn = QPushButton(tr("wizard_btn_skip_step"))
        skip_btn.clicked.connect(lambda: self._mark_done("release"))
        layout.addWidget(skip_btn)
        layout.addStretch(1)
        self._add_page("release", page)

    def _refresh_release(self):
        self.release_status_label.setText("")
        self.release_run_btn.setEnabled(True)

    def _do_release(self):
        self.release_run_btn.setEnabled(False)
        suggested_tag = version_as_tag(self.new_version) if self.new_version else ""
        started = self._invoke_and_hook(
            self.main_window._open_release_dialog, "worker",
            self._on_release_step_success, self._on_release_step_error,
            suggested_tag=suggested_tag
        )
        if not started:
            # Dialog abgebrochen oder kein Tag angegeben
            self.release_run_btn.setEnabled(True)

    def _on_release_step_success(self, _result):
        self.release_status_label.setText(tr("wizard_step_done"))
        self._mark_done("release")

    def _on_release_step_error(self, error_msg):
        self.release_run_btn.setEnabled(True)
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_release_error", error=error_msg))

    # ------------------------------------------------------------------
    # Schritt: AUR Version aktualisieren (optional)
    # ------------------------------------------------------------------
    def _build_aur_version_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_aur_version_title")))

        self.aur_version_status_label = QLabel()
        self.aur_version_status_label.setWordWrap(True)
        layout.addWidget(self.aur_version_status_label)

        layout.addWidget(QLabel(tr("aur_version_label")))
        self.wizard_aur_version_edit = QLineEdit()
        self.wizard_aur_version_edit.setPlaceholderText(tr("aur_version_placeholder"))
        layout.addWidget(self.wizard_aur_version_edit)

        self.aur_version_run_btn = QPushButton(tr("wizard_btn_run_aur_version"))
        self.aur_version_run_btn.clicked.connect(self._do_aur_version)
        layout.addWidget(self.aur_version_run_btn)
        layout.addStretch(1)
        self._add_page("aur_version", page)

    def _refresh_aur_version(self):
        if not self.main_window.aur_repo_obj:
            self.aur_version_status_label.setText(tr("wizard_no_aur_repo"))
            self.aur_version_run_btn.setEnabled(False)
            return
        current = self.main_window.aur_version_edit.text().strip()
        self.aur_version_status_label.setText(tr("wizard_aur_current_version", version=current))
        if not self.wizard_aur_version_edit.text().strip():
            suggestion = version_as_pkgver(self.new_version) if self.new_version else current
            self.wizard_aur_version_edit.setText(suggestion)

    def _do_aur_version(self):
        version = self.wizard_aur_version_edit.text().strip()
        if not version:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_version_required"))
            return
        self.main_window.aur_version_edit.setText(version)
        self.aur_version_run_btn.setEnabled(False)
        started = self._invoke_and_hook(
            self.main_window.on_aur_update_version, "aur_worker",
            self._on_aur_version_step_success, self._on_aur_version_step_error
        )
        if not started:
            self.aur_version_run_btn.setEnabled(True)

    def _on_aur_version_step_success(self, result):
        self.aur_version_status_label.setText(tr("wizard_step_done"))
        self._mark_done("aur_version")
        # Commit-Nachricht für den nächsten Schritt vorbelegen
        self.wizard_aur_commit_msg_edit.setText(
            tr("aur_commit_msg_default", version=result.get("new_version", ""))
        )

    def _on_aur_version_step_error(self, error_msg):
        self.aur_version_run_btn.setEnabled(True)
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_update_error", error=error_msg))

    # ------------------------------------------------------------------
    # Schritt: AUR Commit && Push (optional)
    # ------------------------------------------------------------------
    def _build_aur_commit_push_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_aur_commit_push_title")))

        self.aur_commit_push_status_label = QLabel()
        self.aur_commit_push_status_label.setWordWrap(True)
        layout.addWidget(self.aur_commit_push_status_label)

        layout.addWidget(QLabel(tr("aur_commit_msg_label")))
        self.wizard_aur_commit_msg_edit = QLineEdit()
        self.wizard_aur_commit_msg_edit.setPlaceholderText(tr("aur_commit_msg_placeholder"))
        layout.addWidget(self.wizard_aur_commit_msg_edit)

        self.aur_commit_push_run_btn = QPushButton(tr("wizard_btn_run_aur_commit_push"))
        self.aur_commit_push_run_btn.clicked.connect(self._do_aur_commit_push)
        layout.addWidget(self.aur_commit_push_run_btn)
        layout.addStretch(1)
        self._add_page("aur_commit_push", page)

    def _refresh_aur_commit_push(self):
        if not self.main_window.aur_repo_obj:
            self.aur_commit_push_status_label.setText(tr("wizard_no_aur_repo"))
            self.aur_commit_push_run_btn.setEnabled(False)
            return
        self.aur_commit_push_status_label.setText("")

    def _do_aur_commit_push(self):
        msg = self.wizard_aur_commit_msg_edit.text().strip()
        if not msg:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_commit_msg_required"))
            return
        self.main_window.aur_commit_msg_edit.setText(msg)
        self.aur_commit_push_run_btn.setEnabled(False)
        started = self._invoke_and_hook(
            self.main_window.on_aur_commit_push, "aur_worker",
            self._on_aur_commit_push_step_success, self._on_aur_commit_push_step_error
        )
        if not started:
            self.aur_commit_push_run_btn.setEnabled(True)

    def _on_aur_commit_push_step_success(self, _result):
        self.aur_commit_push_status_label.setText(tr("wizard_step_done"))
        self.wizard_aur_commit_msg_edit.clear()
        self._mark_done("aur_commit_push")

    def _on_aur_commit_push_step_error(self, error_msg):
        self.aur_commit_push_run_btn.setEnabled(True)
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_push_error", error=error_msg))

    # ------------------------------------------------------------------
    # Abschluss-Seite
    # ------------------------------------------------------------------
    def _build_summary_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.addWidget(self._title_label(tr("wizard_step_summary_title")))
        self.summary_label = QLabel()
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label)
        layout.addStretch(1)
        self._add_page("summary", page)

    def _refresh_summary(self):
        labels = {
            "commit": tr("wizard_step_commit_title"),
            "push": tr("wizard_step_push_title"),
            "release": tr("wizard_step_release_title"),
            "aur_version": tr("wizard_step_aur_version_title"),
            "aur_commit_push": tr("wizard_step_aur_commit_push_title"),
        }
        lines = []
        for key in self._order:
            if key == "summary":
                continue
            mark = "✓" if key in self._done else "–"
            lines.append(f"{mark} {labels.get(key, key)}")
        self.summary_label.setText(tr("wizard_summary_text") + "\n\n" + "\n".join(lines))
        self._mark_done("summary")

    def _title_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-weight: bold; font-size: 13px;")
        return label


class HelpDialog(QDialog):
    """Benutzerhandbuch als scrollbarer Dialog."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_help_title"))
        self.setModal(True)
        self.resize(680, 600)

        layout = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(8)

        help_text = QTextEdit()
        help_text.setReadOnly(True)
        help_text.setHtml(tr("help_html"))
        content_layout.addWidget(help_text)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)


class AboutDialog(QDialog):
    """Über-Dialog mit Version und Autor."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_about_title"))
        self.setModal(True)
        self.setFixedSize(400, 260)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        title = QLabel(f"<b style='font-size:15px;'>{tr('about_app_title')}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        version = QLabel(tr("about_version"))
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)

        separator = QLabel("<hr>")
        layout.addWidget(separator)

        author = QLabel(tr("about_author_block"))
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        author.setOpenExternalLinks(True)
        author.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(author)

        desc = QLabel(tr("about_desc"))
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        btn_box.accepted.connect(self.accept)
        layout.addWidget(btn_box)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(tr("main_window_title"))
        self.setMinimumSize(650, 650)

        self.github = None
        self.current_user = None
        self.repos = []
        self.selected_repo = None

        self.local_repo_path = None
        self.repo_obj = None
        self.default_folder = None
        self.token = None
        self._last_state = None  # letztes Ergebnis von _analyze_repo_state()

        # AUR-Tab
        self.aur_folder = None
        self.aur_repo_obj = None
        self.aur_default_folder = None
        self.aur_worker = None
        self._aur_last_state = None  # letztes Ergebnis von _analyze_aur_state()
        # True, sobald in diesem Durchlauf (seit dem Laden des Ordners bzw.
        # seit dem letzten erfolgreichen AUR-Push) "Version aktualisieren"
        # erfolgreich gelaufen ist. Dient als Reihenfolge-Sperre: commit/push
        # zum AUR fragen nach, wenn dieser Schritt noch fehlt (siehe
        # _guard_aur_push_order()).
        self.aur_version_updated = False

        self.init_ui()
        self.load_saved_credentials()
        self.load_settings()
        self.status_bar.showMessage(tr("status_ready"))

    # ------------------------------------------------------------------
    # Update-Assistent
    # ------------------------------------------------------------------
    def on_open_update_assistant(self):
        if not self.repo_obj and not self.aur_repo_obj:
            QMessageBox.information(
                self, tr("msg_no_repo_title"), tr("wizard_no_local_repo") + " " + tr("wizard_no_aur_repo")
            )
            return
        dialog = UpdateAssistantDialog(self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Hilfe / Über
    # ------------------------------------------------------------------
    def on_show_help(self):
        dialog = HelpDialog(self)
        dialog.exec()

    def on_show_about(self):
        dialog = AboutDialog(self)
        dialog.exec()

    # ------------------------------------------------------------------
    # Sprache
    # ------------------------------------------------------------------
    def on_change_language(self, lang_code):
        if lang_code == get_current_language():
            return
        set_language(lang_code)
        self.retranslate_ui()

    def retranslate_ui(self):
        """Aktualisiert alle sichtbaren Texte auf die aktuell aktive Sprache,
        ohne dass die Anwendung neu gestartet werden muss."""
        self.setWindowTitle(tr("main_window_title"))

        # Menü
        self.tools_menu.setTitle(tr("menu_tools"))
        self.action_update_assistant.setText(tr("menu_action_update_assistant"))
        self.action_update_assistant.setToolTip(tr("menu_action_update_assistant_tooltip"))
        self.action_update_assistant.setStatusTip(tr("menu_action_update_assistant_tooltip"))
        self.help_menu.setTitle(tr("menu_help"))
        self.action_help.setText(tr("menu_action_manual"))
        self.action_help.setToolTip(tr("menu_action_manual_tooltip"))
        self.action_help.setStatusTip(tr("menu_action_manual_tooltip"))
        self.action_about.setText(tr("menu_action_about"))
        self.action_about.setToolTip(tr("menu_action_about_tooltip"))
        self.action_about.setStatusTip(tr("menu_action_about_tooltip"))
        self.language_menu.setTitle(tr("menu_language"))
        for code, display_name in AVAILABLE_LANGUAGES.items():
            for action in self.language_action_group.actions():
                if action.text() == display_name:
                    tooltip = tr("menu_language_item_tooltip", language=display_name)
                    action.setToolTip(tooltip)
                    action.setStatusTip(tooltip)
                    break

        # Login
        self.login_group.setTitle(tr("login_group_title"))
        self.user_label.setText(tr("login_username_label"))
        self.user_edit.setPlaceholderText(tr("login_username_placeholder"))
        self.user_edit.setToolTip(tr("login_username_tooltip"))
        self.token_label.setText(tr("login_token_label"))
        self.token_edit.setPlaceholderText(tr("login_token_placeholder"))
        self.token_edit.setToolTip(tr("login_token_tooltip"))
        self.connect_btn.setText(tr("btn_connect"))
        self.connect_btn.setToolTip(tr("btn_connect_tooltip"))
        self.check_token_btn.setText(tr("btn_check_token"))
        self.check_token_btn.setToolTip(tr("btn_check_token_tooltip"))
        self.create_token_btn.setText(tr("btn_create_token"))
        self.create_token_btn.setToolTip(tr("btn_create_token_tooltip"))

        # Repository-Liste
        self.list_group.setTitle(tr("repolist_group_title"))
        self.repo_list.setToolTip(tr("repolist_tooltip"))
        self.new_btn.setText(tr("btn_new_repo"))
        self.new_btn.setToolTip(tr("btn_new_repo_tooltip"))
        self.delete_btn.setText(tr("btn_delete_repo"))
        self.delete_btn.setToolTip(tr("btn_delete_repo_tooltip"))
        self.refresh_btn.setText(tr("btn_refresh"))
        self.refresh_btn.setToolTip(tr("btn_refresh_tooltip"))

        # Lokales Repository
        self.local_group.setTitle(tr("local_group_title"))
        self.default_folder_label.setText(tr("local_default_folder_label"))
        self.default_folder_edit.setPlaceholderText(tr("local_default_folder_placeholder"))
        self.set_default_btn.setText(tr("btn_set_default"))
        self.set_default_btn.setToolTip(tr("btn_set_default_tooltip"))
        self.change_default_btn.setText(tr("btn_change_default"))
        self.change_default_btn.setToolTip(tr("btn_change_default_tooltip"))
        self.clone_btn.setText(tr("btn_clone"))
        self.clone_btn.setToolTip(tr("btn_clone_tooltip"))
        self.init_btn.setText(tr("btn_init"))
        self.init_btn.setToolTip(tr("btn_init_tooltip"))
        self.browse_btn.setText(tr("btn_browse"))
        self.browse_btn.setToolTip(tr("btn_browse_tooltip"))
        self.path_label.setText(tr("local_loaded_label"))
        self.path_edit.setPlaceholderText(tr("local_loaded_placeholder"))
        self.commit_label.setText(tr("local_commit_msg_label"))
        self.commit_msg_edit.setPlaceholderText(tr("local_commit_msg_placeholder"))
        self.commit_btn.setText(tr("btn_commit"))
        self.commit_btn.setToolTip(tr("btn_commit_tooltip"))
        self.push_btn.setText(tr("btn_push"))
        self.push_btn.setToolTip(tr("btn_push_tooltip"))
        self.pull_btn.setText(tr("btn_pull"))
        self.pull_btn.setToolTip(tr("btn_pull_tooltip"))
        self.link_remote_btn.setText(tr("btn_link_remote"))
        self.link_remote_btn.setToolTip(tr("btn_link_remote_tooltip"))

        self.check_status_btn.setText(tr("btn_check_status"))
        self.check_status_btn.setToolTip(tr("btn_check_status_tooltip"))
        self.suggested_action_btn.setToolTip(tr("btn_suggested_action_tooltip"))
        if self._last_state:
            # Empfehlungstext und Aktionsbutton in neuer Sprache neu aufbauen
            self._apply_recommendation(self._last_state)
        else:
            self.recommendation_label.setText(tr("recommendation_none"))
            self.suggested_action_btn.setText(tr("btn_suggested_action"))

        # Tabs
        self.tabs.setTabText(0, tr("tab_github"))
        self.tabs.setTabText(1, tr("tab_aur"))

        # AUR-Tab
        self.aur_group.setTitle(tr("aur_group_title"))
        self.aur_intro_label.setText(tr("aur_intro_text"))
        self.aur_folder_label.setText(tr("aur_folder_label"))
        self.aur_folder_edit.setPlaceholderText(tr("aur_folder_placeholder"))
        self.aur_browse_btn.setText(tr("btn_aur_browse"))
        self.aur_browse_btn.setToolTip(tr("btn_aur_browse_tooltip"))
        self.aur_new_package_btn.setText(tr("btn_aur_new_package"))
        self.aur_new_package_btn.setToolTip(tr("btn_aur_new_package_tooltip"))
        self.aur_version_label.setText(tr("aur_version_label"))
        self.aur_version_edit.setPlaceholderText(tr("aur_version_placeholder"))
        self.aur_update_btn.setText(tr("btn_aur_update"))
        self.aur_update_btn.setToolTip(tr("btn_aur_update_tooltip"))
        self.aur_commit_label.setText(tr("aur_commit_msg_label"))
        self.aur_commit_msg_edit.setPlaceholderText(tr("aur_commit_msg_placeholder"))
        self.aur_commit_push_btn.setText(tr("btn_aur_commit_push"))
        self.aur_commit_push_btn.setToolTip(tr("btn_aur_commit_push_tooltip"))
        if not self.aur_repo_obj:
            self.aur_info_label.setText(tr("aur_info_none"))

        self.aur_check_status_btn.setText(tr("btn_aur_check_status"))
        self.aur_check_status_btn.setToolTip(tr("btn_aur_check_status_tooltip"))
        self.aur_suggested_action_btn.setToolTip(tr("btn_aur_suggested_action_tooltip"))
        if self._aur_last_state:
            self._apply_aur_recommendation(self._aur_last_state)
        else:
            self.aur_recommendation_label.setText(tr("aur_recommendation_none"))
            self.aur_suggested_action_btn.setText(tr("btn_aur_suggested_action"))
        self._update_aur_step_indicator()

        if self.repo_obj:
            self.branch_label.setText(tr("branch_label", branch=self.repo_obj.active_branch.name))
        else:
            self.branch_label.setText(tr("branch_label_empty"))

        self.status_bar.showMessage(tr("status_ready"))

    # ------------------------------------------------------------------
    # Hilfsmethode: Remote-URL immer korrekt mit Token setzen
    # ------------------------------------------------------------------
    def _ensure_auth_url(self, origin):
        """Setzt die Remote-URL auf die authentifizierte Version mit aktuellem Token.
        Entfernt vorher eventuell vorhandene Token/User-Info."""
        url = origin.url
        # Extrahiere die Basis-URL (ohne Token/Benutzername)
        if "@" in url and "://" in url:
            # Beispiel: https://user:token@github.com/user/repo.git
            # Nimm den Teil nach dem @
            base_url = "https://" + url.split("@")[-1]
        else:
            base_url = url
        # Jetzt die authentifizierte URL mit aktuellem Token erstellen
        username = self.current_user.login
        token = self.token
        auth_url = f"https://{username}:{token}@{base_url[8:]}"
        origin.set_url(auth_url)
        return auth_url

    # ------------------------------------------------------------------
    # UI initialisieren
    # ------------------------------------------------------------------
    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        outer_layout.addWidget(self.tabs)

        github_tab = QWidget()
        main_layout = QVBoxLayout(github_tab)

        # ---------- Menüleiste ----------
        menubar = self.menuBar()

        self.tools_menu = menubar.addMenu(tr("menu_tools"))
        self.action_update_assistant = QAction(tr("menu_action_update_assistant"), self)
        self.action_update_assistant.setToolTip(tr("menu_action_update_assistant_tooltip"))
        self.action_update_assistant.setStatusTip(tr("menu_action_update_assistant_tooltip"))
        self.action_update_assistant.triggered.connect(self.on_open_update_assistant)
        self.tools_menu.addAction(self.action_update_assistant)

        self.help_menu = menubar.addMenu(tr("menu_help"))

        self.action_help = QAction(tr("menu_action_manual"), self)
        self.action_help.setShortcut("F1")
        self.action_help.setToolTip(tr("menu_action_manual_tooltip"))
        self.action_help.setStatusTip(tr("menu_action_manual_tooltip"))
        self.action_help.triggered.connect(self.on_show_help)
        self.help_menu.addAction(self.action_help)

        self.help_menu.addSeparator()

        self.action_about = QAction(tr("menu_action_about"), self)
        self.action_about.setToolTip(tr("menu_action_about_tooltip"))
        self.action_about.setStatusTip(tr("menu_action_about_tooltip"))
        self.action_about.triggered.connect(self.on_show_about)
        self.help_menu.addAction(self.action_about)

        # ---------- Sprachmenü ----------
        self.language_menu = menubar.addMenu(tr("menu_language"))
        self.language_action_group = QActionGroup(self)
        self.language_action_group.setExclusive(True)
        current_lang = get_current_language()
        for code, display_name in AVAILABLE_LANGUAGES.items():
            lang_action = QAction(display_name, self)
            lang_action.setCheckable(True)
            lang_action.setChecked(code == current_lang)
            tooltip = tr("menu_language_item_tooltip", language=display_name)
            lang_action.setToolTip(tooltip)
            lang_action.setStatusTip(tooltip)
            lang_action.triggered.connect(
                lambda checked, c=code: self.on_change_language(c)
            )
            self.language_action_group.addAction(lang_action)
            self.language_menu.addAction(lang_action)

        # ---------- Login ----------
        self.login_group = QGroupBox(tr("login_group_title"))
        login_layout = QVBoxLayout(self.login_group)

        user_layout = QHBoxLayout()
        self.user_label = QLabel(tr("login_username_label"))
        user_layout.addWidget(self.user_label)
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText(tr("login_username_placeholder"))
        self.user_edit.setToolTip(tr("login_username_tooltip"))
        user_layout.addWidget(self.user_edit)
        login_layout.addLayout(user_layout)

        token_layout = QHBoxLayout()
        self.token_label = QLabel(tr("login_token_label"))
        token_layout.addWidget(self.token_label)
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText(tr("login_token_placeholder"))
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setToolTip(tr("login_token_tooltip"))
        token_layout.addWidget(self.token_edit)
        login_layout.addLayout(token_layout)

        btn_login_layout = QHBoxLayout()
        self.connect_btn = QPushButton(tr("btn_connect"))
        self.connect_btn.setToolTip(tr("btn_connect_tooltip"))
        self.connect_btn.clicked.connect(self.on_connect)
        btn_login_layout.addWidget(self.connect_btn)

        self.check_token_btn = QPushButton(tr("btn_check_token"))
        self.check_token_btn.setToolTip(tr("btn_check_token_tooltip"))
        self.check_token_btn.clicked.connect(self.on_check_token)
        self.check_token_btn.setEnabled(False)
        btn_login_layout.addWidget(self.check_token_btn)

        self.create_token_btn = QPushButton(tr("btn_create_token"))
        self.create_token_btn.setToolTip(tr("btn_create_token_tooltip"))
        self.create_token_btn.clicked.connect(self.on_create_token)
        btn_login_layout.addWidget(self.create_token_btn)

        login_layout.addLayout(btn_login_layout)
        main_layout.addWidget(self.login_group)

        # ---------- Repository-Liste ----------
        self.list_group = QGroupBox(tr("repolist_group_title"))
        list_layout = QVBoxLayout(self.list_group)

        self.repo_list = QListWidget()
        self.repo_list.setToolTip(tr("repolist_tooltip"))
        self.repo_list.itemSelectionChanged.connect(self.on_repo_selected)
        list_layout.addWidget(self.repo_list)

        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton(tr("btn_new_repo"))
        self.new_btn.setToolTip(tr("btn_new_repo_tooltip"))
        self.new_btn.clicked.connect(self.on_new_repo)
        self.new_btn.setEnabled(False)
        btn_layout.addWidget(self.new_btn)

        self.delete_btn = QPushButton(tr("btn_delete_repo"))
        self.delete_btn.setToolTip(tr("btn_delete_repo_tooltip"))
        self.delete_btn.clicked.connect(self.on_delete_repo)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        self.refresh_btn = QPushButton(tr("btn_refresh"))
        self.refresh_btn.setToolTip(tr("btn_refresh_tooltip"))
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.refresh_btn.setEnabled(False)
        btn_layout.addWidget(self.refresh_btn)

        list_layout.addLayout(btn_layout)
        main_layout.addWidget(self.list_group)

        # ---------- Lokales Repository ----------
        self.local_group = QGroupBox(tr("local_group_title"))
        local_layout = QVBoxLayout(self.local_group)

        # Standardordner
        default_layout = QHBoxLayout()
        self.default_folder_label = QLabel(tr("local_default_folder_label"))
        default_layout.addWidget(self.default_folder_label)
        self.default_folder_edit = QLineEdit()
        self.default_folder_edit.setReadOnly(True)
        self.default_folder_edit.setPlaceholderText(tr("local_default_folder_placeholder"))
        default_layout.addWidget(self.default_folder_edit)

        self.set_default_btn = QPushButton(tr("btn_set_default"))
        self.set_default_btn.setToolTip(tr("btn_set_default_tooltip"))
        self.set_default_btn.clicked.connect(self.on_set_default_folder)
        default_layout.addWidget(self.set_default_btn)

        self.change_default_btn = QPushButton(tr("btn_change_default"))
        self.change_default_btn.setToolTip(tr("btn_change_default_tooltip"))
        self.change_default_btn.clicked.connect(self.on_change_default_folder)
        default_layout.addWidget(self.change_default_btn)

        local_layout.addLayout(default_layout)

        # Aktionen
        action_layout = QHBoxLayout()
        self.clone_btn = QPushButton(tr("btn_clone"))
        self.clone_btn.setToolTip(tr("btn_clone_tooltip"))
        self.clone_btn.clicked.connect(self.on_clone_repo)
        self.clone_btn.setEnabled(False)
        action_layout.addWidget(self.clone_btn)

        self.init_btn = QPushButton(tr("btn_init"))
        self.init_btn.setToolTip(tr("btn_init_tooltip"))
        self.init_btn.clicked.connect(self.on_init_repo)
        self.init_btn.setEnabled(False)
        action_layout.addWidget(self.init_btn)

        self.browse_btn = QPushButton(tr("btn_browse"))
        self.browse_btn.setToolTip(tr("btn_browse_tooltip"))
        self.browse_btn.clicked.connect(self.on_browse_folder)
        self.browse_btn.setEnabled(False)
        action_layout.addWidget(self.browse_btn)

        local_layout.addLayout(action_layout)

        # Pfad
        path_layout = QHBoxLayout()
        self.path_label = QLabel(tr("local_loaded_label"))
        path_layout.addWidget(self.path_label)
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText(tr("local_loaded_placeholder"))
        path_layout.addWidget(self.path_edit)
        local_layout.addLayout(path_layout)

        # Commit
        commit_layout = QHBoxLayout()
        self.commit_label = QLabel(tr("local_commit_msg_label"))
        commit_layout.addWidget(self.commit_label)
        self.commit_msg_edit = QLineEdit()
        self.commit_msg_edit.setPlaceholderText(tr("local_commit_msg_placeholder"))
        commit_layout.addWidget(self.commit_msg_edit)

        self.commit_btn = QPushButton(tr("btn_commit"))
        self.commit_btn.setToolTip(tr("btn_commit_tooltip"))
        self.commit_btn.clicked.connect(self.on_commit)
        self.commit_btn.setEnabled(False)
        commit_layout.addWidget(self.commit_btn)

        local_layout.addLayout(commit_layout)

        # Push/Pull/Branch
        push_pull_layout = QHBoxLayout()
        self.push_btn = QPushButton(tr("btn_push"))
        self.push_btn.setToolTip(tr("btn_push_tooltip"))
        self.push_btn.clicked.connect(self.on_push)
        self.push_btn.setEnabled(False)
        push_pull_layout.addWidget(self.push_btn)

        self.pull_btn = QPushButton(tr("btn_pull"))
        self.pull_btn.setToolTip(tr("btn_pull_tooltip"))
        self.pull_btn.clicked.connect(self.on_pull)
        self.pull_btn.setEnabled(False)
        push_pull_layout.addWidget(self.pull_btn)

        self.release_btn = QPushButton(tr("btn_release"))
        self.release_btn.setToolTip(tr("btn_release_tooltip"))
        self.release_btn.clicked.connect(self.on_create_release)
        self.release_btn.setEnabled(False)
        push_pull_layout.addWidget(self.release_btn)

        self.link_remote_btn = QPushButton(tr("btn_link_remote"))
        self.link_remote_btn.setToolTip(tr("btn_link_remote_tooltip"))
        self.link_remote_btn.clicked.connect(self.on_link_remote)
        self.link_remote_btn.setEnabled(False)
        push_pull_layout.addWidget(self.link_remote_btn)

        self.branch_label = QLabel(tr("branch_label_empty"))
        push_pull_layout.addWidget(self.branch_label)
        push_pull_layout.addStretch()

        local_layout.addLayout(push_pull_layout)

        # Status-Analyse / Aktionsempfehlung
        recommend_layout = QHBoxLayout()
        self.check_status_btn = QPushButton(tr("btn_check_status"))
        self.check_status_btn.setToolTip(tr("btn_check_status_tooltip"))
        self.check_status_btn.clicked.connect(self.on_check_status)
        self.check_status_btn.setEnabled(False)
        recommend_layout.addWidget(self.check_status_btn)

        self.recommendation_label = QLabel(tr("recommendation_none"))
        self.recommendation_label.setWordWrap(True)
        recommend_layout.addWidget(self.recommendation_label, 1)

        self.suggested_action_btn = QPushButton(tr("btn_suggested_action"))
        self.suggested_action_btn.setToolTip(tr("btn_suggested_action_tooltip"))
        self.suggested_action_btn.clicked.connect(self.on_suggested_action)
        self.suggested_action_btn.setEnabled(False)
        recommend_layout.addWidget(self.suggested_action_btn)

        local_layout.addLayout(recommend_layout)

        main_layout.addWidget(self.local_group)

        self.tabs.addTab(github_tab, tr("tab_github"))

        # ---------- AUR-Tab ----------
        aur_tab = QWidget()
        aur_outer_layout = QVBoxLayout(aur_tab)

        self.aur_group = QGroupBox(tr("aur_group_title"))
        aur_layout = QVBoxLayout(self.aur_group)

        aur_intro = QLabel(tr("aur_intro_text"))
        aur_intro.setWordWrap(True)
        aur_layout.addWidget(aur_intro)
        self.aur_intro_label = aur_intro

        # Ordner des lokal geklonten AUR-Repositories
        aur_folder_layout = QHBoxLayout()
        self.aur_folder_label = QLabel(tr("aur_folder_label"))
        aur_folder_layout.addWidget(self.aur_folder_label)
        self.aur_folder_edit = QLineEdit()
        self.aur_folder_edit.setReadOnly(True)
        self.aur_folder_edit.setPlaceholderText(tr("aur_folder_placeholder"))
        aur_folder_layout.addWidget(self.aur_folder_edit)
        self.aur_browse_btn = QPushButton(tr("btn_aur_browse"))
        self.aur_browse_btn.setToolTip(tr("btn_aur_browse_tooltip"))
        self.aur_browse_btn.clicked.connect(self.on_aur_browse_folder)
        aur_folder_layout.addWidget(self.aur_browse_btn)
        self.aur_new_package_btn = QPushButton(tr("btn_aur_new_package"))
        self.aur_new_package_btn.setToolTip(tr("btn_aur_new_package_tooltip"))
        self.aur_new_package_btn.clicked.connect(self.on_new_aur_package)
        aur_folder_layout.addWidget(self.aur_new_package_btn)
        aur_layout.addLayout(aur_folder_layout)

        # Aktuell erkannte Paketinfo (Name/Version/Release aus der PKGBUILD)
        self.aur_info_label = QLabel(tr("aur_info_none"))
        self.aur_info_label.setWordWrap(True)
        aur_layout.addWidget(self.aur_info_label)

        # Neue Version eingeben
        aur_version_layout = QHBoxLayout()
        self.aur_version_label = QLabel(tr("aur_version_label"))
        aur_version_layout.addWidget(self.aur_version_label)
        self.aur_version_edit = QLineEdit()
        self.aur_version_edit.setPlaceholderText(tr("aur_version_placeholder"))
        aur_version_layout.addWidget(self.aur_version_edit)
        self.aur_update_btn = QPushButton(tr("btn_aur_update"))
        self.aur_update_btn.setToolTip(tr("btn_aur_update_tooltip"))
        self.aur_update_btn.clicked.connect(self.on_aur_update_version)
        self.aur_update_btn.setEnabled(False)
        aur_version_layout.addWidget(self.aur_update_btn)
        aur_layout.addLayout(aur_version_layout)

        # Sichtbarer Reihenfolge-Hinweis: zeigt, ob "Version aktualisieren"
        # in diesem Durchlauf bereits gelaufen ist, bevor committet/gepusht
        # wird (siehe _guard_aur_push_order()).
        self.aur_step_indicator_label = QLabel()
        self.aur_step_indicator_label.setWordWrap(True)
        aur_layout.addWidget(self.aur_step_indicator_label)

        # Commit & Push zum AUR
        aur_commit_layout = QHBoxLayout()
        self.aur_commit_label = QLabel(tr("aur_commit_msg_label"))
        aur_commit_layout.addWidget(self.aur_commit_label)
        self.aur_commit_msg_edit = QLineEdit()
        self.aur_commit_msg_edit.setPlaceholderText(tr("aur_commit_msg_placeholder"))
        aur_commit_layout.addWidget(self.aur_commit_msg_edit)
        self.aur_commit_push_btn = QPushButton(tr("btn_aur_commit_push"))
        self.aur_commit_push_btn.setToolTip(tr("btn_aur_commit_push_tooltip"))
        self.aur_commit_push_btn.clicked.connect(self.on_aur_commit_push)
        self.aur_commit_push_btn.setEnabled(False)
        aur_commit_layout.addWidget(self.aur_commit_push_btn)
        aur_layout.addLayout(aur_commit_layout)

        # Status-Analyse / Aktionsempfehlung (analog zum GitHub-Tab)
        aur_recommend_layout = QHBoxLayout()
        self.aur_check_status_btn = QPushButton(tr("btn_aur_check_status"))
        self.aur_check_status_btn.setToolTip(tr("btn_aur_check_status_tooltip"))
        self.aur_check_status_btn.clicked.connect(self.on_aur_check_status)
        self.aur_check_status_btn.setEnabled(False)
        aur_recommend_layout.addWidget(self.aur_check_status_btn)

        self.aur_recommendation_label = QLabel(tr("aur_recommendation_none"))
        self.aur_recommendation_label.setWordWrap(True)
        aur_recommend_layout.addWidget(self.aur_recommendation_label, 1)

        self.aur_suggested_action_btn = QPushButton(tr("btn_aur_suggested_action"))
        self.aur_suggested_action_btn.setToolTip(tr("btn_aur_suggested_action_tooltip"))
        self.aur_suggested_action_btn.clicked.connect(self.on_aur_suggested_action)
        self.aur_suggested_action_btn.setEnabled(False)
        aur_recommend_layout.addWidget(self.aur_suggested_action_btn)

        aur_layout.addLayout(aur_recommend_layout)

        aur_outer_layout.addWidget(self.aur_group)
        aur_outer_layout.addStretch()

        self.tabs.addTab(aur_tab, tr("tab_aur"))
        self.aur_tab_widget = aur_tab

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

    # ------------------------------------------------------------------
    # Standardordner
    # ------------------------------------------------------------------
    def load_settings(self):
        settings = load_settings()
        if 'default_folder' in settings:
            self.default_folder = settings['default_folder']
            self.default_folder_edit.setText(self.default_folder)
        else:
            default = os.path.join(os.path.expanduser("~"), "GitHub")
            if os.path.exists(default) or os.access(os.path.dirname(default), os.W_OK):
                self.default_folder = default
                self.default_folder_edit.setText(default)
                settings['default_folder'] = default
                save_settings(settings)

        aur_folder = settings.get('aur_default_folder')
        if aur_folder and os.path.isdir(aur_folder):
            # Bewusst ohne Fehlerdialoge: der gespeicherte Ordner könnte
            # zwischenzeitlich verschoben oder gelöscht worden sein - in
            # dem Fall soll der Start nicht durch eine Meldung gestört werden.
            self._load_aur_repo(aur_folder, show_errors=False)

    def save_default_folder(self, folder):
        self.default_folder = folder
        self.default_folder_edit.setText(folder)
        settings = load_settings()
        settings['default_folder'] = folder
        save_settings(settings)

    def on_set_default_folder(self):
        if self.local_repo_path and os.path.isdir(self.local_repo_path):
            self.save_default_folder(self.local_repo_path)
            self.status_bar.showMessage(tr("status_default_folder_set", folder=self.local_repo_path))
        else:
            QMessageBox.warning(self, tr("msg_no_repo_title"), tr("msg_load_local_first"))

    def on_change_default_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("dlg_choose_default_folder"),
            self.default_folder or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.save_default_folder(folder)
            self.status_bar.showMessage(tr("status_default_folder_changed", folder=folder))

    # ------------------------------------------------------------------
    # Login / Token
    # ------------------------------------------------------------------
    def load_saved_credentials(self):
        config = load_config()
        if 'username' in config:
            self.user_edit.setText(config['username'])
        if 'token' in config:
            self.token = config['token']
            self.token_edit.setText(config['token'])
            if 'saved_at' in config:
                try:
                    saved = datetime.datetime.fromisoformat(config['saved_at'])
                    age = datetime.datetime.now() - saved
                    days = age.days
                    self.status_bar.showMessage(tr("status_token_saved_days", days=days))
                except:
                    pass
            self.check_token_btn.setEnabled(True)
            self.on_check_token()
        else:
            self.check_token_btn.setEnabled(False)

    def on_check_token(self):
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.information(self, tr("msg_token_check_title"), tr("msg_token_check_empty"))
            return

        self.status_bar.showMessage(tr("status_checking_token"))
        self.check_token_btn.setEnabled(False)

        def test_token():
            auth = Auth.Token(token)
            g = Github(auth=auth)
            user = g.get_user()
            return user.login

        self.worker = GithubWorker(test_token)
        self.worker.finished.connect(self._on_token_valid)
        self.worker.error.connect(self._on_token_invalid)
        self.worker.start()

    def _on_token_valid(self, username):
        self.check_token_btn.setEnabled(True)
        config = load_config()
        if 'saved_at' in config:
            try:
                saved = datetime.datetime.fromisoformat(config['saved_at'])
                age = datetime.datetime.now() - saved
                days = age.days
                self.status_bar.showMessage(
                    tr("status_token_valid_days", username=username, days=days)
                )
            except:
                self.status_bar.showMessage(tr("status_token_valid", username=username))
        else:
            self.status_bar.showMessage(tr("status_token_valid", username=username))

    def _on_token_invalid(self, error_msg):
        self.check_token_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_token_invalid"))
        if "401" in error_msg or "Bad credentials" in error_msg:
            reply = QMessageBox.warning(
                self,
                tr("msg_token_invalid_title"),
                tr("msg_token_invalid_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.token_edit.clear()
                self.token_edit.setFocus()
        else:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_token_check_error", error=error_msg))

    def on_create_token(self):
        webbrowser.open("https://github.com/settings/tokens")
        QMessageBox.information(
            self,
            tr("msg_create_token_title"),
            tr("msg_create_token_text")
        )

    def on_connect(self):
        username = self.user_edit.text().strip()
        token = self.token_edit.text().strip()
        if not username or not token:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_username_token_required"))
            return
        self.status_bar.showMessage(tr("status_connecting"))
        self.connect_btn.setEnabled(False)

        self.worker = GithubWorker(self._connect_to_github, username, token)
        self.worker.finished.connect(self._on_connect_finished)
        self.worker.error.connect(self._on_connect_error)
        self.worker.start()

    def _connect_to_github(self, username, token):
        auth = Auth.Token(token)
        g = Github(auth=auth)
        user = g.get_user()
        repos = list(user.get_repos())
        return (g, user, repos, token)

    def _on_connect_finished(self, result):
        self.github, self.current_user, self.repos, self.token = result
        self.connect_btn.setEnabled(True)
        self.new_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.check_token_btn.setEnabled(True)
        self.browse_btn.setEnabled(True)
        self.clone_btn.setEnabled(True)
        self.init_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_connected_as", username=self.current_user.login))
        self._populate_repo_list()
        save_config(self.user_edit.text().strip(), self.token)

    def _on_connect_error(self, error_msg):
        self.connect_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_connect_failed"))
        QMessageBox.critical(self, tr("msg_connect_error_title"), tr("msg_connect_error_text", error=error_msg))

    # ------------------------------------------------------------------
    # Repository-Liste
    # ------------------------------------------------------------------
    def _populate_repo_list(self):
        self.repo_list.clear()
        for repo in self.repos:
            item = QListWidgetItem(repo.name)
            item.setData(Qt.ItemDataRole.UserRole, repo)
            self.repo_list.addItem(item)

    def on_repo_selected(self):
        selected_items = self.repo_list.selectedItems()
        if selected_items:
            self.selected_repo = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.delete_btn.setEnabled(True)
            self.release_btn.setEnabled(True)
        else:
            self.selected_repo = None
            self.delete_btn.setEnabled(False)
            self.release_btn.setEnabled(False)

    def on_refresh(self):
        if not self.github or not self.current_user:
            return
        self.status_bar.showMessage(tr("status_loading_repos"))
        self.refresh_btn.setEnabled(False)
        self.worker = GithubWorker(self._refresh_repos)
        self.worker.finished.connect(self._on_refresh_finished)
        self.worker.error.connect(self._on_refresh_error)
        self.worker.start()

    def _refresh_repos(self):
        return list(self.current_user.get_repos())

    def _on_refresh_finished(self, repos):
        self.repos = repos
        self._populate_repo_list()
        self.refresh_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_repos_refreshed"))

    def _on_refresh_error(self, error_msg):
        self.refresh_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_refresh_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_connect_error_text", error=error_msg))

    # ------------------------------------------------------------------
    # Neues Repository / Löschen
    # ------------------------------------------------------------------
    def on_new_repo(self):
        if not self.github:
            return
        dialog = NewRepoDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_repo_data()
            if not data["name"]:
                QMessageBox.warning(self, tr("msg_error_title"), tr("msg_repo_name_empty"))
                return
            # Beschreibung bereinigen
            description = data["description"]
            cleaned_description = re.sub(r'[\x00-\x1F\x7F]', ' ', description)
            cleaned_description = re.sub(r'\s+', ' ', cleaned_description).strip()
            data["description"] = cleaned_description

            self.status_bar.showMessage(tr("status_creating_repo", name=data['name']))
            self.new_btn.setEnabled(False)
            self.worker = GithubWorker(self._create_repo, data)
            self.worker.finished.connect(self._on_create_finished)
            self.worker.error.connect(self._on_create_error)
            self.worker.start()

    def _create_repo(self, data):
        return self.current_user.create_repo(
            name=data["name"],
            description=data["description"],
            private=data["private"]
        )

    def _on_create_finished(self, repo):
        self.new_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_repo_created", name=repo.name))
        self.on_refresh()
        reply = QMessageBox.question(
            self, tr("msg_aur_offer_title"),
            tr("msg_aur_offer_text", name=repo.name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.on_new_aur_package(prefill_repo=repo)

    def _on_create_error(self, error_msg):
        self.new_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_create_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_create_error", error=error_msg))

    def on_delete_repo(self):
        if not self.selected_repo:
            return
        repo_name = self.selected_repo.name
        reply = QMessageBox.question(
            self,
            tr("msg_delete_confirm_title"),
            tr("msg_delete_confirm_text", name=repo_name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.status_bar.showMessage(tr("status_deleting_repo", name=repo_name))
        self.delete_btn.setEnabled(False)
        self.worker = GithubWorker(self._delete_repo, self.selected_repo)
        self.worker.finished.connect(self._on_delete_finished)
        self.worker.error.connect(self._on_delete_error)
        self.worker.start()

    def _delete_repo(self, repo):
        repo.delete()

    def _on_delete_finished(self, _):
        self.delete_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_repo_deleted"))
        self.selected_repo = None
        self.on_refresh()

    def _on_delete_error(self, error_msg):
        self.delete_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_delete_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_delete_error", error=error_msg))

    def _local_repo_matches_selected(self):
        """True, wenn das aktuell lokal geladene Repository (self.repo_obj)
        zum in der Liste ausgewählten GitHub-Repository (self.selected_repo)
        gehört (Vergleich über die Remote-URL). Nur wenn das zutrifft, kann
        vor einem Release sinnvoll geprüft werden, ob committete/gepushte
        Änderungen fehlen."""
        if not self.repo_obj or not self.selected_repo or not self.repo_obj.remotes:
            return False
        try:
            origin_url = self.repo_obj.remotes.origin.url
        except Exception:
            return False
        if "@" in origin_url and "://" in origin_url:
            base = "https://" + origin_url.split("@")[-1]
        else:
            base = origin_url
        base = base.rstrip("/")
        if base.lower().endswith(".git"):
            base = base[:-4]
        return base.lower().endswith(self.selected_repo.full_name.lower())

    def on_create_release(self):
        """Erstellt ein neues GitHub-Release (inkl. Tag) für das aktuell
        ausgewählte Repository. Benötigt kein lokal ausgechecktes Repo -
        die Auswahl in der Repo-Liste genügt.

        Reihenfolge-Sperre: ein Release taggt den aktuellen Stand AUF
        GITHUB. Ist zufällig das passende lokale Repo geladen und dort
        gibt es noch uncommittete Änderungen oder ungepushte Commits,
        würde das Release diese NICHT enthalten. Wird das erkannt (nach
        einem kurzen Status-Check), fragt das Tool vorher nach, statt
        stillschweigend ein Release auf einem veralteten Stand zu bauen."""
        if not self.selected_repo:
            QMessageBox.warning(self, tr("msg_no_github_repo_title"), tr("msg_no_github_repo_text_release"))
            return

        if self._local_repo_matches_selected():
            self.status_bar.showMessage(tr("status_checking_repo_state"))
            self.release_btn.setEnabled(False)
            self.worker = GithubWorker(self._analyze_repo_state)
            self.worker.finished.connect(self._on_release_precheck_finished)
            self.worker.error.connect(self._on_release_precheck_error)
            self.worker.start()
        else:
            # Kein passendes lokales Repo geladen - wir können den
            # Commit/Push-Stand nicht prüfen, also direkt zum Dialog.
            self._open_release_dialog()

    def _on_release_precheck_finished(self, result):
        self.release_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_ready"))
        if self._confirm_release_order(result):
            self._open_release_dialog()

    def _on_release_precheck_error(self, _error_msg):
        # Status konnte nicht ermittelt werden (z.B. kein Netzwerk beim
        # Fetch) - lieber nicht blockieren, aber auch nicht so tun, als
        # wäre geprüft worden.
        self.release_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_ready"))
        self._open_release_dialog()

    def _confirm_release_order(self, state):
        """Zeigt bei Bedarf die Reihenfolge-Warnung (Commit -> Push ->
        Release) und gibt True zurück, wenn trotzdem fortgefahren werden
        soll (bzw. wenn alles bereits sauber ist)."""
        kind = state.get("state")
        if kind == "merge_pending":
            text_key = "msg_release_order_warning_merge"
        elif kind == "commit_needed":
            text_key = "msg_release_order_warning_commit"
        elif kind in ("push_needed", "diverged"):
            text_key = "msg_release_order_warning_push"
        else:
            # up_to_date, pull_needed, no_remote, no_auth, unknown: kein
            # committeter/gepushter Stand fehlt erkennbar - nichts zu tun.
            return True

        reply = QMessageBox.question(
            self,
            tr("msg_release_order_warning_title"),
            tr(text_key),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def _open_release_dialog(self, suggested_tag=""):
        # Standard-Branch als Vorschlag für das Ziel des Tags vorbelegen
        try:
            default_branch = self.selected_repo.default_branch
        except Exception:
            default_branch = ""

        dialog = NewReleaseDialog(self, suggested_tag=suggested_tag)
        dialog.target_branch_edit.setText(default_branch or "")
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_release_data()
        if not data["tag"]:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_release_tag_empty"))
            return

        release_title = data["title"] or data["tag"]

        self.status_bar.showMessage(tr("status_creating_release", tag=data["tag"]))
        self.release_btn.setEnabled(False)
        self.worker = GithubWorker(
            self._create_release,
            self.selected_repo,
            data["tag"],
            release_title,
            data["notes"],
            data["prerelease"],
            data["draft"],
            data["target_branch"],
        )
        self.worker.finished.connect(self._on_release_finished)
        self.worker.error.connect(self._on_release_error)
        self.worker.start()

    def _create_release(self, repo, tag, title, notes, prerelease, draft, target_branch):
        kwargs = {
            "tag": tag,
            "name": title,
            "message": notes,
            "draft": draft,
            "prerelease": prerelease,
        }
        # target_commitish nur setzen, wenn explizit angegeben - sonst
        # verwendet GitHub automatisch den Standard-Branch des Repos.
        if target_branch:
            kwargs["target_commitish"] = target_branch
        return repo.create_git_release(**kwargs)

    def _on_release_finished(self, release):
        self.release_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_release_created", tag=release.tag_name))
        QMessageBox.information(
            self,
            tr("msg_release_created_title"),
            tr("msg_release_created_text", tag=release.tag_name, url=release.html_url)
        )

    def _on_release_error(self, error_msg):
        self.release_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_release_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_release_error", error=error_msg))

    # ------------------------------------------------------------------
    # Lokales Repository
    # ------------------------------------------------------------------
    def _load_repo(self, folder):
        try:
            repo = Repo(folder)
            branch = repo.active_branch.name
            self.branch_label.setText(tr("branch_label", branch=branch))
            self.local_repo_path = folder
            self.repo_obj = repo
            self.path_edit.setText(folder)
            self.commit_btn.setEnabled(True)
            self.check_status_btn.setEnabled(True)

            if not repo.remotes:
                # Kein Remote vorhanden: Repo trotzdem laden (Commit ist ja
                # unabhängig von GitHub möglich), aber Push/Pull sind erst
                # nach Verknüpfung mit einem GitHub-Repository sinnvoll.
                self.push_btn.setEnabled(False)
                self.pull_btn.setEnabled(False)
                self.link_remote_btn.setEnabled(True)
                self.status_bar.showMessage(tr("status_local_repo_loaded_no_remote", folder=folder))
                QMessageBox.information(
                    self,
                    tr("msg_no_remote_title"),
                    tr("msg_no_remote_text", folder=folder)
                )
            else:
                self.push_btn.setEnabled(True)
                self.pull_btn.setEnabled(True)
                self.link_remote_btn.setEnabled(True)
                self.status_bar.showMessage(tr("status_local_repo_loaded", folder=folder))
            self.on_check_status()
            return True
        except InvalidGitRepositoryError:
            QMessageBox.critical(self, tr("msg_no_git_repo_title"), tr("msg_no_git_repo_text", folder=folder))
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_load_error", error=e))
        return False

    def on_link_remote(self):
        """Verknüpft das geladene lokale Repository mit dem ausgewählten
        GitHub-Repository, indem der Remote 'origin' gesetzt bzw. überschrieben wird."""
        if not self.repo_obj:
            QMessageBox.warning(self, tr("msg_no_repo_title"), tr("msg_load_local_first"))
            return
        if not self.selected_repo:
            QMessageBox.warning(
                self,
                tr("msg_no_github_repo_title"),
                tr("msg_no_github_repo_text_link")
            )
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_connect_first"))
            return

        try:
            username = self.current_user.login
            token = self.token
            clone_url = self.selected_repo.clone_url
            auth_url = f"https://{username}:{token}@{clone_url[8:]}"

            if "origin" in [r.name for r in self.repo_obj.remotes]:
                origin = self.repo_obj.remotes.origin
                origin.set_url(auth_url)
            else:
                self.repo_obj.create_remote("origin", auth_url)

            self.push_btn.setEnabled(True)
            self.pull_btn.setEnabled(True)
            self.status_bar.showMessage(
                tr("status_linked_to_repo", full_name=self.selected_repo.full_name)
            )
            QMessageBox.information(
                self,
                tr("msg_linked_title"),
                tr("msg_linked_text", full_name=self.selected_repo.full_name)
            )
            self.on_check_status()
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_link_error", error=e))

    def on_browse_folder(self):
        start_dir = self.default_folder if self.default_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("dlg_choose_local_repo_folder"),
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._load_repo(folder)

    def on_clone_repo(self):
        if not self.selected_repo:
            QMessageBox.warning(self, tr("msg_no_repo_title"), tr("msg_load_local_first"))
            return
        if not self.default_folder:
            QMessageBox.warning(self, tr("msg_no_default_folder_title"), tr("msg_no_default_folder_text"))
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_connect_first"))
            return

        repo_name = self.selected_repo.name
        target_dir = os.path.join(self.default_folder, repo_name)

        if os.path.exists(target_dir):
            reply = QMessageBox.question(
                self,
                tr("msg_folder_exists_title"),
                tr("msg_folder_exists_text", folder=target_dir),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.status_bar.showMessage(tr("status_cloning", name=repo_name))
        self.clone_btn.setEnabled(False)

        def do_clone():
            username = self.current_user.login
            token = self.token
            url = self.selected_repo.clone_url
            auth_url = f"https://{username}:{token}@{url[8:]}"
            repo = Repo.clone_from(auth_url, target_dir)
            return repo

        self.worker = GithubWorker(do_clone)
        self.worker.finished.connect(self._on_clone_finished)
        self.worker.error.connect(self._on_clone_error)
        self.worker.start()

    def _on_clone_finished(self, repo):
        self.clone_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_cloned", path=repo.working_dir))
        self._load_repo(repo.working_dir)

    def _on_clone_error(self, error_msg):
        self.clone_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_clone_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_clone_error", error=error_msg))

    def on_init_repo(self):
        if not self.default_folder:
            QMessageBox.warning(self, tr("msg_no_default_folder_title"), tr("msg_no_default_folder_text"))
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_connect_first"))
            return
        if not self.selected_repo:
            # Das ist die Ursache von "Kein Remote konfiguriert": ein frisch mit
            # 'git init' erstelltes Repository hat noch keinen Remote. Ohne ein
            # ausgewähltes GitHub-Repository wüsste die App nicht, welches
            # Remote sie setzen soll.
            QMessageBox.warning(
                self,
                tr("msg_no_github_repo_title"),
                tr("msg_no_github_repo_text_init")
            )
            return

        # Warnung, falls das GitHub-Repository bereits Inhalte hat: 'git init' +
        # Push würde dann auf unzusammenhängende Historien treffen und scheitern
        # (bzw. einen Force-Push erfordern). In diesem Fall ist 'Repository
        # klonen' der richtige Weg.
        if getattr(self.selected_repo, "size", 0) and self.selected_repo.size > 0:
            reply = QMessageBox.question(
                self,
                tr("msg_repo_not_empty_title"),
                tr("msg_repo_not_empty_text", name=self.selected_repo.name),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        name, ok = QInputDialog.getText(
            self,
            tr("msg_new_repo_dialog_title"),
            tr("msg_new_repo_dialog_label"),
            text=self.selected_repo.name
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        target_dir = os.path.join(self.default_folder, name)

        if os.path.exists(target_dir):
            QMessageBox.warning(self, tr("msg_exists_title"), tr("msg_exists_text", folder=target_dir))
            return

        try:
            os.makedirs(target_dir)
            repo = Repo.init(target_dir)

            # Remote 'origin' auf das ausgewählte GitHub-Repository setzen –
            # ohne diesen Schritt bleibt das Repo dauerhaft ohne Remote.
            username = self.current_user.login
            token = self.token
            clone_url = self.selected_repo.clone_url
            auth_url = f"https://{username}:{token}@{clone_url[8:]}"
            repo.create_remote("origin", auth_url)

            self.status_bar.showMessage(
                tr("status_init_done", full_name=self.selected_repo.full_name, path=target_dir)
            )
            self._load_repo(target_dir)
        except Exception as e:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_init_error", error=e))

    # ------------------------------------------------------------------
    # Merge-Status prüfen und auflösen (vor Push/Pull)
    # ------------------------------------------------------------------
    def _merge_in_progress(self, repo=None):
        """True, wenn im Repo ein Merge begonnen, aber nicht abgeschlossen
        wurde. Git legt dafür die Datei .git/MERGE_HEAD an und entfernt sie
        erst wieder, wenn der Merge-Commit gemacht oder der Merge mit
        'git merge --abort' verworfen wird. Ohne Angabe wird das GitHub-Repo
        geprüft (bisheriges Verhalten); für den AUR-Tab wird self.aur_repo_obj
        übergeben."""
        if repo is None:
            repo = self.repo_obj
        if not repo:
            return False
        return os.path.exists(os.path.join(repo.git_dir, "MERGE_HEAD"))

    def _has_unresolved_conflicts(self, repo=None):
        """True, wenn 'git status --porcelain' noch nicht zusammengeführte
        Pfade zeigt (Statuscodes UU/AA/DD/AU/UA/UD/DU = Konfliktmarker
        wurden noch nicht von Hand aufgelöst)."""
        if repo is None:
            repo = self.repo_obj
        conflict_codes = {"UU", "AA", "DD", "AU", "UA", "UD", "DU"}
        status_output = repo.git.status(porcelain=True)
        return any(line[:2] in conflict_codes for line in status_output.splitlines())

    def _resolve_pending_merge(self, repo=None):
        """Wird vor jedem Push/Pull aufgerufen. Prüft, ob noch ein
        unabgeschlossener Merge offen ist (z.B. weil eine frühere
        Konfliktlösung nicht zu Ende geführt wurde) und lässt den Nutzer
        entscheiden: Merge committen oder verwerfen. Läuft bewusst im
        GUI-Thread (vor dem Start des Workers), da QMessageBox-Dialoge
        keinen Worker-Thread verwenden dürfen. Ohne Angabe wird das
        GitHub-Repo verwendet; für den AUR-Tab wird self.aur_repo_obj
        übergeben.

        Rückgabe: True, wenn fortgefahren werden kann (kein offener Merge,
        oder er wurde soeben aufgelöst). False, wenn der Nutzer abgebrochen
        hat oder die Auflösung fehlschlug."""
        if repo is None:
            repo = self.repo_obj
        if not self._merge_in_progress(repo):
            return True

        if self._has_unresolved_conflicts(repo):
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Warning)
            box.setWindowTitle(tr("msg_merge_pending_title"))
            box.setText(tr("msg_merge_conflicts_unresolved_text"))
            btn_abort = box.addButton(tr("btn_merge_abort"), QMessageBox.ButtonRole.DestructiveRole)
            box.addButton(tr("btn_cancel"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_abort)
            box.exec()
            if box.clickedButton() == btn_abort:
                try:
                    repo.git.merge(abort=True)
                    self.status_bar.showMessage(tr("status_merge_aborted"))
                    return True
                except GitCommandError as e:
                    QMessageBox.critical(self, tr("msg_error_title"), tr("msg_merge_abort_error", error=e))
            return False

        # Keine offenen Konflikte mehr - der Merge wurde nur noch nicht
        # committet (z.B. weil das Programm oder das Terminal dazwischen
        # geschlossen wurde).
        box = QMessageBox(self)
        box.setIcon(QMessageBox.Icon.Question)
        box.setWindowTitle(tr("msg_merge_pending_title"))
        box.setText(tr("msg_merge_pending_text"))
        btn_commit = box.addButton(tr("btn_merge_commit"), QMessageBox.ButtonRole.AcceptRole)
        btn_abort = box.addButton(tr("btn_merge_abort"), QMessageBox.ButtonRole.DestructiveRole)
        box.addButton(tr("btn_cancel"), QMessageBox.ButtonRole.RejectRole)
        box.setDefaultButton(btn_commit)
        box.exec()
        clicked = box.clickedButton()
        try:
            if clicked == btn_commit:
                repo.git.commit(no_edit=True)
                self.status_bar.showMessage(tr("status_merge_committed"))
                return True
            if clicked == btn_abort:
                repo.git.merge(abort=True)
                self.status_bar.showMessage(tr("status_merge_aborted"))
                return True
        except GitCommandError as e:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_merge_resolve_error", error=e))
        return False

    # ------------------------------------------------------------------
    # Status-Analyse und Aktionsempfehlung
    # ------------------------------------------------------------------
    def _analyze_repo_state(self):
        """Ermittelt den aktuellen Zustand des geladenen Repositories und
        leitet daraus eine empfohlene nächste Aktion ab. Läuft im
        Worker-Thread, da das Ermitteln von Ahead/Behind einen 'fetch'
        (Netzwerkzugriff) erfordert.

        Reihenfolge der Prüfung (jede weitere Prüfung ist nur sinnvoll,
        wenn die vorherige unauffällig ist):
        1. Offener, unabgeschlossener Merge?
        2. Uncommittete Änderungen (staged/unstaged/untracked)?
        3. Kein Remote verknüpft?
        4. Nicht angemeldet (kein Token/Benutzer)?
        5. Ahead/Behind-Vergleich mit dem Remote-Branch nach 'fetch'.
        """
        result = {"state": "unknown", "dirty_count": 0, "ahead": 0, "behind": 0}

        if self._merge_in_progress():
            result["state"] = "merge_pending"
            return result

        status_output = self.repo_obj.git.status(porcelain=True)
        dirty_lines = [line for line in status_output.splitlines() if line.strip()]
        result["dirty_count"] = len(dirty_lines)
        if dirty_lines:
            result["state"] = "commit_needed"
            return result

        if not self.repo_obj.remotes:
            result["state"] = "no_remote"
            return result

        if not self.token or not self.current_user:
            result["state"] = "no_auth"
            return result

        local_branch = self.repo_obj.active_branch.name
        remote_branch = local_branch
        if self.selected_repo is not None:
            try:
                default_branch = self.selected_repo.default_branch
                if default_branch:
                    remote_branch = default_branch
            except Exception:
                pass
        result["remote_branch"] = remote_branch

        origin = self.repo_obj.remotes.origin
        self._ensure_auth_url(origin)
        try:
            origin.fetch()
            remote_ref = f"origin/{remote_branch}"
            ahead = list(self.repo_obj.iter_commits(f"{remote_ref}..{local_branch}"))
            behind = list(self.repo_obj.iter_commits(f"{local_branch}..{remote_ref}"))
        except GitCommandError:
            # Remote-Branch existiert vermutlich noch nicht (erster Push steht aus).
            result["state"] = "push_needed"
            result["ahead"] = 0
            return result

        result["ahead"] = len(ahead)
        result["behind"] = len(behind)

        if result["ahead"] and result["behind"]:
            result["state"] = "diverged"
        elif result["ahead"]:
            result["state"] = "push_needed"
        elif result["behind"]:
            result["state"] = "pull_needed"
        else:
            result["state"] = "up_to_date"
        return result

    def on_check_status(self):
        """Startet die Statusanalyse im Hintergrund und aktualisiert danach
        die Empfehlungsanzeige."""
        if not self.repo_obj:
            return
        self.status_bar.showMessage(tr("status_checking_repo_state"))
        self.check_status_btn.setEnabled(False)
        self.suggested_action_btn.setEnabled(False)

        self.worker = GithubWorker(self._analyze_repo_state)
        self.worker.finished.connect(self._on_check_status_finished)
        self.worker.error.connect(self._on_check_status_error)
        self.worker.start()

    def _on_check_status_finished(self, result):
        self.check_status_btn.setEnabled(True)
        self._apply_recommendation(result)
        self.status_bar.showMessage(tr("status_check_done"))

    def _on_check_status_error(self, error_msg):
        self.check_status_btn.setEnabled(True)
        self._last_state = None
        self.recommendation_label.setText(tr("recommendation_error"))
        self.suggested_action_btn.setText(tr("btn_suggested_action"))
        self.suggested_action_btn.setEnabled(False)
        self.status_bar.showMessage(tr("status_check_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_check_status_error", error=error_msg))

    def _apply_recommendation(self, result):
        """Aktualisiert Empfehlungstext und Aktionsbutton anhand des von
        _analyze_repo_state() gelieferten Zustands. Wird auch bei
        Sprachwechsel erneut aufgerufen, um die Anzeige neu zu übersetzen."""
        self._last_state = result
        state = result.get("state")

        if state == "merge_pending":
            self.recommendation_label.setText(tr("recommendation_merge_pending"))
            self.suggested_action_btn.setText(tr("action_btn_resolve_merge"))
            self.suggested_action_btn.setEnabled(True)
        elif state == "commit_needed":
            self.recommendation_label.setText(
                tr("recommendation_commit_needed", count=result.get("dirty_count", 0))
            )
            self.suggested_action_btn.setText(tr("action_btn_commit"))
            self.suggested_action_btn.setEnabled(True)
        elif state == "no_remote":
            self.recommendation_label.setText(tr("recommendation_no_remote"))
            self.suggested_action_btn.setText(tr("btn_suggested_action"))
            self.suggested_action_btn.setEnabled(False)
        elif state == "no_auth":
            self.recommendation_label.setText(tr("recommendation_no_auth"))
            self.suggested_action_btn.setText(tr("btn_suggested_action"))
            self.suggested_action_btn.setEnabled(False)
        elif state == "push_needed":
            self.recommendation_label.setText(
                tr("recommendation_push_needed", ahead=result.get("ahead", 0))
            )
            self.suggested_action_btn.setText(tr("action_btn_push"))
            self.suggested_action_btn.setEnabled(True)
        elif state == "pull_needed":
            self.recommendation_label.setText(
                tr("recommendation_pull_needed", behind=result.get("behind", 0))
            )
            self.suggested_action_btn.setText(tr("action_btn_pull"))
            self.suggested_action_btn.setEnabled(True)
        elif state == "diverged":
            self.recommendation_label.setText(
                tr("recommendation_diverged", ahead=result.get("ahead", 0), behind=result.get("behind", 0))
            )
            self.suggested_action_btn.setText(tr("action_btn_pull"))
            self.suggested_action_btn.setEnabled(True)
        elif state == "up_to_date":
            self.recommendation_label.setText(tr("recommendation_up_to_date"))
            self.suggested_action_btn.setText(tr("btn_suggested_action"))
            self.suggested_action_btn.setEnabled(False)
        else:
            self.recommendation_label.setText(tr("recommendation_none"))
            self.suggested_action_btn.setText(tr("btn_suggested_action"))
            self.suggested_action_btn.setEnabled(False)

    def on_suggested_action(self):
        """Führt die aktuell empfohlene Aktion aus. Bei 'Commit empfohlen'
        wird - falls das Textfeld noch leer ist - nur der Fokus dorthin
        gesetzt, damit der Nutzer den Commit-Text eingeben kann; ein
        erneuter Klick (oder Enter im Feld) löst dann den Commit aus."""
        state = self._last_state
        if not state:
            return
        kind = state.get("state")

        if kind == "merge_pending":
            if self._resolve_pending_merge():
                self.on_check_status()
        elif kind == "commit_needed":
            if not self.commit_msg_edit.text().strip():
                self.commit_msg_edit.setFocus()
                self.status_bar.showMessage(tr("status_enter_commit_message"))
                return
            self.on_commit()
        elif kind == "push_needed":
            self.on_push()
        elif kind in ("pull_needed", "diverged"):
            self.on_pull()
        elif kind == "no_remote":
            QMessageBox.information(
                self, tr("msg_no_remote_title"),
                tr("msg_no_remote_text", folder=self.local_repo_path or "")
            )
        elif kind == "no_auth":
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_connect_first"))
        # "up_to_date": nichts zu tun, Button ist ohnehin deaktiviert

    # ------------------------------------------------------------------
    # Commit / Push / Pull
    # ------------------------------------------------------------------
    def on_commit(self):
        if not self.repo_obj:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_no_local_repo"))
            return
        msg = self.commit_msg_edit.text().strip()
        if not msg:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_commit_msg_required"))
            return

        self.status_bar.showMessage(tr("status_commit_in_progress"))
        self.commit_btn.setEnabled(False)

        def do_commit():
            self.repo_obj.git.add(A=True)
            # Prüfen, ob nach dem Staging überhaupt etwas zu committen ist.
            # git status --porcelain ist die zuverlässigste Methode: liefert
            # für jede staged Änderung eine Zeile (A, M, D, R …).
            # GitPython-interne Methoden (index.diff, is_dirty) können im
            # Worker-Thread veraltete Objekt-Zustände zurückgeben.
            status_output = self.repo_obj.git.status(porcelain=True)
            staged_lines = [
                line for line in status_output.splitlines()
                if line and line[0] != ' ' and line[0] != '?'
            ]
            if not staged_lines:
                raise RuntimeError(tr("err_no_changes_to_commit"))
            commit = self.repo_obj.index.commit(msg)
            return commit

        self.worker = GithubWorker(do_commit)
        self.worker.finished.connect(self._on_commit_finished)
        self.worker.error.connect(self._on_commit_error)
        self.worker.start()

    def _on_commit_finished(self, commit):
        self.commit_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_commit_success", hash=commit.hexsha[:7]))
        self.commit_msg_edit.clear()
        if self.repo_obj:
            self.branch_label.setText(tr("branch_label", branch=self.repo_obj.active_branch.name))
        self.on_check_status()

    def _on_commit_error(self, error_msg):
        self.commit_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_commit_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_commit_error", error=error_msg))

    def on_push(self):
        if not self.repo_obj:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_no_local_repo"))
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_no_token_user"))
            return

        # Erst einen evtl. noch offenen Merge klären (z.B. aus einem
        # vorherigen, nicht abgeschlossenen Pull) - sonst lehnt Git jeden
        # weiteren Push/Pull mit "MERGE_HEAD exists" ab.
        if not self._resolve_pending_merge():
            self.status_bar.showMessage(tr("status_push_cancelled"))
            return

        local_branch = self.repo_obj.active_branch.name
        target_branch = local_branch  # Standard: gleicher Name auf dem Remote

        # Weicht der lokale Branch vom Standard-Branch auf GitHub ab (z.B.
        # lokal 'master', GitHub 'main'), VORHER fragen statt nur danach zu
        # warnen. So landet der Push dort, wo der Nutzer ihn auf GitHub
        # tatsächlich sehen will.
        default_branch = None
        if self.selected_repo is not None:
            try:
                default_branch = self.selected_repo.default_branch
            except Exception:
                default_branch = None

        if default_branch and local_branch != default_branch:
            box = QMessageBox(self)
            box.setIcon(QMessageBox.Icon.Question)
            box.setWindowTitle(tr("msg_branch_mismatch_title"))
            box.setText(
                tr("msg_branch_mismatch_text", local=local_branch, default=default_branch)
            )
            btn_default = box.addButton(
                tr("btn_push_to_default", branch=default_branch), QMessageBox.ButtonRole.AcceptRole
            )
            btn_same = box.addButton(
                tr("btn_push_to_local", branch=local_branch), QMessageBox.ButtonRole.ActionRole
            )
            box.addButton(tr("btn_cancel"), QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_default)
            box.exec()
            clicked = box.clickedButton()
            if clicked == btn_default:
                target_branch = default_branch
            elif clicked == btn_same:
                target_branch = local_branch
            else:
                self.status_bar.showMessage(tr("status_push_cancelled"))
                return

        self.status_bar.showMessage(tr("status_pushing"))
        self.push_btn.setEnabled(False)

        def do_push():
            origin = self.repo_obj.remotes.origin
            # URL auf korrekte authentifizierte Version setzen
            self._ensure_auth_url(origin)
            branch = self.repo_obj.active_branch
            refspec = f"{branch.name}:{target_branch}"

            # Vorab per Fetch den tatsächlichen Git-Status ermitteln, statt
            # das erst über einen abgelehnten Push herauszufinden:
            # - Gibt es lokale Commits, die der Remote-Branch noch nicht hat
            #   (sonst ist gar kein Push nötig)?
            # - Hat der Remote-Branch Commits, die lokal fehlen (dann würde
            #   der Push ohnehin abgelehnt und ein Pull ist zuerst nötig)?
            ahead = behind = None
            try:
                origin.fetch()
                remote_ref = f"origin/{target_branch}"
                ahead = list(self.repo_obj.iter_commits(f"{remote_ref}..{branch.name}"))
                behind = list(self.repo_obj.iter_commits(f"{branch.name}..{remote_ref}"))
            except GitCommandError:
                # Remote-Branch existiert vermutlich noch nicht (erster Push
                # dieses Branches) - normal fortfahren.
                pass

            if ahead is not None and not ahead:
                # Keine lokalen Commits, die übertragen werden müssten.
                return {
                    "local_branch": branch.name,
                    "remote_branch": target_branch,
                    "up_to_date": True,
                }

            if behind:
                # Remote hat Commits, die lokal fehlen - ein Push würde
                # jetzt ohnehin scheitern. Statt es zu versuchen, direkt
                # zurückmelden, dass zuerst gepullt werden muss.
                return {
                    "local_branch": branch.name,
                    "remote_branch": target_branch,
                    "needs_pull": True,
                }

            try:
                push_infos = origin.push(refspec=refspec)
            except GitCommandError as e:
                if "does not exist" in str(e) or "upstream" in str(e):
                    push_infos = origin.push(refspec=refspec, set_upstream=True)
                else:
                    raise

            # WICHTIG: GitPython wirft bei einem von GitHub abgelehnten Push
            # (z.B. non-fast-forward, Schreibschutz, falscher Branch) keine
            # Exception – der Aufruf "gelingt" technisch, ohne dass tatsächlich
            # etwas übertragen wurde. Deshalb müssen die zurückgegebenen
            # PushInfo-Objekte explizit auf Fehler-Flags geprüft werden.
            if not push_infos:
                raise RuntimeError(tr("err_push_no_feedback"))

            error_flags = (
                git.PushInfo.ERROR
                | git.PushInfo.REJECTED
                | git.PushInfo.REMOTE_REJECTED
                | git.PushInfo.REMOTE_FAILURE
            )
            error_summaries = []
            up_to_date = False
            for info in push_infos:
                if info.flags & error_flags:
                    error_summaries.append(info.summary.strip())
                if info.flags & git.PushInfo.UP_TO_DATE:
                    up_to_date = True

            if error_summaries:
                raise RuntimeError(
                    tr("err_push_rejected", summaries="\n".join(error_summaries))
                )

            return {
                "local_branch": branch.name,
                "remote_branch": target_branch,
                "up_to_date": up_to_date,
            }

        self.worker = GithubWorker(do_push)
        self.worker.finished.connect(self._on_push_finished)
        self.worker.error.connect(self._on_push_error)
        self.worker.start()

    def _on_push_finished(self, result):
        self.push_btn.setEnabled(True)
        local_branch = result.get("local_branch", "?")
        remote_branch = result.get("remote_branch", local_branch)

        if result.get("needs_pull"):
            self.status_bar.showMessage(tr("status_push_needs_pull"))
            reply = QMessageBox.question(
                self,
                tr("msg_remote_ahead_title"),
                tr("msg_remote_ahead_text", branch=remote_branch),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.on_pull()
            return

        if result.get("up_to_date"):
            self.status_bar.showMessage(
                tr("status_push_up_to_date", branch=remote_branch)
            )
            QMessageBox.information(
                self,
                tr("msg_up_to_date_title"),
                tr("msg_up_to_date_text", branch=remote_branch)
            )
        elif local_branch != remote_branch:
            self.status_bar.showMessage(
                tr("status_push_success_renamed", local=local_branch, remote=remote_branch)
            )
        else:
            self.status_bar.showMessage(tr("status_push_success", branch=remote_branch))
        self.on_check_status()

        # Nach einem tatsächlichen Push (nicht bei "bereits aktuell") anbieten,
        # gleich auch das AUR-Paket zu aktualisieren - aber nur, wenn dafür
        # ein AUR-Ordner konfiguriert ist.
        if not result.get("up_to_date") and self.aur_repo_obj:
            reply = QMessageBox.question(
                self,
                tr("msg_aur_after_push_title"),
                tr("msg_aur_after_push_text"),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.tabs.setCurrentWidget(self.aur_tab_widget)

    def _on_push_error(self, error_msg):
        self.push_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_push_failed"))
        if "non-fast-forward" in error_msg or "rejected" in error_msg.lower():
            reply = QMessageBox.critical(
                self,
                tr("msg_error_title"),
                tr("msg_push_error_pull_question", error=error_msg),
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.on_pull()
        else:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_push_error", error=error_msg))

    def on_pull(self):
        if not self.repo_obj:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_no_local_repo"))
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_no_token_user"))
            return

        # Erst einen evtl. noch offenen Merge klären (z.B. aus einem
        # vorherigen, nicht abgeschlossenen Pull) - sonst lehnt Git jeden
        # weiteren Pull mit "MERGE_HEAD exists" ab.
        if not self._resolve_pending_merge():
            self.status_bar.showMessage(tr("status_pull_cancelled"))
            return

        self.status_bar.showMessage(tr("status_pulling"))
        self.pull_btn.setEnabled(False)

        def do_pull():
            origin = self.repo_obj.remotes.origin
            self._ensure_auth_url(origin)
            local_branch = self.repo_obj.active_branch.name

            # Remote-Branch ermitteln: bevorzugt den Standard-Branch des
            # ausgewählten GitHub-Repositories (passend zur Push-Logik), da
            # dort die eigentlich relevanten Commits liegen, auch wenn der
            # lokale Branch anders heißt (z.B. 'master' vs. 'main').
            remote_branch = local_branch
            if self.selected_repo is not None:
                try:
                    default_branch = self.selected_repo.default_branch
                    if default_branch:
                        remote_branch = default_branch
                except Exception:
                    pass

            origin.fetch()

            try:
                # Explizit --no-rebase übergeben, damit Git 2.27+ nicht mit
                # "Need to specify how to reconcile divergent branches" abbricht.
                # Merge ist die sichere Standardstrategie für GUI-Nutzer.
                self.repo_obj.git.pull(
                    "origin", remote_branch, no_rebase=True
                )
            except GitCommandError as e:
                msg = str(e)
                if "unrelated histories" in msg.lower() or "refusing to merge" in msg.lower():
                    # Tritt typischerweise auf, wenn ein lokal frisch initialisiertes
                    # Repository mit einem bereits befüllten GitHub-Repository
                    # verknüpft wurde (z.B. README über die Weboberfläche erstellt).
                    try:
                        self.repo_obj.git.pull(
                            "origin", remote_branch,
                            allow_unrelated_histories=True, no_rebase=True
                        )
                    except GitCommandError as e2:
                        if "conflict" in str(e2).lower():
                            raise RuntimeError(tr("err_merge_conflict_unrelated"))
                        raise RuntimeError(tr("err_pull_failed", error=e2))
                elif "conflict" in msg.lower():
                    raise RuntimeError(tr("err_merge_conflict"))
                else:
                    raise

            return remote_branch

        self.worker = GithubWorker(do_pull)
        self.worker.finished.connect(self._on_pull_finished)
        self.worker.error.connect(self._on_pull_error)
        self.worker.start()

    def _on_pull_finished(self, remote_branch):
        self.pull_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_pull_success", branch=remote_branch))
        if self.repo_obj:
            self.branch_label.setText(tr("branch_label", branch=self.repo_obj.active_branch.name))
        self.on_check_status()

    def _on_pull_error(self, error_msg):
        self.pull_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_pull_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_pull_error", error=error_msg))

    # ------------------------------------------------------------------
    # AUR-Tab: PKGBUILD-Version/Checksums aktualisieren und zum AUR pushen
    # ------------------------------------------------------------------
    def _parse_pkgbuild(self, text):
        """Liest pkgname/pkgver/pkgrel aus einer PKGBUILD-Textdatei aus.
        Deckt den Regelfall skalarer Werte ab; Bash-Arrays (z.B. bei
        Split-Packages) werden nicht unterstützt."""
        pkgname_m = PKGNAME_RE.search(text)
        pkgver_m = PKGVER_RE.search(text)
        pkgrel_m = PKGREL_RE.search(text)
        pkgname = pkgname_m.group(1).strip() if pkgname_m else "?"
        pkgver = pkgver_m.group(1).strip() if pkgver_m else "?"
        pkgrel = pkgrel_m.group(1).strip() if pkgrel_m else "?"
        return pkgname, pkgver, pkgrel

    def _bump_pkgbuild(self, text, new_version):
        """Setzt pkgver auf new_version. Ist die Version unverändert (reiner
        Rebuild ohne neue Upstream-Version), wird stattdessen nur pkgrel um
        1 erhöht - das ist auf dem AUR die übliche Konvention. Gibt den
        neuen PKGBUILD-Text sowie den verwendeten pkgrel-Wert zurück."""
        old_pkgver_m = PKGVER_RE.search(text)
        old_pkgver = old_pkgver_m.group(1).strip() if old_pkgver_m else None

        if old_pkgver == new_version:
            old_pkgrel_m = PKGREL_RE.search(text)
            old_rel = old_pkgrel_m.group(1).strip() if old_pkgrel_m else "1"
            try:
                new_rel = str(int(old_rel) + 1)
            except ValueError:
                new_rel = "1"
        else:
            new_rel = "1"

        text = PKGVER_RE.sub(f"pkgver={new_version}", text, count=1)
        text = PKGREL_RE.sub(f"pkgrel={new_rel}", text, count=1)
        return text, new_rel

    def _load_aur_repo(self, folder, show_errors=True):
        """Lädt einen lokal bereits geklonten AUR-Ordner (z.B. von
        ssh://aur@aur.archlinux.org/<paket>.git). show_errors=False
        unterdrückt Fehlerdialoge (z.B. beim stillen Laden aus den
        gespeicherten Einstellungen beim Programmstart)."""
        pkgbuild_path = os.path.join(folder, "PKGBUILD")
        if not os.path.isfile(pkgbuild_path):
            if show_errors:
                QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_no_pkgbuild", folder=folder))
            return False

        try:
            repo = Repo(folder)
        except InvalidGitRepositoryError:
            if show_errors:
                QMessageBox.critical(self, tr("msg_no_git_repo_title"), tr("msg_no_git_repo_text", folder=folder))
            return False
        except Exception as e:
            if show_errors:
                QMessageBox.critical(self, tr("msg_error_title"), tr("msg_load_error", error=e))
            return False

        try:
            with open(pkgbuild_path, "r", encoding="utf-8") as f:
                text = f.read()
            pkgname, pkgver, pkgrel = self._parse_pkgbuild(text)
        except Exception as e:
            if show_errors:
                QMessageBox.critical(self, tr("msg_error_title"), tr("msg_load_error", error=e))
            return False

        self.aur_folder = folder
        self.aur_repo_obj = repo
        self.aur_folder_edit.setText(folder)
        self.aur_info_label.setText(tr("aur_info", pkgname=pkgname, version=pkgver, rel=pkgrel))
        self.aur_version_edit.setText(pkgver)
        self.aur_update_btn.setEnabled(True)
        self.aur_commit_push_btn.setEnabled(False)
        self.aur_check_status_btn.setEnabled(True)
        self.aur_version_updated = False
        self._update_aur_step_indicator()
        self.status_bar.showMessage(tr("status_aur_folder_loaded", folder=folder))
        self.on_aur_check_status()
        return True

    def on_new_aur_package(self, prefill_repo=None):
        """Dünner Wrapper um _on_new_aur_package_impl(): fängt jede dort
        unerwartet auftretende Exception ab. Der eigentliche Ablauf läuft
        teils synchron im GUI-Thread (Ordnerauswahl, GitHub-Attributzugriffe),
        also außerhalb des try/except in GithubWorker.run(). PyQt6 fängt
        (anders als PyQt5) eine unbehandelte Exception aus einem Slot nicht
        mehr ab, sondern beendet den ganzen Prozess - dieses try/except
        verhindert genau diesen Absturz und zeigt stattdessen einen
        Fehlerdialog."""
        try:
            self._on_new_aur_package_impl(prefill_repo=prefill_repo)
        except Exception as e:
            self.aur_new_package_btn.setEnabled(True)
            QMessageBox.critical(
                self, tr("msg_error_title"),
                tr("msg_aur_package_create_error", error=f"{e}\n\n{traceback.format_exc()}")
            )

    def _on_new_aur_package_impl(self, prefill_repo=None):
        """Legt ein neues AUR-Paket (PKGBUILD-Grundgerüst) für ein
        GitHub-Repository an: Ordner erstellen, PKGBUILD schreiben,
        lokales Git-Repo initialisieren und den AUR-Remote setzen. Danach
        lädt es die App wie einen normal ausgewählten AUR-Ordner.

        Fragt bei jedem Aufruf sowohl den Speicherort als auch den
        Ordnernamen ab (statt den Basisordner nur beim ersten Mal zu
        erfragen und den Ordnernamen automatisch vom Paketnamen
        abzuleiten)."""
        suggested_pkgname = ""
        suggested_url = ""
        suggested_desc = ""
        if prefill_repo is not None and hasattr(prefill_repo, "name"):
            suggested_pkgname = re.sub(r'[^a-z0-9@._+-]', '-', prefill_repo.name.lower())
            suggested_url = prefill_repo.html_url or ""
            suggested_desc = (prefill_repo.description or "").strip()
        elif self.selected_repo is not None and hasattr(self.selected_repo, "name"):
            suggested_pkgname = re.sub(r'[^a-z0-9@._+-]', '-', self.selected_repo.name.lower())
            suggested_url = self.selected_repo.html_url or ""
            suggested_desc = (self.selected_repo.description or "").strip()

        start_dir = self.aur_default_folder if self.aur_default_folder else os.path.expanduser("~")
        location = QFileDialog.getExistingDirectory(
            self, tr("dlg_choose_aur_location"),
            start_dir, QFileDialog.Option.ShowDirsOnly
        )
        if not location:
            return

        folder_name, ok = QInputDialog.getText(
            self, tr("dlg_aur_folder_name_title"), tr("dlg_aur_folder_name_label"),
            text=suggested_pkgname
        )
        if not ok:
            return
        folder_name = folder_name.strip()
        if not folder_name or os.sep in folder_name or folder_name in (".", ".."):
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_foldername_invalid"))
            return

        folder = os.path.join(location, folder_name)
        if os.path.exists(folder):
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_folder_exists", folder=folder))
            return

        # Speicherort merken, damit der Dateidialog beim naechsten Mal dort
        # startet - abgefragt wird er trotzdem jedes Mal aufs Neue.
        self.aur_default_folder = location
        settings = load_settings()
        settings['aur_default_folder'] = location
        save_settings(settings)

        if not suggested_pkgname:
            suggested_pkgname = re.sub(r'[^a-z0-9@._+-]', '-', folder_name.lower())

        dialog = NewAurPackageDialog(
            self, suggested_pkgname=suggested_pkgname,
            suggested_url=suggested_url, suggested_desc=suggested_desc
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        data = dialog.get_package_data()
        if not data["pkgname"] or not AUR_PKGNAME_RE.match(data["pkgname"]):
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_pkgname_invalid"))
            return
        if not data["pkgver"] or re.search(r'\s', data["pkgver"]):
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_version_invalid"))
            return
        if not data["url"]:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_url_required"))
            return

        data["folder"] = folder
        try:
            # self.current_user.name loest bei PyGithub bei Bedarf einen
            # synchronen API-Aufruf aus (lazy loading). Das laeuft hier
            # noch im GUI-Thread, also ausserhalb des try/except in
            # GithubWorker.run() - ein Netzwerkfehler/Timeout in genau
            # diesem Moment wuerde sonst als unbehandelte Exception aus
            # diesem Slot fliegen. Anders als PyQt5 faengt PyQt6 das nicht
            # ab und beendet stattdessen den ganzen Prozess (Absturz statt
            # Fehlerdialog). Maintainer-Zeile bleibt im Fehlerfall leer,
            # das Anlegen des Pakets soll daran nicht scheitern.
            data["maintainer"] = f"{self.current_user.name or self.current_user.login} <>" if self.current_user else ""
        except Exception:
            data["maintainer"] = ""

        self.status_bar.showMessage(tr("status_aur_creating_package", pkgname=data["pkgname"]))
        self.aur_new_package_btn.setEnabled(False)
        self.aur_worker = GithubWorker(self._create_new_aur_package, data)
        self.aur_worker.finished.connect(self._on_new_aur_package_finished)
        self.aur_worker.error.connect(self._on_new_aur_package_error)
        self.aur_worker.start()

    def _create_new_aur_package(self, data):
        os.makedirs(data["folder"])
        pkgbuild_path = os.path.join(data["folder"], "PKGBUILD")
        with open(pkgbuild_path, "w", encoding="utf-8") as f:
            f.write(build_pkgbuild_template(data))

        repo = Repo.init(data["folder"])
        repo.create_remote("origin", f"ssh://aur@aur.archlinux.org/{data['pkgname']}.git")
        return data

    def _on_new_aur_package_finished(self, data):
        self.aur_new_package_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_aur_package_created", pkgname=data["pkgname"]))
        self.tabs.setCurrentWidget(self.aur_tab_widget)
        self._load_aur_repo(data["folder"])
        QMessageBox.information(
            self, tr("msg_aur_package_created_title"),
            tr("msg_aur_package_created_text", pkgname=data["pkgname"], version=data["pkgver"])
        )

    def _on_new_aur_package_error(self, error_msg):
        self.aur_new_package_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_aur_creating_package_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_package_create_error", error=error_msg))

    def on_aur_browse_folder(self):
        start_dir = self.aur_default_folder if self.aur_default_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self,
            tr("dlg_choose_aur_folder"),
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if not folder:
            return
        if self._load_aur_repo(folder):
            self.aur_default_folder = folder
            settings = load_settings()
            settings['aur_default_folder'] = folder
            save_settings(settings)

    def on_aur_update_version(self):
        """Setzt die neue Version in der PKGBUILD, aktualisiert per
        'updpkgsums' die Prüfsummen (lädt dafür die Quellen herunter) und
        erzeugt die .SRCINFO neu (per 'makepkg --printsrcinfo'). Läuft im
        Hintergrund, da sowohl der Download als auch makepkg blockieren."""
        if not self.aur_repo_obj:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_no_folder"))
            return
        new_version = self.aur_version_edit.text().strip()
        if not new_version:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_version_required"))
            return
        if re.search(r'\s', new_version):
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_version_invalid"))
            return

        self.status_bar.showMessage(tr("status_aur_updating"))
        self.aur_update_btn.setEnabled(False)
        self.aur_commit_push_btn.setEnabled(False)

        folder = self.aur_folder

        def do_update():
            pkgbuild_path = os.path.join(folder, "PKGBUILD")
            with open(pkgbuild_path, "r", encoding="utf-8") as f:
                text = f.read()
            pkgname, old_version, _ = self._parse_pkgbuild(text)
            new_text, new_rel = self._bump_pkgbuild(text, new_version)
            with open(pkgbuild_path, "w", encoding="utf-8") as f:
                f.write(new_text)

            # Prüfsummen neu ermitteln: lädt die in 'source=' referenzierten
            # Dateien herunter und schreibt sha256sums/b2sums direkt in die
            # PKGBUILD - Standardwerkzeug aus 'pacman-contrib'.
            try:
                subprocess.run(
                    ["updpkgsums"], cwd=folder, check=True,
                    capture_output=True, text=True
                )
            except FileNotFoundError:
                raise RuntimeError(tr("err_aur_updpkgsums_missing"))
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    tr("err_aur_updpkgsums_failed", error=(e.stderr or e.stdout or str(e)).strip())
                )

            # .SRCINFO aus der aktualisierten PKGBUILD neu generieren
            try:
                result = subprocess.run(
                    ["makepkg", "--printsrcinfo"], cwd=folder, check=True,
                    capture_output=True, text=True
                )
            except FileNotFoundError:
                raise RuntimeError(tr("err_aur_makepkg_missing"))
            except subprocess.CalledProcessError as e:
                raise RuntimeError(
                    tr("err_aur_makepkg_failed", error=(e.stderr or e.stdout or str(e)).strip())
                )

            with open(os.path.join(folder, ".SRCINFO"), "w", encoding="utf-8") as f:
                f.write(result.stdout)

            return {
                "pkgname": pkgname,
                "old_version": old_version,
                "new_version": new_version,
                "pkgrel": new_rel,
            }

        self.aur_worker = GithubWorker(do_update)
        self.aur_worker.finished.connect(self._on_aur_update_finished)
        self.aur_worker.error.connect(self._on_aur_update_error)
        self.aur_worker.start()

    def _on_aur_update_finished(self, result):
        self.aur_update_btn.setEnabled(True)
        new_version = result["new_version"]
        self.aur_info_label.setText(
            tr("aur_info", pkgname=result["pkgname"], version=new_version, rel=result["pkgrel"])
        )
        self.aur_commit_msg_edit.setText(tr("aur_commit_msg_default", version=new_version))
        self.aur_commit_push_btn.setEnabled(True)
        self.aur_version_updated = True
        self._update_aur_step_indicator()
        self.status_bar.showMessage(tr("status_aur_update_done", version=new_version))
        self.on_aur_check_status()

    def _on_aur_update_error(self, error_msg):
        self.aur_update_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_aur_update_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_update_error", error=error_msg))

    def on_aur_commit_push(self):
        if not self.aur_repo_obj:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_aur_no_folder"))
            return
        msg = self.aur_commit_msg_edit.text().strip()
        if not msg:
            QMessageBox.warning(self, tr("msg_error_title"), tr("msg_commit_msg_required"))
            return
        if not self._guard_aur_push_order():
            return

        self.status_bar.showMessage(tr("status_aur_pushing"))
        self.aur_commit_push_btn.setEnabled(False)
        self.aur_check_status_btn.setEnabled(False)
        self.aur_suggested_action_btn.setEnabled(False)

        repo = self.aur_repo_obj

        def do_commit_push():
            # Bewusst nur diese beiden Dateien staged, statt 'add(A=True)':
            # ein AUR-Arbeitsordner enthält nach 'makepkg' häufig zusätzlich
            # Build-Artefakte (pkg/, src/, *.pkg.tar.zst), die keinesfalls
            # ins AUR-Git-Repo gehören.
            repo.git.add(["PKGBUILD", ".SRCINFO"])
            status_output = repo.git.status(porcelain=True)
            staged_lines = [
                line for line in status_output.splitlines()
                if line and line[0] != ' ' and line[0] != '?'
            ]
            if not staged_lines:
                raise RuntimeError(tr("err_no_changes_to_commit"))

            repo.index.commit(msg)

            if not repo.remotes:
                raise RuntimeError(tr("err_aur_no_remote"))

            origin = repo.remotes.origin
            push_infos = origin.push()
            if not push_infos:
                raise RuntimeError(tr("err_push_no_feedback"))

            error_flags = (
                git.PushInfo.ERROR
                | git.PushInfo.REJECTED
                | git.PushInfo.REMOTE_REJECTED
                | git.PushInfo.REMOTE_FAILURE
            )
            error_summaries = [
                info.summary.strip() for info in push_infos if info.flags & error_flags
            ]
            if error_summaries:
                raise RuntimeError(tr("err_push_rejected", summaries="\n".join(error_summaries)))
            return True

        self.aur_worker = GithubWorker(do_commit_push)
        self.aur_worker.finished.connect(self._on_aur_push_finished)
        self.aur_worker.error.connect(self._on_aur_push_error)
        self.aur_worker.start()

    def _on_aur_push_finished(self, _result):
        self.aur_commit_push_btn.setEnabled(True)
        self.aur_commit_msg_edit.clear()
        # Durchlauf abgeschlossen - für den nächsten Release wieder eine
        # frische Versionsaktualisierung verlangen (siehe _guard_aur_push_order()).
        self.aur_version_updated = False
        self._update_aur_step_indicator()
        self.status_bar.showMessage(tr("status_aur_push_success"))
        QMessageBox.information(self, tr("msg_aur_push_success_title"), tr("msg_aur_push_success_text"))
        self.on_aur_check_status()

    def _on_aur_push_error(self, error_msg):
        self.aur_commit_push_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_aur_push_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_push_error", error=error_msg))
        self.on_aur_check_status()

    # ------------------------------------------------------------------
    # AUR-Tab: Status-Analyse und Aktionsempfehlung (analog zum GitHub-Tab)
    # ------------------------------------------------------------------
    def _is_aur_build_artifact(self, path):
        """True, wenn 'path' (aus 'git status --porcelain', unversioniert)
        typischerweise von makepkg/updpkgsums erzeugt wird und NICHT ins
        AUR-Git-Repo gehört (Quell-Tarball, Build-/Paketverzeichnis, etc.)."""
        name = path.rstrip('/')
        base = os.path.basename(name)
        if base in AUR_BUILD_ARTIFACT_DIRS:
            return True
        return any(fnmatch.fnmatch(base, pattern) for pattern in AUR_BUILD_ARTIFACT_PATTERNS)

    def _analyze_aur_state(self):
        """Ermittelt den Zustand des geladenen AUR-Repositories - analog zu
        _analyze_repo_state() für den GitHub-Tab, aber ohne PyGithub-Bezug
        (kein Personal-Access-Token nötig, da AUR-Zugriff über SSH läuft).

        Wichtiger Unterschied zum GitHub-Tab: 'git status' im AUR-Ordner
        zeigt nach 'updpkgsums'/makepkg häufig unversionierte Build-
        Artefakte (heruntergeladene Quell-Tarballs, pkg/, src/), die
        keinesfalls committet werden sollen. Diese werden hier getrennt von
        echten Änderungen (PKGBUILD/.SRCINFO) und von tatsächlich neuen,
        zu versionierenden Dateien behandelt."""
        result = {
            "state": "unknown", "dirty_count": 0, "ahead": 0, "behind": 0,
            "new_files": [], "artifacts": [],
        }
        repo = self.aur_repo_obj

        if self._merge_in_progress(repo):
            result["state"] = "merge_pending"
            return result

        status_output = repo.git.status(porcelain=True)
        lines = [line for line in status_output.splitlines() if line.strip()]

        tracked_changes = []   # bereits versionierte Dateien: modifiziert/staged/gelöscht/umbenannt
        new_relevant = []      # unversionierte Dateien, die vermutlich versioniert werden sollen
        artifacts = []         # unversionierte Build-Artefakte (Tarballs, pkg/, src/, ...)

        for line in lines:
            code = line[:2]
            path = line[3:].strip().strip('"')
            if code == "??":
                if self._is_aur_build_artifact(path):
                    artifacts.append(path)
                else:
                    new_relevant.append(path)
            else:
                tracked_changes.append(path)

        result["dirty_count"] = len(tracked_changes)
        result["new_files"] = new_relevant
        result["artifacts"] = artifacts

        if tracked_changes:
            result["state"] = "commit_needed"
            return result

        if new_relevant:
            result["state"] = "new_files_to_add"
            return result

        if artifacts:
            result["state"] = "build_artifacts_found"
            return result

        if not repo.remotes:
            result["state"] = "no_remote"
            return result

        local_branch = repo.active_branch.name
        origin = repo.remotes.origin
        try:
            origin.fetch()
            remote_ref = f"origin/{local_branch}"
            ahead = list(repo.iter_commits(f"{remote_ref}..{local_branch}"))
            behind = list(repo.iter_commits(f"{local_branch}..{remote_ref}"))
        except GitCommandError:
            # Remote-Branch existiert vermutlich noch nicht (erster Push steht aus).
            result["state"] = "push_needed"
            return result

        result["ahead"] = len(ahead)
        result["behind"] = len(behind)
        if result["ahead"] and result["behind"]:
            result["state"] = "diverged"
        elif result["ahead"]:
            result["state"] = "push_needed"
        elif result["behind"]:
            result["state"] = "pull_needed"
        else:
            result["state"] = "up_to_date"
        return result

    def on_aur_check_status(self):
        if not self.aur_repo_obj:
            return
        self.status_bar.showMessage(tr("status_aur_checking_repo_state"))
        self.aur_check_status_btn.setEnabled(False)
        self.aur_suggested_action_btn.setEnabled(False)

        self.aur_worker = GithubWorker(self._analyze_aur_state)
        self.aur_worker.finished.connect(self._on_aur_check_status_finished)
        self.aur_worker.error.connect(self._on_aur_check_status_error)
        self.aur_worker.start()

    def _on_aur_check_status_finished(self, result):
        self.aur_check_status_btn.setEnabled(True)
        self._apply_aur_recommendation(result)
        self.status_bar.showMessage(tr("status_aur_check_done"))

    def _on_aur_check_status_error(self, error_msg):
        self.aur_check_status_btn.setEnabled(True)
        self._aur_last_state = None
        self.aur_recommendation_label.setText(tr("aur_recommendation_error"))
        self.aur_suggested_action_btn.setText(tr("btn_aur_suggested_action"))
        self.aur_suggested_action_btn.setEnabled(False)
        self.status_bar.showMessage(tr("status_aur_check_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_check_status_error", error=error_msg))

    def _apply_aur_recommendation(self, result):
        self._aur_last_state = result
        state = result.get("state")

        if state == "merge_pending":
            self.aur_recommendation_label.setText(tr("aur_recommendation_merge_pending"))
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_resolve_merge"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "commit_needed":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_commit_needed", count=result.get("dirty_count", 0))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_commit"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "new_files_to_add":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_new_files", count=len(result.get("new_files", [])))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_add_files"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "build_artifacts_found":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_artifacts_found", count=len(result.get("artifacts", [])))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_cleanup"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "no_remote":
            self.aur_recommendation_label.setText(tr("aur_recommendation_no_remote"))
            self.aur_suggested_action_btn.setText(tr("btn_aur_suggested_action"))
            self.aur_suggested_action_btn.setEnabled(False)
        elif state == "push_needed":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_push_needed", ahead=result.get("ahead", 0))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_push"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "pull_needed":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_pull_needed", behind=result.get("behind", 0))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_pull"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "diverged":
            self.aur_recommendation_label.setText(
                tr("aur_recommendation_diverged", ahead=result.get("ahead", 0), behind=result.get("behind", 0))
            )
            self.aur_suggested_action_btn.setText(tr("aur_action_btn_pull"))
            self.aur_suggested_action_btn.setEnabled(True)
        elif state == "up_to_date":
            self.aur_recommendation_label.setText(tr("aur_recommendation_up_to_date"))
            self.aur_suggested_action_btn.setText(tr("btn_aur_suggested_action"))
            self.aur_suggested_action_btn.setEnabled(False)
        else:
            self.aur_recommendation_label.setText(tr("aur_recommendation_none"))
            self.aur_suggested_action_btn.setText(tr("btn_aur_suggested_action"))
            self.aur_suggested_action_btn.setEnabled(False)

    def _update_aur_step_indicator(self):
        """Aktualisiert den sichtbaren Hinweis, ob 'Version aktualisieren'
        in diesem Durchlauf schon gelaufen ist. Rein informativ - die
        eigentliche Sperre sitzt in _guard_aur_push_order()."""
        if not self.aur_repo_obj:
            self.aur_step_indicator_label.setText("")
            return
        if self.aur_version_updated:
            self.aur_step_indicator_label.setText(tr("aur_step_indicator_done"))
        else:
            self.aur_step_indicator_label.setText(tr("aur_step_indicator_pending"))

    def _guard_aur_push_order(self):
        """Reihenfolge-Sperre für den AUR-Tab: fragt nach, bevor committet
        oder gepusht wird, ohne dass in diesem Durchlauf zuvor 'Version
        aktualisieren' gelaufen ist. Verhindert das versehentliche
        Vertauschen der Reihenfolge (z.B. erst pushen/committen und die
        Versionsnummer erst danach hochzusetzen).

        Gibt True zurück, wenn fortgefahren werden darf (Version wurde
        aktualisiert, oder der Nutzer bestätigt den bewussten Verzicht
        darauf - z.B. für einen reinen PKGBUILD-Fix ohne Versionswechsel).
        """
        if self.aur_version_updated:
            return True
        reply = QMessageBox.question(
            self,
            tr("msg_aur_order_warning_title"),
            tr("msg_aur_order_warning_text"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        return reply == QMessageBox.StandardButton.Yes

    def on_aur_suggested_action(self):
        state = self._aur_last_state
        if not state:
            return
        kind = state.get("state")

        if kind == "merge_pending":
            if self._resolve_pending_merge(self.aur_repo_obj):
                self.on_aur_check_status()
        elif kind == "commit_needed":
            if not self.aur_commit_msg_edit.text().strip():
                self.aur_commit_msg_edit.setFocus()
                self.status_bar.showMessage(tr("status_enter_commit_message"))
                return
            self.on_aur_commit_push()
        elif kind == "new_files_to_add":
            self._aur_add_new_files()
        elif kind == "build_artifacts_found":
            self._aur_cleanup_artifacts()
        elif kind == "push_needed":
            self.on_aur_push_only()
        elif kind in ("pull_needed", "diverged"):
            self.on_aur_pull()
        elif kind == "no_remote":
            QMessageBox.warning(self, tr("msg_error_title"), tr("err_aur_no_remote"))
        # "up_to_date": nichts zu tun, Button ist ohnehin deaktiviert

    def on_aur_push_only(self):
        """Pusht bereits vorhandene lokale Commits, ohne vorher etwas zu
        committen (Empfehlung 'push_needed': es gibt nichts Neues zu
        staged, nur der Push zum AUR steht noch aus)."""
        if not self.aur_repo_obj:
            return
        if not self._guard_aur_push_order():
            return
        self.status_bar.showMessage(tr("status_aur_pushing"))
        self.aur_commit_push_btn.setEnabled(False)
        self.aur_check_status_btn.setEnabled(False)
        self.aur_suggested_action_btn.setEnabled(False)

        repo = self.aur_repo_obj

        def do_push():
            if not repo.remotes:
                raise RuntimeError(tr("err_aur_no_remote"))
            origin = repo.remotes.origin
            push_infos = origin.push()
            if not push_infos:
                raise RuntimeError(tr("err_push_no_feedback"))
            error_flags = (
                git.PushInfo.ERROR
                | git.PushInfo.REJECTED
                | git.PushInfo.REMOTE_REJECTED
                | git.PushInfo.REMOTE_FAILURE
            )
            error_summaries = [
                info.summary.strip() for info in push_infos if info.flags & error_flags
            ]
            if error_summaries:
                raise RuntimeError(tr("err_push_rejected", summaries="\n".join(error_summaries)))
            return True

        self.aur_worker = GithubWorker(do_push)
        self.aur_worker.finished.connect(self._on_aur_push_finished)
        self.aur_worker.error.connect(self._on_aur_push_error)
        self.aur_worker.start()

    def on_aur_pull(self):
        """Holt Änderungen vom AUR-Remote (z.B. Edits eines Co-Maintainers).
        Prüft vorher auf einen offenen Merge, wie beim GitHub-Pull."""
        if not self.aur_repo_obj:
            return
        if not self._resolve_pending_merge(self.aur_repo_obj):
            return

        self.status_bar.showMessage(tr("status_aur_pulling"))
        self.aur_check_status_btn.setEnabled(False)
        self.aur_suggested_action_btn.setEnabled(False)

        repo = self.aur_repo_obj

        def do_pull():
            origin = repo.remotes.origin
            origin.pull()
            return True

        self.aur_worker = GithubWorker(do_pull)
        self.aur_worker.finished.connect(self._on_aur_pull_finished)
        self.aur_worker.error.connect(self._on_aur_pull_error)
        self.aur_worker.start()

    def _on_aur_pull_finished(self, _result):
        self.status_bar.showMessage(tr("status_aur_pull_success"))
        # PKGBUILD könnte sich durch den Pull geändert haben (z.B. neue
        # Version durch einen Co-Maintainer) - Anzeige neu laden.
        self._load_aur_repo(self.aur_folder, show_errors=False)

    def _on_aur_pull_error(self, error_msg):
        self.status_bar.showMessage(tr("status_aur_pull_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_pull_error", error=error_msg))
        self.on_aur_check_status()

    def _aur_add_new_files(self):
        """Versioniert neu gefundene, relevante Dateien (z.B. eine neue
        .install-Datei oder ein Patch), die noch nicht Teil des Git-Repos
        sind. Build-Artefakte werden hier nie einbezogen - die Erkennung
        erfolgt bereits in _analyze_aur_state(). Nach dem 'git add' zeigt
        die nächste Statusprüfung automatisch 'Commit empfohlen'."""
        state = self._aur_last_state
        if not state:
            return
        new_files = state.get("new_files", [])
        if not new_files:
            return

        file_list = "\n".join(f"• {f}" for f in new_files)
        reply = QMessageBox.question(
            self,
            tr("msg_aur_add_files_title"),
            tr("msg_aur_add_files_text", files=file_list),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        try:
            self.aur_repo_obj.git.add(new_files)
        except GitCommandError as e:
            QMessageBox.critical(self, tr("msg_error_title"), tr("msg_aur_add_files_error", error=e))
            return

        self.status_bar.showMessage(tr("status_aur_files_added"))
        self.on_aur_check_status()

    def _aur_cleanup_artifacts(self):
        """Löscht unversionierte Build-Artefakte (z.B. das von updpkgsums
        heruntergeladene Quell-Tarball, pkg/- oder src/-Ordner) aus dem
        AUR-Ordner. Diese Dateien gehören nicht ins Git-Repo und würden
        sonst dauerhaft als 'Commit empfohlen' angezeigt."""
        state = self._aur_last_state
        if not state:
            return
        artifacts = state.get("artifacts", [])
        if not artifacts:
            return

        file_list = "\n".join(f"• {f}" for f in artifacts)
        reply = QMessageBox.question(
            self,
            tr("msg_aur_cleanup_title"),
            tr("msg_aur_cleanup_text", files=file_list),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.Yes
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        errors = []
        for rel_path in artifacts:
            full_path = os.path.join(self.aur_folder, rel_path.rstrip('/'))
            try:
                if os.path.islink(full_path) or os.path.isfile(full_path):
                    os.remove(full_path)
                elif os.path.isdir(full_path):
                    shutil.rmtree(full_path)
            except OSError as e:
                errors.append(f"{rel_path}: {e}")

        if errors:
            QMessageBox.warning(
                self, tr("msg_error_title"),
                tr("msg_aur_cleanup_partial_error", errors="\n".join(errors))
            )
        else:
            self.status_bar.showMessage(tr("status_aur_cleanup_done"))
        self.on_aur_check_status()


# ----------------------------------------------------------------------
# 5. Start
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
