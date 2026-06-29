#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub Repository Manager
Mit korrekter Remote-URL-Behandlung: Entfernt doppelte Token.
Mit Push-Ergebnis-Prüfung: Erkennt von GitHub abgelehnte oder
folgenlose Pushes, statt fälschlich "Erfolg" zu melden.
"""

import sys
import subprocess
import os
import json
import time
import datetime
import webbrowser
import re

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
        print(f"\nVersuche Installation mit Systempaketmanager: {' '.join(system_cmd)}")
        try:
            subprocess.check_call(system_cmd)
            print("Systeminstallation erfolgreich.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("Systeminstallation fehlgeschlagen. Versuche jetzt pip --user...")
    else:
        print("Kein Systempaketmanager erkannt. Verwende pip --user.")

    print(f"\nFühre aus: {' '.join(pip_cmd)}")
    try:
        subprocess.check_call(pip_cmd)
        print("pip-Installation erfolgreich.")
        return True
    except subprocess.CalledProcessError:
        print("pip-Installation fehlgeschlagen.")
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
    print("  FEHLENDE ABHÄNGIGKEITEN")
    print("="*60)
    print(f"Folgende Module werden benötigt, sind aber nicht installiert: {', '.join(missing)}")
    distro = detect_distro()
    print(f"Erkannte Distribution: {distro}")

    answer = input("\nMöchtest du die fehlenden Pakete automatisch installieren lassen? (j/N): ").strip().lower()
    if answer not in ('j', 'ja', 'y', 'yes'):
        print("Installation abgelehnt. Bitte installiere die Pakete manuell und starte das Skript neu.")
        sys.exit(1)

    success = install_packages(distro, missing)
    if success:
        print("\nInstallation abgeschlossen. Starte das Skript neu...")
        time.sleep(1)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        print("\nInstallation fehlgeschlagen. Bitte installiere die Pakete manuell und starte das Skript neu.")
        sys.exit(1)

check_and_install_dependencies()

# ----------------------------------------------------------------------
# 2. Module importieren
# ----------------------------------------------------------------------
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QMessageBox, QDialog, QDialogButtonBox, QFormLayout, QTextEdit,
    QCheckBox, QStatusBar, QGroupBox, QFileDialog, QInputDialog
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
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

# Settings für Standardordner
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
        self.setWindowTitle("Neues Repository erstellen")
        self.setModal(True)
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("Repository-Name")
        form.addRow("Name:", self.name_edit)
        self.desc_edit = QTextEdit()
        self.desc_edit.setPlaceholderText("Beschreibung (optional)")
        self.desc_edit.setMaximumHeight(100)
        form.addRow("Beschreibung:", self.desc_edit)
        self.private_check = QCheckBox("Privat")
        form.addRow("Sichtbarkeit:", self.private_check)
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
            self.error.emit(str(e))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GitHub Repository Manager 1.06")
        self.setMinimumSize(650, 650)

        self.github = None
        self.current_user = None
        self.repos = []
        self.selected_repo = None

        self.local_repo_path = None
        self.repo_obj = None
        self.default_folder = None
        self.token = None

        self.init_ui()
        self.load_saved_credentials()
        self.load_settings()
        self.status_bar.showMessage("Bereit")

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
        main_layout = QVBoxLayout(central)

        # ---------- Login ----------
        login_group = QGroupBox("GitHub Login")
        login_layout = QVBoxLayout(login_group)

        user_layout = QHBoxLayout()
        user_layout.addWidget(QLabel("Benutzername:"))
        self.user_edit = QLineEdit()
        self.user_edit.setPlaceholderText("GitHub-Benutzername")
        self.user_edit.setToolTip("Gib deinen GitHub-Benutzernamen ein")
        user_layout.addWidget(self.user_edit)
        login_layout.addLayout(user_layout)

        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Personal Access Token:"))
        self.token_edit = QLineEdit()
        self.token_edit.setPlaceholderText("ghp_...")
        self.token_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_edit.setToolTip("Gib deinen Personal Access Token (PAT) ein.")
        token_layout.addWidget(self.token_edit)
        login_layout.addLayout(token_layout)

        btn_login_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Verbinden")
        self.connect_btn.setToolTip("Mit GitHub verbinden")
        self.connect_btn.clicked.connect(self.on_connect)
        btn_login_layout.addWidget(self.connect_btn)

        self.check_token_btn = QPushButton("Token prüfen")
        self.check_token_btn.setToolTip("Prüft, ob der Token gültig ist")
        self.check_token_btn.clicked.connect(self.on_check_token)
        self.check_token_btn.setEnabled(False)
        btn_login_layout.addWidget(self.check_token_btn)

        self.create_token_btn = QPushButton("Neuen Token erstellen")
        self.create_token_btn.setToolTip("Öffnet GitHub-Seite zum Erstellen eines Tokens")
        self.create_token_btn.clicked.connect(self.on_create_token)
        btn_login_layout.addWidget(self.create_token_btn)

        login_layout.addLayout(btn_login_layout)
        main_layout.addWidget(login_group)

        # ---------- Repository-Liste ----------
        list_group = QGroupBox("Repositorys")
        list_layout = QVBoxLayout(list_group)

        self.repo_list = QListWidget()
        self.repo_list.setToolTip("Liste aller GitHub-Repositories")
        self.repo_list.itemSelectionChanged.connect(self.on_repo_selected)
        list_layout.addWidget(self.repo_list)

        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("Neues Repository")
        self.new_btn.setToolTip("Erstellt ein neues Repository auf GitHub")
        self.new_btn.clicked.connect(self.on_new_repo)
        self.new_btn.setEnabled(False)
        btn_layout.addWidget(self.new_btn)

        self.delete_btn = QPushButton("Repository löschen")
        self.delete_btn.setToolTip("Löscht das ausgewählte Repository")
        self.delete_btn.clicked.connect(self.on_delete_repo)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        self.refresh_btn = QPushButton("Aktualisieren")
        self.refresh_btn.setToolTip("Aktualisiert die Repository-Liste")
        self.refresh_btn.clicked.connect(self.on_refresh)
        self.refresh_btn.setEnabled(False)
        btn_layout.addWidget(self.refresh_btn)

        list_layout.addLayout(btn_layout)
        main_layout.addWidget(list_group)

        # ---------- Lokales Repository ----------
        local_group = QGroupBox("Lokales Repository")
        local_layout = QVBoxLayout(local_group)

        # Standardordner
        default_layout = QHBoxLayout()
        default_layout.addWidget(QLabel("Standardordner:"))
        self.default_folder_edit = QLineEdit()
        self.default_folder_edit.setReadOnly(True)
        self.default_folder_edit.setPlaceholderText("Kein Standardordner gesetzt")
        default_layout.addWidget(self.default_folder_edit)

        self.set_default_btn = QPushButton("Als Standard setzen")
        self.set_default_btn.setToolTip("Setzt aktuellen Ordner als Standard")
        self.set_default_btn.clicked.connect(self.on_set_default_folder)
        default_layout.addWidget(self.set_default_btn)

        self.change_default_btn = QPushButton("Ändern")
        self.change_default_btn.setToolTip("Wählt neuen Standardordner")
        self.change_default_btn.clicked.connect(self.on_change_default_folder)
        default_layout.addWidget(self.change_default_btn)

        local_layout.addLayout(default_layout)

        # Aktionen
        action_layout = QHBoxLayout()
        self.clone_btn = QPushButton("Repository klonen")
        self.clone_btn.setToolTip("Klonen des ausgewählten Repositories in den Standardordner")
        self.clone_btn.clicked.connect(self.on_clone_repo)
        self.clone_btn.setEnabled(False)
        action_layout.addWidget(self.clone_btn)

        self.init_btn = QPushButton("Neues Repo init")
        self.init_btn.setToolTip(
            "Erstellt ein neues lokales Git-Repository (git init) und verknüpft "
            "es mit dem oben in der Liste ausgewählten GitHub-Repository"
        )
        self.init_btn.clicked.connect(self.on_init_repo)
        self.init_btn.setEnabled(False)
        action_layout.addWidget(self.init_btn)

        self.browse_btn = QPushButton("Ordner auswählen")
        self.browse_btn.setToolTip("Wählt einen lokalen Ordner als Git-Repository")
        self.browse_btn.clicked.connect(self.on_browse_folder)
        self.browse_btn.setEnabled(False)
        action_layout.addWidget(self.browse_btn)

        local_layout.addLayout(action_layout)

        # Pfad
        path_layout = QHBoxLayout()
        path_layout.addWidget(QLabel("Geladen:"))
        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText("Kein Repository geladen")
        path_layout.addWidget(self.path_edit)
        local_layout.addLayout(path_layout)

        # Commit
        commit_layout = QHBoxLayout()
        commit_layout.addWidget(QLabel("Commit-Nachricht:"))
        self.commit_msg_edit = QLineEdit()
        self.commit_msg_edit.setPlaceholderText("Änderungen beschreiben...")
        commit_layout.addWidget(self.commit_msg_edit)

        self.commit_btn = QPushButton("Commit")
        self.commit_btn.setToolTip("Fügt alle Änderungen hinzu und erstellt Commit")
        self.commit_btn.clicked.connect(self.on_commit)
        self.commit_btn.setEnabled(False)
        commit_layout.addWidget(self.commit_btn)

        local_layout.addLayout(commit_layout)

        # Push/Pull/Branch
        push_pull_layout = QHBoxLayout()
        self.push_btn = QPushButton("Push zu GitHub")
        self.push_btn.setToolTip("Pusht Commits zu GitHub")
        self.push_btn.clicked.connect(self.on_push)
        self.push_btn.setEnabled(False)
        push_pull_layout.addWidget(self.push_btn)

        self.pull_btn = QPushButton("Pull von GitHub")
        self.pull_btn.setToolTip("Holt Änderungen von GitHub")
        self.pull_btn.clicked.connect(self.on_pull)
        self.pull_btn.setEnabled(False)
        push_pull_layout.addWidget(self.pull_btn)

        self.link_remote_btn = QPushButton("Mit GitHub verknüpfen")
        self.link_remote_btn.setToolTip(
            "Setzt den Remote 'origin' des geladenen lokalen Repositories auf "
            "das oben in der Liste ausgewählte GitHub-Repository"
        )
        self.link_remote_btn.clicked.connect(self.on_link_remote)
        self.link_remote_btn.setEnabled(False)
        push_pull_layout.addWidget(self.link_remote_btn)

        self.branch_label = QLabel("Branch: –")
        push_pull_layout.addWidget(self.branch_label)
        push_pull_layout.addStretch()

        local_layout.addLayout(push_pull_layout)
        main_layout.addWidget(local_group)

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

    def save_default_folder(self, folder):
        self.default_folder = folder
        self.default_folder_edit.setText(folder)
        settings = load_settings()
        settings['default_folder'] = folder
        save_settings(settings)

    def on_set_default_folder(self):
        if self.local_repo_path and os.path.isdir(self.local_repo_path):
            self.save_default_folder(self.local_repo_path)
            self.status_bar.showMessage(f"Standardordner gesetzt: {self.local_repo_path}")
        else:
            QMessageBox.warning(self, "Kein Ordner", "Lade zuerst ein lokales Repository.")

    def on_change_default_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Standardordner auswählen",
            self.default_folder or os.path.expanduser("~"),
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self.save_default_folder(folder)
            self.status_bar.showMessage(f"Standardordner geändert: {folder}")

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
                    self.status_bar.showMessage(f"Token gespeichert vor {days} Tag(en)")
                except:
                    pass
            self.check_token_btn.setEnabled(True)
            self.on_check_token()
        else:
            self.check_token_btn.setEnabled(False)

    def on_check_token(self):
        token = self.token_edit.text().strip()
        if not token:
            QMessageBox.information(self, "Token prüfen", "Kein Token eingegeben.")
            return

        self.status_bar.showMessage("Prüfe Token...")
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
                    f"Token gültig (Benutzer: {username}) – gespeichert vor {days} Tag(en)"
                )
            except:
                self.status_bar.showMessage(f"Token gültig (Benutzer: {username})")
        else:
            self.status_bar.showMessage(f"Token gültig (Benutzer: {username})")

    def _on_token_invalid(self, error_msg):
        self.check_token_btn.setEnabled(True)
        self.status_bar.showMessage("Token ist ungültig oder abgelaufen")
        if "401" in error_msg or "Bad credentials" in error_msg:
            reply = QMessageBox.warning(
                self,
                "Token ungültig",
                "Der Token ist ungültig. Möchtest du das Feld leeren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.token_edit.clear()
                self.token_edit.setFocus()
        else:
            QMessageBox.critical(self, "Fehler", f"Fehler bei der Token-Prüfung:\n{error_msg}")

    def on_create_token(self):
        webbrowser.open("https://github.com/settings/tokens")
        QMessageBox.information(
            self,
            "Token erstellen",
            "Die GitHub-Seite wurde geöffnet.\n\n"
            "1. Klicke auf 'Generate new token' (classic)\n"
            "2. Wähle ein Ablaufdatum\n"
            "3. Wähle die Berechtigung 'repo'\n"
            "4. Token kopieren und hier einfügen"
        )

    def on_connect(self):
        username = self.user_edit.text().strip()
        token = self.token_edit.text().strip()
        if not username or not token:
            QMessageBox.warning(self, "Fehler", "Bitte Benutzername und Token eingeben.")
            return
        self.status_bar.showMessage("Verbinde...")
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
        self.status_bar.showMessage(f"Verbunden als {self.current_user.login}")
        self._populate_repo_list()
        save_config(self.user_edit.text().strip(), self.token)

    def _on_connect_error(self, error_msg):
        self.connect_btn.setEnabled(True)
        self.status_bar.showMessage("Verbindung fehlgeschlagen")
        QMessageBox.critical(self, "Verbindungsfehler", f"Fehler bei der Verbindung:\n{error_msg}")

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
        else:
            self.selected_repo = None
            self.delete_btn.setEnabled(False)

    def on_refresh(self):
        if not self.github or not self.current_user:
            return
        self.status_bar.showMessage("Lade Repositorys neu...")
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
        self.status_bar.showMessage("Repositorys aktualisiert")

    def _on_refresh_error(self, error_msg):
        self.refresh_btn.setEnabled(True)
        self.status_bar.showMessage("Aktualisierung fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Aktualisieren:\n{error_msg}")

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
                QMessageBox.warning(self, "Fehler", "Der Repository-Name darf nicht leer sein.")
                return
            # Beschreibung bereinigen
            description = data["description"]
            cleaned_description = re.sub(r'[\x00-\x1F\x7F]', ' ', description)
            cleaned_description = re.sub(r'\s+', ' ', cleaned_description).strip()
            data["description"] = cleaned_description

            self.status_bar.showMessage(f"Erstelle Repository '{data['name']}'...")
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
        self.status_bar.showMessage(f"Repository '{repo.name}' erstellt")
        self.on_refresh()

    def _on_create_error(self, error_msg):
        self.new_btn.setEnabled(True)
        self.status_bar.showMessage("Erstellen fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Erstellen:\n{error_msg}")

    def on_delete_repo(self):
        if not self.selected_repo:
            return
        repo_name = self.selected_repo.name
        reply = QMessageBox.question(
            self,
            "Repository löschen",
            f"Soll das Repository '{repo_name}' wirklich gelöscht werden?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self.status_bar.showMessage(f"Lösche Repository '{repo_name}'...")
        self.delete_btn.setEnabled(False)
        self.worker = GithubWorker(self._delete_repo, self.selected_repo)
        self.worker.finished.connect(self._on_delete_finished)
        self.worker.error.connect(self._on_delete_error)
        self.worker.start()

    def _delete_repo(self, repo):
        repo.delete()

    def _on_delete_finished(self, _):
        self.delete_btn.setEnabled(True)
        self.status_bar.showMessage("Repository gelöscht")
        self.selected_repo = None
        self.on_refresh()

    def _on_delete_error(self, error_msg):
        self.delete_btn.setEnabled(True)
        self.status_bar.showMessage("Löschen fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Löschen:\n{error_msg}")

    # ------------------------------------------------------------------
    # Lokales Repository
    # ------------------------------------------------------------------
    def _load_repo(self, folder):
        try:
            repo = Repo(folder)
            branch = repo.active_branch.name
            self.branch_label.setText(f"Branch: {branch}")
            self.local_repo_path = folder
            self.repo_obj = repo
            self.path_edit.setText(folder)
            self.commit_btn.setEnabled(True)

            if not repo.remotes:
                # Kein Remote vorhanden: Repo trotzdem laden (Commit ist ja
                # unabhängig von GitHub möglich), aber Push/Pull sind erst
                # nach Verknüpfung mit einem GitHub-Repository sinnvoll.
                self.push_btn.setEnabled(False)
                self.pull_btn.setEnabled(False)
                self.link_remote_btn.setEnabled(True)
                self.status_bar.showMessage(
                    f"Lokales Repository geladen: {folder} – kein Remote konfiguriert. "
                    "Wähle oben ein GitHub-Repository aus und klicke auf "
                    "'Mit GitHub verknüpfen'."
                )
                QMessageBox.information(
                    self,
                    "Kein Remote konfiguriert",
                    f"'{folder}' wurde geladen, ist aber noch nicht mit einem "
                    "GitHub-Repository verknüpft (kein 'origin' Remote).\n\n"
                    "Wähle oben in der Liste 'Repositorys' das passende GitHub-"
                    "Repository aus und klicke dann auf 'Mit GitHub verknüpfen', "
                    "um Push/Pull zu aktivieren."
                )
            else:
                self.push_btn.setEnabled(True)
                self.pull_btn.setEnabled(True)
                self.link_remote_btn.setEnabled(True)
                self.status_bar.showMessage(f"Lokales Repository geladen: {folder}")
            return True
        except InvalidGitRepositoryError:
            QMessageBox.critical(self, "Kein Git-Repository", f"'{folder}' ist kein Git-Repository.")
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Laden:\n{e}")
        return False

    def on_link_remote(self):
        """Verknüpft das geladene lokale Repository mit dem ausgewählten
        GitHub-Repository, indem der Remote 'origin' gesetzt bzw. überschrieben wird."""
        if not self.repo_obj:
            QMessageBox.warning(self, "Kein Repository", "Lade zuerst ein lokales Repository.")
            return
        if not self.selected_repo:
            QMessageBox.warning(
                self,
                "Kein GitHub-Repository ausgewählt",
                "Wähle zuerst oben in der Liste 'Repositorys' das GitHub-"
                "Repository aus, mit dem verknüpft werden soll."
            )
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, "Fehler", "Bitte verbinde dich zuerst.")
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
                f"Mit GitHub-Repository '{self.selected_repo.full_name}' verknüpft"
            )
            QMessageBox.information(
                self,
                "Verknüpft",
                f"Das lokale Repository ist nun mit "
                f"'{self.selected_repo.full_name}' verknüpft.\n\n"
                "Falls das GitHub-Repository bereits Inhalte hat und das lokale "
                "Repository noch keine gemeinsame Historie hat, zuerst "
                "'Pull von GitHub' ausführen, bevor gepusht wird."
            )
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Verknüpfen:\n{e}")

    def on_browse_folder(self):
        start_dir = self.default_folder if self.default_folder else os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(
            self,
            "Lokales Git-Repository auswählen",
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )
        if folder:
            self._load_repo(folder)

    def on_clone_repo(self):
        if not self.selected_repo:
            QMessageBox.warning(self, "Kein Repository", "Wähle zuerst ein Repository aus.")
            return
        if not self.default_folder:
            QMessageBox.warning(self, "Kein Standardordner", "Setze zuerst einen Standardordner.")
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, "Fehler", "Bitte verbinde dich zuerst.")
            return

        repo_name = self.selected_repo.name
        target_dir = os.path.join(self.default_folder, repo_name)

        if os.path.exists(target_dir):
            reply = QMessageBox.question(
                self,
                "Ordner existiert",
                f"Der Ordner '{target_dir}' existiert. Überschreiben?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        self.status_bar.showMessage(f"Klone {repo_name}...")
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
        self.status_bar.showMessage(f"Repository geklont: {repo.working_dir}")
        self._load_repo(repo.working_dir)

    def _on_clone_error(self, error_msg):
        self.clone_btn.setEnabled(True)
        self.status_bar.showMessage("Klonen fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Klonen:\n{error_msg}")

    def on_init_repo(self):
        if not self.default_folder:
            QMessageBox.warning(self, "Kein Standardordner", "Setze zuerst einen Standardordner.")
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, "Fehler", "Bitte verbinde dich zuerst.")
            return
        if not self.selected_repo:
            # Das ist die Ursache von "Kein Remote konfiguriert": ein frisch mit
            # 'git init' erstelltes Repository hat noch keinen Remote. Ohne ein
            # ausgewähltes GitHub-Repository wüsste die App nicht, welches
            # Remote sie setzen soll.
            QMessageBox.warning(
                self,
                "Kein GitHub-Repository ausgewählt",
                "Wähle zuerst oben in der Liste 'Repositorys' das GitHub-"
                "Repository aus, mit dem das neue lokale Repository verknüpft "
                "werden soll.\n\n"
                "Falls es noch nicht existiert, lege es zuerst über "
                "'Neues Repository' an."
            )
            return

        # Warnung, falls das GitHub-Repository bereits Inhalte hat: 'git init' +
        # Push würde dann auf unzusammenhängende Historien treffen und scheitern
        # (bzw. einen Force-Push erfordern). In diesem Fall ist 'Repository
        # klonen' der richtige Weg.
        if getattr(self.selected_repo, "size", 0) and self.selected_repo.size > 0:
            reply = QMessageBox.question(
                self,
                "Repository ist nicht leer",
                f"'{self.selected_repo.name}' enthält auf GitHub bereits Dateien.\n"
                "Ein neues lokales Repository per 'git init' hat eine eigene, "
                "unabhängige Historie – der erste Push würde fehlschlagen oder "
                "einen Force-Push erfordern.\n\n"
                "Empfehlung: Stattdessen 'Repository klonen' verwenden.\n\n"
                "Trotzdem fortfahren?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            if reply != QMessageBox.StandardButton.Yes:
                return

        name, ok = QInputDialog.getText(
            self,
            "Neues Repository",
            "Name des neuen lokalen Ordners:",
            text=self.selected_repo.name
        )
        if not ok or not name.strip():
            return
        name = name.strip()
        target_dir = os.path.join(self.default_folder, name)

        if os.path.exists(target_dir):
            QMessageBox.warning(self, "Existiert", f"Der Ordner '{target_dir}' existiert bereits.")
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
                f"Neues Repository initialisiert und mit "
                f"'{self.selected_repo.full_name}' verknüpft: {target_dir}"
            )
            self._load_repo(target_dir)
        except Exception as e:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Initialisieren:\n{e}")

    # ------------------------------------------------------------------
    # Commit / Push / Pull
    # ------------------------------------------------------------------
    def on_commit(self):
        if not self.repo_obj:
            QMessageBox.warning(self, "Fehler", "Kein lokales Repository ausgewählt.")
            return
        msg = self.commit_msg_edit.text().strip()
        if not msg:
            QMessageBox.warning(self, "Fehler", "Bitte eine Commit-Nachricht eingeben.")
            return

        self.status_bar.showMessage("Commit wird ausgeführt...")
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
                raise RuntimeError(
                    "Keine Änderungen zum Committen gefunden.\n"
                    "Prüfe, ob im richtigen Ordner gearbeitet wurde und ob die "
                    "geänderten Dateien nicht durch .gitignore ausgeschlossen sind."
                )
            commit = self.repo_obj.index.commit(msg)
            return commit

        self.worker = GithubWorker(do_commit)
        self.worker.finished.connect(self._on_commit_finished)
        self.worker.error.connect(self._on_commit_error)
        self.worker.start()

    def _on_commit_finished(self, commit):
        self.commit_btn.setEnabled(True)
        self.status_bar.showMessage(f"Commit erfolgreich: {commit.hexsha[:7]}")
        self.commit_msg_edit.clear()
        if self.repo_obj:
            self.branch_label.setText(f"Branch: {self.repo_obj.active_branch.name}")

    def _on_commit_error(self, error_msg):
        self.commit_btn.setEnabled(True)
        self.status_bar.showMessage("Commit fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Commit:\n{error_msg}")

    def on_push(self):
        if not self.repo_obj:
            QMessageBox.warning(self, "Fehler", "Kein lokales Repository ausgewählt.")
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, "Fehler", "Kein Token oder Benutzer. Bitte verbinde dich erneut.")
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
            box.setWindowTitle("Branch-Abweichung")
            box.setText(
                f"Der lokale Branch heißt '{local_branch}', der Standard-Branch "
                f"dieses Repositories auf GitHub ist aber '{default_branch}'.\n\n"
                "Wohin soll gepusht werden?"
            )
            btn_default = box.addButton(
                f"Auf '{default_branch}' pushen (empfohlen)", QMessageBox.ButtonRole.AcceptRole
            )
            btn_same = box.addButton(
                f"Auf '{local_branch}' pushen", QMessageBox.ButtonRole.ActionRole
            )
            box.addButton("Abbrechen", QMessageBox.ButtonRole.RejectRole)
            box.setDefaultButton(btn_default)
            box.exec()
            clicked = box.clickedButton()
            if clicked == btn_default:
                target_branch = default_branch
            elif clicked == btn_same:
                target_branch = local_branch
            else:
                self.status_bar.showMessage("Push abgebrochen")
                return

        self.status_bar.showMessage("Push wird ausgeführt...")
        self.push_btn.setEnabled(False)

        def do_push():
            origin = self.repo_obj.remotes.origin
            # URL auf korrekte authentifizierte Version setzen
            self._ensure_auth_url(origin)
            branch = self.repo_obj.active_branch
            refspec = f"{branch.name}:{target_branch}"
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
                raise RuntimeError(
                    "GitHub hat keine Rückmeldung zum Push gesendet. "
                    "Es kann nicht bestätigt werden, dass die Änderungen "
                    "übertragen wurden."
                )

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
                    "GitHub hat den Push abgelehnt:\n" + "\n".join(error_summaries) +
                    "\n\nMögliche Ursache: Der Remote-Branch enthält Commits, die "
                    "lokal nicht vorhanden sind (z.B. Änderungen über die GitHub-"
                    "Weboberfläche). Erst 'Pull von GitHub' ausführen, dann erneut pushen."
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

        if result.get("up_to_date"):
            self.status_bar.showMessage(
                f"Push: Branch '{remote_branch}' war bereits aktuell – keine neuen Commits"
            )
            QMessageBox.information(
                self,
                "Bereits aktuell",
                f"Es gab keine neuen Commits, die nach '{remote_branch}' übertragen "
                "werden konnten.\n\nWurden die Änderungen vorher committet?"
            )
        elif local_branch != remote_branch:
            self.status_bar.showMessage(
                f"Push erfolgreich: '{local_branch}' → GitHub-Branch '{remote_branch}'"
            )
        else:
            self.status_bar.showMessage(f"Push erfolgreich (Branch: {remote_branch})")

    def _on_push_error(self, error_msg):
        self.push_btn.setEnabled(True)
        self.status_bar.showMessage("Push fehlgeschlagen")
        if "non-fast-forward" in error_msg or "rejected" in error_msg.lower():
            reply = QMessageBox.critical(
                self,
                "Fehler",
                f"Fehler beim Push:\n{error_msg}\n\n"
                "Möchtest du jetzt einen Pull ausführen, um die Remote-Änderungen "
                "zuerst zu holen und danach erneut zu pushen?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.on_pull()
        else:
            QMessageBox.critical(self, "Fehler", f"Fehler beim Push:\n{error_msg}")

    def on_pull(self):
        if not self.repo_obj:
            QMessageBox.warning(self, "Fehler", "Kein lokales Repository ausgewählt.")
            return
        if not self.token or not self.current_user:
            QMessageBox.warning(self, "Fehler", "Kein Token oder Benutzer. Bitte verbinde dich erneut.")
            return

        self.status_bar.showMessage("Pull wird ausgeführt...")
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
                            raise RuntimeError(
                                "Merge-Konflikt beim Zusammenführen der bisher "
                                "unabhängigen Historien: dieselben Dateien wurden "
                                "lokal und auf GitHub unterschiedlich geändert.\n\n"
                                "Bitte im Terminal im Projektordner mit 'git status' "
                                "prüfen, Konflikte manuell lösen und anschließend "
                                "committen."
                            )
                        raise RuntimeError(f"Pull fehlgeschlagen:\n{e2}")
                elif "conflict" in msg.lower():
                    raise RuntimeError(
                        "Merge-Konflikt beim Pull. Bitte im Terminal im "
                        "Projektordner mit 'git status' prüfen, Konflikte "
                        "manuell lösen und anschließend committen."
                    )
                else:
                    raise

            return remote_branch

        self.worker = GithubWorker(do_pull)
        self.worker.finished.connect(self._on_pull_finished)
        self.worker.error.connect(self._on_pull_error)
        self.worker.start()

    def _on_pull_finished(self, remote_branch):
        self.pull_btn.setEnabled(True)
        self.status_bar.showMessage(f"Pull erfolgreich von '{remote_branch}'")
        if self.repo_obj:
            self.branch_label.setText(f"Branch: {self.repo_obj.active_branch.name}")

    def _on_pull_error(self, error_msg):
        self.pull_btn.setEnabled(True)
        self.status_bar.showMessage("Pull fehlgeschlagen")
        QMessageBox.critical(self, "Fehler", f"Fehler beim Pull:\n{error_msg}")


# ----------------------------------------------------------------------
# 5. Start
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
