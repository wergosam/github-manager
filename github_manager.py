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
    QScrollArea
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

        self.init_ui()
        self.load_saved_credentials()
        self.load_settings()
        self.status_bar.showMessage(tr("status_ready"))

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
        self.help_menu.setTitle(tr("menu_help"))
        self.action_help.setText(tr("menu_action_manual"))
        self.action_about.setText(tr("menu_action_about"))
        self.language_menu.setTitle(tr("menu_language"))

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
        main_layout = QVBoxLayout(central)

        # ---------- Menüleiste ----------
        menubar = self.menuBar()
        self.help_menu = menubar.addMenu(tr("menu_help"))

        self.action_help = QAction(tr("menu_action_manual"), self)
        self.action_help.setShortcut("F1")
        self.action_help.triggered.connect(self.on_show_help)
        self.help_menu.addAction(self.action_help)

        self.help_menu.addSeparator()

        self.action_about = QAction(tr("menu_action_about"), self)
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

        self.link_remote_btn = QPushButton(tr("btn_link_remote"))
        self.link_remote_btn.setToolTip(tr("btn_link_remote_tooltip"))
        self.link_remote_btn.clicked.connect(self.on_link_remote)
        self.link_remote_btn.setEnabled(False)
        push_pull_layout.addWidget(self.link_remote_btn)

        self.branch_label = QLabel(tr("branch_label_empty"))
        push_pull_layout.addWidget(self.branch_label)
        push_pull_layout.addStretch()

        local_layout.addLayout(push_pull_layout)
        main_layout.addWidget(self.local_group)

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
        else:
            self.selected_repo = None
            self.delete_btn.setEnabled(False)

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

    def _on_pull_error(self, error_msg):
        self.pull_btn.setEnabled(True)
        self.status_bar.showMessage(tr("status_pull_failed"))
        QMessageBox.critical(self, tr("msg_error_title"), tr("msg_pull_error", error=error_msg))


# ----------------------------------------------------------------------
# 5. Start
# ----------------------------------------------------------------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
