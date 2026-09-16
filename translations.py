#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Zentrale Übersetzungsverwaltung für den GitHub Repository Manager.

Neue Sprache hinzufügen:
  1. Sprachcode + Anzeigename in AVAILABLE_LANGUAGES eintragen.
  2. Einen neuen Eintrag in TRANSLATIONS mit allen Schlüsseln (am besten
     die komplette "de"- oder "en"-Sektion kopieren und übersetzen) anlegen.
Das war's – die GUI und die Konsolenausgaben übernehmen die neue Sprache
automatisch (Sprachmenü, Systemspracherkennung, gespeicherte Auswahl).
"""

import os
import json
import locale

CONFIG_DIR = os.path.expanduser("~/.config/github_manager")
SETTINGS_FILE = os.path.join(CONFIG_DIR, "settings.json")

# Sprachcode -> Anzeigename (wird z.B. im Sprachmenü verwendet)
AVAILABLE_LANGUAGES = {
    "de": "Deutsch",
    "en": "English",
}

DEFAULT_LANGUAGE = "de"

TRANSLATIONS = {
    # ====================================================================
    # DEUTSCH
    # ====================================================================
    "de": {
        # ---- Abhängigkeiten / Konsole ----
        "deps_header": "FEHLENDE ABHÄNGIGKEITEN",
        "deps_needed": "Folgende Module werden benötigt, sind aber nicht installiert: {modules}",
        "deps_distro": "Erkannte Distribution: {distro}",
        "deps_prompt": "\nMöchtest du die fehlenden Pakete automatisch installieren lassen? (j/N): ",
        "deps_declined": "Installation abgelehnt. Bitte installiere die Pakete manuell und starte das Skript neu.",
        "deps_install_done_restart": "\nInstallation abgeschlossen. Starte das Skript neu...",
        "deps_install_failed_manual": "\nInstallation fehlgeschlagen. Bitte installiere die Pakete manuell und starte das Skript neu.",
        "deps_try_system_pkg": "\nVersuche Installation mit Systempaketmanager: {cmd}",
        "deps_system_success": "Systeminstallation erfolgreich.",
        "deps_system_failed_try_pip": "Systeminstallation fehlgeschlagen. Versuche jetzt pip --user...",
        "deps_no_system_mgr": "Kein Systempaketmanager erkannt. Verwende pip --user.",
        "deps_running": "\nFühre aus: {cmd}",
        "deps_pip_success": "pip-Installation erfolgreich.",
        "deps_pip_failed": "pip-Installation fehlgeschlagen.",

        # ---- Dialog: Neues Repository ----
        "dlg_newrepo_title": "Neues Repository erstellen",
        "dlg_newrepo_name_label": "Name:",
        "dlg_newrepo_name_placeholder": "Repository-Name",
        "dlg_newrepo_desc_label": "Beschreibung:",
        "dlg_newrepo_desc_placeholder": "Beschreibung (optional)",
        "dlg_newrepo_visibility_label": "Sichtbarkeit:",
        "dlg_newrepo_private_checkbox": "Privat",

        # ---- Dialog: Neues Release ----
        "dlg_newrelease_title": "Neues Release erstellen",
        "dlg_newrelease_tag_label": "Tag:",
        "dlg_newrelease_tag_placeholder": "z.B. v1.0.0",
        "dlg_newrelease_target_label": "Ziel-Branch:",
        "dlg_newrelease_target_placeholder": "Standard-Branch verwenden (optional)",
        "dlg_newrelease_reltitle_label": "Titel:",
        "dlg_newrelease_reltitle_placeholder": "Release-Titel (optional, sonst Tag)",
        "dlg_newrelease_notes_label": "Notizen / Changelog:",
        "dlg_newrelease_notes_placeholder": "Was ist neu in diesem Release?",
        "dlg_newrelease_prerelease_checkbox": "Als Vorabversion (Pre-Release) markieren",
        "dlg_newrelease_draft_checkbox": "Als Entwurf speichern (nicht veröffentlichen)",

        # ---- Dialog: Hilfe ----
        "dlg_help_title": "Hilfe – GitHub Repository Manager",
        "help_html": """
<style>
  body { font-family: sans-serif; font-size: 13px; }
  h2 { color: #2a6099; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  h3 { color: #1a4070; margin-top: 14px; margin-bottom: 4px; }
  p, li { line-height: 1.6; }
  ul { margin-top: 4px; }
  code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
  .hinweis { background: #fffbe6; border-left: 4px solid #f0b429;
             padding: 6px 10px; margin: 8px 0; border-radius: 3px; }
  .tipp { background: #e8f4fd; border-left: 4px solid #2a6099;
          padding: 6px 10px; margin: 8px 0; border-radius: 3px; }
</style>
<h2>GitHub Repository Manager – Benutzerhandbuch</h2>

<h2>1. Erste Schritte – Login</h2>
<p>Um die App zu nutzen, benötigst du einen GitHub-Account und einen
<b>Personal Access Token (PAT)</b>.</p>
<h3>Token erstellen</h3>
<ul>
  <li>Klicke auf <b>„Neuen Token erstellen"</b> – die GitHub-Einstellungsseite öffnet sich.</li>
  <li>Wähle <b>„Generate new token (classic)"</b>.</li>
  <li>Setze ein Ablaufdatum und aktiviere die Berechtigung <code>repo</code>.</li>
  <li>Kopiere den generierten Token und füge ihn im Feld <b>„Personal Access Token"</b> ein.</li>
</ul>
<h3>Verbinden</h3>
<ul>
  <li>Benutzername und Token eingeben, dann <b>„Verbinden"</b> klicken.</li>
  <li>Bei Erfolg erscheinen deine Repositories in der Liste.</li>
  <li>Zugangsdaten werden lokal gespeichert (<code>~/.config/github_manager/</code>)
      und beim nächsten Start automatisch geladen.</li>
</ul>
<div class="tipp">
  <b>Tipp:</b> Mit <b>„Token prüfen"</b> kannst du jederzeit die Gültigkeit
  deines Tokens testen, ohne dich neu zu verbinden.
</div>

<h2>2. Repositories verwalten</h2>
<h3>Neues Repository erstellen</h3>
<ul>
  <li>Klicke auf <b>„Neues Repository"</b>.</li>
  <li>Namen und optionale Beschreibung eingeben, Sichtbarkeit wählen (öffentlich/privat).</li>
  <li>Das Repository wird auf GitHub angelegt und erscheint sofort in der Liste.</li>
</ul>
<h3>Repository löschen</h3>
<ul>
  <li>Repository in der Liste auswählen, dann <b>„Repository löschen"</b> klicken.</li>
  <li>Eine Sicherheitsabfrage verhindert versehentliches Löschen.</li>
</ul>
<div class="hinweis">
  <b>Achtung:</b> Das Löschen entfernt das Repository unwiderruflich von GitHub,
  einschliesslich aller Commits, Issues und Pull Requests.
</div>
<h3>Liste aktualisieren</h3>
<ul>
  <li><b>„Aktualisieren"</b> lädt die Repository-Liste neu von GitHub.</li>
</ul>

<h2>3. Lokales Repository</h2>
<h3>Standardordner setzen</h3>
<p>Der Standardordner ist der Basisordner, in dem Repositories geklont oder
initialisiert werden.</p>
<ul>
  <li><b>„Als Standard setzen"</b> – übernimmt den aktuell geladenen Repo-Pfad als Standard.</li>
  <li><b>„Ändern"</b> – öffnet einen Ordner-Auswahldialog.</li>
</ul>
<h3>Repository klonen</h3>
<ul>
  <li>Ein Repository in der Liste auswählen.</li>
  <li><b>„Repository klonen"</b> klicken – der Inhalt wird in den Standardordner heruntergeladen.</li>
  <li>Das geklonte Repository wird automatisch als aktives lokales Repo geladen.</li>
</ul>
<h3>Neues lokales Repository initialisieren</h3>
<ul>
  <li>Ein <b>GitHub-Repository</b> in der Liste auswählen (Ziel für den späteren Push).</li>
  <li><b>„Neues lokales Repo"</b> klicken.</li>
  <li>Es wird ein neuer Ordner im Standardverzeichnis erstellt, <code>git init</code>
      ausgeführt und <code>origin</code> auf das gewählte GitHub-Repository gesetzt.</li>
</ul>
<div class="hinweis">
  <b>Achtung:</b> Falls das GitHub-Repository bereits Dateien enthält (z.B. ein
  automatisch erstelltes README), ist <b>„Repository klonen"</b> der richtige Weg –
  sonst entstehen divergente Historien.
</div>
<h3>Vorhandenes lokales Repository laden</h3>
<ul>
  <li><b>„Lokales Repo laden"</b> öffnet einen Ordner-Auswahldialog.</li>
  <li>Wähle einen Ordner, der bereits ein <code>.git</code>-Verzeichnis enthält.</li>
</ul>

<h2>4. Commit, Push und Pull</h2>
<h3>Commit</h3>
<ul>
  <li>Eine Commit-Nachricht im Textfeld eingeben.</li>
  <li><b>„Commit"</b> klicken – alle Änderungen im Repo werden gestaged und committet.</li>
</ul>
<div class="hinweis">
  <b>„Keine Änderungen gefunden"</b> bedeutet: Im geladenen Ordner gibt es keine
  geänderten Dateien. Prüfe, ob du den richtigen Ordner geladen hast oder ob
  Dateien durch <code>.gitignore</code> ausgeschlossen sind.
</div>
<h3>Push</h3>
<ul>
  <li><b>„Push zu GitHub"</b> überträgt die lokalen Commits auf GitHub.</li>
  <li>Falls der lokale Branch anders heisst als der Standard-Branch auf GitHub
      (z.B. <code>master</code> vs. <code>main</code>), erscheint eine Rückfrage.</li>
  <li>Bei einem abgelehnten Push (<b>non-fast-forward</b>) bietet die App an,
      automatisch einen Pull auszuführen.</li>
</ul>
<h3>Pull</h3>
<ul>
  <li><b>„Pull von GitHub"</b> holt die neuesten Commits vom Remote und merged sie lokal.</li>
  <li>Bei Merge-Konflikten erscheint eine Meldung – die Konflikte müssen manuell
      im Terminal gelöst werden (<code>git status</code>, Dateien bearbeiten,
      dann committen).</li>
</ul>
<div class="tipp">
  <b>Empfohlener Arbeitsablauf:</b><br>
  1. <b>Pull</b> ausführen (Remote-Änderungen holen)<br>
  2. Dateien bearbeiten<br>
  3. <b>Commit</b> mit aussagekräftiger Nachricht<br>
  4. <b>Push</b> zu GitHub
</div>

<h2>5. Release erstellen</h2>
<ul>
  <li>Repository in der Liste auswählen, dann <b>„Release erstellen"</b> klicken.</li>
  <li>Tag (z.B. <code>v1.3.0</code>), Ziel-Branch, Titel und Release-Notes eingeben;
      optional als <b>Vorabversion</b> oder <b>Entwurf</b> markieren.</li>
  <li>Ein Release taggt den Stand, der gerade <b>auf GitHub</b> liegt – nicht den
      lokalen Arbeitsstand.</li>
</ul>
<div class="hinweis">
  <b>Reihenfolge-Prüfung:</b> Ist zufällig das passende lokale Repository geladen,
  prüft die App vorher kurz den Status. Gibt es noch uncommittete Änderungen,
  ungepushte Commits oder einen offenen Merge, warnt sie mit dem Hinweis
  <b>„Noch nicht alles gepusht"</b> und der empfohlenen Reihenfolge
  <b>Commit → Push → Release</b>. Du kannst trotzdem fortfahren, solltest dann
  aber wissen, dass diese Änderungen nicht im Release enthalten sind.
</div>

<h2>6. AUR-Paket verwalten (Tab „AUR")</h2>
<h3>Ordner laden</h3>
<ul>
  <li><b>„Ordner auswählen"</b> öffnet einen bereits vorhandenen lokalen
      AUR-Git-Ordner (mit <code>PKGBUILD</code>).</li>
  <li>Paketname, aktuelle Version und <code>pkgrel</code> werden angezeigt.</li>
</ul>
<h3>Neues AUR-Paket erstellen</h3>
<ul>
  <li><b>„Neues AUR-Paket erstellen"</b> legt ein PKGBUILD-Grundgerüst für ein
      noch nicht existierendes Paket an, gekoppelt an ein GitHub-Repository
      (Name, Startversion, Beschreibung, URL, Lizenz, Architektur und
      Abhängigkeiten werden abgefragt).</li>
  <li>Erstellt den Ordner, initialisiert ein Git-Repository und setzt den
      Remote auf <code>ssh://aur@aur.archlinux.org/&lt;paket&gt;.git</code> –
      veröffentlicht wird das Paket aber erst mit dem ersten Push.</li>
  <li>Wird direkt nach dem Erstellen eines <b>neuen GitHub-Repositorys</b>
      angeboten (Rückfrage „Möchtest du dafür auch ein AUR-Paket anlegen?"),
      lässt sich aber jederzeit auch einzeln im AUR-Tab starten.</li>
</ul>
<div class="hinweis">
  <b>Achtung:</b> Der generierte <code>package()</code>-Abschnitt ist nur ein
  Platzhalter und muss ans jeweilige Projekt angepasst werden. Ausserdem
  braucht <code>source=</code> einen existierenden GitHub-Tag – lege also
  zuerst ein passendes Release an (siehe Abschnitt 5), bevor du
  „Version aktualisieren" für das neue Paket ausführst. Zum Veröffentlichen
  muss zudem ein SSH-Schlüssel im eigenen AUR-Konto hinterlegt sein.
</div>
<h3>Version aktualisieren</h3>
<ul>
  <li>Neue Version eintragen, dann <b>„Version aktualisieren"</b> klicken.</li>
  <li>Das setzt <code>pkgver</code> in der PKGBUILD, lädt per <code>updpkgsums</code>
      die in <code>source=</code> referenzierten Dateien neu herunter und schreibt
      die Prüfsummen, und generiert die <code>.SRCINFO</code> neu
      (<code>makepkg --printsrcinfo</code>).</li>
  <li>Dieser Schritt ändert nur <b>lokale</b> Dateien – er committet und pusht
      noch nichts zum AUR.</li>
</ul>
<div class="hinweis">
  <b>Achtung:</b> Verweist <code>source=</code> auf einen Git-Tag
  (z.B. <code>archive/refs/tags/v$pkgver.tar.gz</code>), muss dieser Tag bereits
  auf GitHub existieren, sonst schlägt <code>updpkgsums</code> fehl. Also zuerst
  den passenden GitHub-Release/Tag erstellen (siehe Abschnitt 5), dann die
  AUR-Version aktualisieren.
</div>
<h3>Commit && Push</h3>
<ul>
  <li>Committet <b>ausschliesslich</b> <code>PKGBUILD</code> und
      <code>.SRCINFO</code> (Build-Artefakte wie <code>pkg/</code>, <code>src/</code>
      oder <code>*.pkg.tar.zst</code> werden bewusst nicht mit eingecheckt) und
      pusht anschliessend zum AUR-Git-Repository.</li>
</ul>
<h3>Status prüfen / Empfohlene Aktion</h3>
<ul>
  <li><b>„Status prüfen"</b> zeigt an, was als Nächstes ansteht (z.B.
      „Commit nötig", „Push nötig", „Aktuell").</li>
  <li><b>„Empfehlung ausführen"</b> führt die vorgeschlagene Aktion direkt aus.</li>
</ul>
<div class="hinweis">
  <b>Reihenfolge-Sperre:</b> Ein Label unter dem Versionsfeld zeigt, ob
  „Version aktualisieren" in diesem Durchlauf schon gelaufen ist (✓/⚠). Wird
  versucht zu committen/pushen, ohne dass zuvor die Version aktualisiert wurde,
  fragt die App zur Sicherheit nach – so wird die falsche Reihenfolge
  <b>„erst Push, dann Commit, dann Version"</b> verhindert. Bei einem reinen
  PKGBUILD-Fix ohne Versionswechsel kann trotzdem bestätigt werden.
</div>

<h2>7. Update-Assistent</h2>
<p>Über das Menü <b>„Assistenten → Update-Assistent..."</b> führt ein geführter
Dialog Schritt für Schritt durch ein komplettes Update, in der richtigen
Reihenfolge – die Buttons zum Weitergehen sind erst aktiv, wenn der jeweilige
Schritt erledigt ist.</p>
<h3>Ablauf</h3>
<ol>
  <li><b>Startseite:</b> Auswahl, ob am Ende ein GitHub-Release erstellt und/oder
      das verknüpfte AUR-Paket aktualisiert werden soll.</li>
  <li><b>Neue Version:</b> zeigt die aktuell erkannte Version (letztes
      GitHub-Release bzw. aktuelle PKGBUILD-Version) und schlägt automatisch
      eine neue Version vor. Über <b>„+ Patch"</b>, <b>„+ Minor"</b> und
      <b>„+ Major"</b> lässt sie sich per Klick hochzählen (nach dem Schema
      Major.Minor.Patch); alternativ manuell eingeben. Diese eine Version wird
      danach automatisch als Tag-Vorschlag fürs Release und als
      <code>pkgver</code>-Vorschlag fürs AUR-Paket verwendet.</li>
  <li><b>Commit</b> (GitHub) → <b>Push</b> (GitHub) → optional
      <b>Release erstellen</b> → optional <b>AUR-Version aktualisieren</b> →
      optional <b>AUR Commit && Push</b> → Zusammenfassung.</li>
</ol>
<div class="hinweis">
  Wird der Assistent mitten im Ablauf geschlossen, obwohl noch Schritte offen
  sind, warnt er davor – sonst kann z.B. eine lokal geänderte, aber nie
  gepushte AUR-Version unbemerkt liegen bleiben.
</div>

<h2>8. Häufige Fehlermeldungen</h2>
<h3>„Need to specify how to reconcile divergent branches"</h3>
<p>Lokaler und Remote-Branch haben eine unterschiedliche Commit-Historie.
Führe zuerst einen <b>Pull</b> aus.</p>
<h3>„rejected (non-fast-forward)"</h3>
<p>GitHub hat Commits, die lokal fehlen (z.B. direkte Änderungen auf der Weboberfläche).
Erst <b>Pull</b>, dann erneut <b>Push</b>.</p>
<h3>„Keine Änderungen zum Committen"</h3>
<p>Es gibt nichts zu committen. Mögliche Ursachen: falscher Ordner geladen,
Dateien noch nicht gespeichert, oder durch <code>.gitignore</code> ausgeschlossen.</p>
<h3>„Token ungültig / 401"</h3>
<p>Der Token ist abgelaufen oder falsch. Neuen Token auf GitHub erstellen und eintragen.</p>
<h3>„Noch nicht alles gepusht" (beim Release erstellen)</h3>
<p>Das lokal geladene Repository hat noch uncommittete oder ungepushte Änderungen,
die im geplanten Release fehlen würden. Erst <b>Commit</b> und <b>Push</b>,
dann Release erstellen – oder bewusst trotzdem fortfahren.</p>
<h3>„Version noch nicht aktualisiert" (im AUR-Tab)</h3>
<p>Es wurde versucht, zum AUR zu committen/pushen, ohne dass zuvor
<b>„Version aktualisieren"</b> gelaufen ist. Meist ein Zeichen für eine
vertauschte Reihenfolge – ausser es handelt sich bewusst um einen reinen
PKGBUILD-Fix ohne Versionswechsel.</p>
        """,

        # ---- Dialog: Über ----
        "dlg_about_title": "Über GitHub Repository Manager",
        "about_app_title": "GitHub Repository Manager",
        "about_version": "Version 1.0.7",
        "about_author_block": (
            "<b>Autor:</b> Jürg Rechsteiner<br>"
            "<b>Website:</b> <a href='https://www.computer-experte.ch'>computer-experte.ch</a><br>"
            "<b>Region:</b> St. Gallen / Thurgau"
        ),
        "about_desc": (
            "<br><i>Ein PyQt6-basierter GitHub Repository Manager<br>"
            "für Linux – entwickelt mit Python und GitPython.</i>"
        ),

        # ---- Hauptfenster: Titel / Menü ----
        "main_window_title": "GitHub Repository Manager 1.07",
        "menu_help": "&Hilfe",
        "menu_action_manual": "&Benutzerhandbuch",
        "menu_action_manual_tooltip": (
            "Öffnet das vollständige Benutzerhandbuch mit Erklärungen zu "
            "Login, Repository-Verwaltung, Commit/Push/Pull, Release-"
            "Erstellung, dem AUR-Tab und dem Update-Assistenten sowie einer "
            "Liste häufiger Fehlermeldungen."
        ),
        "menu_action_about": "&Über...",
        "menu_action_about_tooltip": (
            "Zeigt Versionsnummer, Autor und Kontaktinformationen zu dieser "
            "Anwendung."
        ),
        "menu_language": "&Sprache",
        "menu_language_item_tooltip": (
            "Wechselt die Sprache der Benutzeroberfläche sofort auf {language} "
            "– kein Neustart nötig."
        ),

        # ---- Tabs ----
        "tab_github": "GitHub",
        "tab_aur": "AUR",

        # ---- Login ----
        "login_group_title": "GitHub Login",
        "login_username_label": "Benutzername:",
        "login_username_placeholder": "GitHub-Benutzername",
        "login_username_tooltip": "Gib deinen GitHub-Benutzernamen ein",
        "login_token_label": "Personal Access Token:",
        "login_token_placeholder": "ghp_...",
        "login_token_tooltip": "Gib deinen Personal Access Token (PAT) ein.",
        "btn_connect": "Verbinden",
        "btn_connect_tooltip": "Mit GitHub verbinden",
        "btn_check_token": "Token prüfen",
        "btn_check_token_tooltip": "Prüft, ob der Token gültig ist",
        "btn_create_token": "Neuen Token erstellen",
        "btn_create_token_tooltip": "Öffnet GitHub-Seite zum Erstellen eines Tokens",

        # ---- Repository-Liste ----
        "repolist_group_title": "Repositorys",
        "repolist_tooltip": "Liste aller GitHub-Repositories",
        "btn_new_repo": "Neues Repository",
        "btn_new_repo_tooltip": "Erstellt ein neues Repository auf GitHub",
        "btn_delete_repo": "Repository löschen",
        "btn_delete_repo_tooltip": "Löscht das ausgewählte Repository",
        "btn_refresh": "Aktualisieren",
        "btn_refresh_tooltip": "Aktualisiert die Repository-Liste",

        # ---- Lokales Repository ----
        "local_group_title": "Lokales Repository",
        "local_default_folder_label": "Standardordner:",
        "local_default_folder_placeholder": "Kein Standardordner gesetzt",
        "btn_set_default": "Als Standard setzen",
        "btn_set_default_tooltip": "Setzt aktuellen Ordner als Standard",
        "btn_change_default": "Ändern",
        "btn_change_default_tooltip": "Wählt neuen Standardordner",
        "btn_clone": "Repository klonen",
        "btn_clone_tooltip": "Klonen des ausgewählten Repositories in den Standardordner",
        "btn_init": "Neues Repo init",
        "btn_init_tooltip": (
            "Erstellt ein neues lokales Git-Repository (git init) und verknüpft "
            "es mit dem oben in der Liste ausgewählten GitHub-Repository"
        ),
        "btn_browse": "Ordner auswählen",
        "btn_browse_tooltip": "Wählt einen lokalen Ordner als Git-Repository",
        "local_loaded_label": "Geladen:",
        "local_loaded_placeholder": "Kein Repository geladen",
        "local_commit_msg_label": "Commit-Nachricht:",
        "local_commit_msg_placeholder": "Änderungen beschreiben...",
        "btn_commit": "Commit",
        "btn_commit_tooltip": "Fügt alle Änderungen hinzu und erstellt Commit",
        "btn_push": "Push zu GitHub",
        "btn_push_tooltip": "Pusht Commits zu GitHub",
        "btn_pull": "Pull von GitHub",
        "btn_pull_tooltip": "Holt Änderungen von GitHub",
        "btn_link_remote": "Mit GitHub verknüpfen",
        "btn_release": "Release erstellen",
        "btn_release_tooltip": "Erstellt ein neues GitHub-Release (mit Tag) für das ausgewählte Repository",
        "btn_link_remote_tooltip": (
            "Setzt den Remote 'origin' des geladenen lokalen Repositories auf "
            "das oben in der Liste ausgewählte GitHub-Repository"
        ),
        "branch_label_empty": "Branch: –",
        "branch_label": "Branch: {branch}",
        "btn_check_status": "Status prüfen",
        "btn_check_status_tooltip": (
            "Prüft den aktuellen Repository-Zustand (Änderungen, offener Merge, "
            "Push/Pull-Bedarf) und schlägt die nächste sinnvolle Aktion vor"
        ),
        "btn_suggested_action": "Empfohlene Aktion ausführen",
        "btn_suggested_action_tooltip": "Führt die oben angezeigte empfohlene Aktion aus",

        # ---- Status-Empfehlung ----
        "recommendation_none": "Noch keine Analyse durchgeführt",
        "recommendation_error": "Statusprüfung fehlgeschlagen",
        "recommendation_merge_pending": "Offener Merge muss zuerst abgeschlossen werden",
        "recommendation_commit_needed": "Commit empfohlen: {count} Änderung(en) vorhanden",
        "recommendation_no_remote": "Kein Remote verknüpft – Push/Pull nicht möglich",
        "recommendation_no_auth": "Nicht angemeldet – Push/Pull-Status kann nicht geprüft werden",
        "recommendation_push_needed": "Push empfohlen: {ahead} Commit(s) voraus",
        "recommendation_pull_needed": "Pull empfohlen: {behind} Commit(s) hinterher",
        "recommendation_diverged": (
            "Branches divergieren: {ahead} eigene(r) / {behind} entfernte(r) Commit(s) "
            "– zuerst Pull empfohlen"
        ),
        "recommendation_up_to_date": "Alles aktuell – keine Aktion nötig",
        "action_btn_resolve_merge": "Merge abschließen",
        "action_btn_commit": "Commit ausführen",
        "action_btn_push": "Push ausführen",
        "action_btn_pull": "Pull ausführen",

        # ---- AUR-Tab ----
        "aur_group_title": "AUR-Paket aktualisieren",
        "aur_intro_text": (
            "Aktualisiert ein lokal bereits geklontes AUR-Paket: setzt die neue "
            "Version (und pkgrel) in der PKGBUILD, lädt die Quellen zur "
            "Prüfsummen-Berechnung neu herunter (updpkgsums), erzeugt die "
            ".SRCINFO neu und pusht per Commit zum AUR."
        ),
        "aur_folder_label": "AUR-Ordner:",
        "aur_folder_placeholder": "Kein AUR-Ordner geladen",
        "btn_aur_browse": "Ordner auswählen",
        "btn_aur_browse_tooltip": (
            "Wählt den lokalen Klon eines AUR-Repositories "
            "(z.B. von ssh://aur@aur.archlinux.org/<paket>.git)"
        ),
        "btn_aur_new_package": "Neues AUR-Paket erstellen",
        "btn_aur_new_package_tooltip": (
            "Legt ein neues, noch nicht existierendes AUR-Paket an: erstellt "
            "einen Ordner mit PKGBUILD-Grundgerüst, initialisiert ein "
            "Git-Repository und setzt den AUR-Remote "
            "(ssh://aur@aur.archlinux.org/<paket>.git). Veröffentlicht wird "
            "das Paket erst mit dem ersten erfolgreichen Push."
        ),

        # ---- Neues AUR-Paket (Dialog) ----
        "dlg_newaur_title": "Neues AUR-Paket",
        "dlg_newaur_intro": (
            "Erstellt ein PKGBUILD-Grundgerüst für ein neues AUR-Paket, das "
            "an ein GitHub-Repository gekoppelt ist. Nach dem Erstellen "
            "kannst du es wie gewohnt im AUR-Tab bearbeiten, mit "
            "„Version aktualisieren\" die Prüfsummen berechnen und mit "
            "„Commit && Push\" auf AUR veröffentlichen."
        ),
        "dlg_newaur_pkgname_label": "Paketname:",
        "dlg_newaur_pkgname_placeholder": "z.B. mein-tool (nur a-z, 0-9, @._+-)",
        "dlg_newaur_pkgver_label": "Startversion:",
        "dlg_newaur_pkgdesc_label": "Beschreibung:",
        "dlg_newaur_pkgdesc_placeholder": "Kurze Beschreibung des Pakets",
        "dlg_newaur_url_label": "Projekt-URL:",
        "dlg_newaur_url_tooltip": (
            "Die URL des GitHub-Repositorys (z.B. https://github.com/name/repo).\n"
            "Wird zweifach verwendet: als \"url=\"-Feld im PKGBUILD und als Basis "
            "für die automatisch erzeugte Quell-URL zum jeweiligen Versions-Tag "
            "(<URL>/archive/refs/tags/v<Version>.tar.gz). Es muss also das echte "
            "GitHub-Repo sein, nicht nur eine allgemeine Projekt-Homepage."
        ),
        "dlg_newaur_license_label": "Lizenz:",
        "dlg_newaur_license_custom_option": "Benutzerdefiniert / SPDX-Ausdruck manuell eingeben…",
        "dlg_newaur_license_custom_placeholder": "z.B. LicenseRef-MeineLizenz oder eigener SPDX-Ausdruck",
        "dlg_newaur_arch_label": "Architektur(en):",
        "dlg_newaur_arch_placeholder": "z.B. x86_64 oder any (kommagetrennt)",
        "dlg_newaur_depends_label": "Abhängigkeiten:",
        "dlg_newaur_depends_placeholder": "kommagetrennt, z.B. python, git",
        "dlg_newaur_hint": (
            "Hinweis: Die Quelle im PKGBUILD verweist auf einen GitHub-Tag "
            "(z.B. v1.0.0). Dieser Tag muss auf GitHub existieren, bevor "
            "„Version aktualisieren\" die Prüfsummen berechnen kann – lege "
            "dafür vorher ein passendes Release an. Den generierten "
            "package()-Abschnitt solltest du danach ans Projekt anpassen."
        ),

        # ---- Neues AUR-Paket: Meldungen ----
        "dlg_choose_aur_base_folder": "Basisordner für AUR-Pakete wählen",
        "dlg_choose_aur_location": "Speicherort für den neuen AUR-Paketordner wählen",
        "dlg_aur_folder_name_title": "Ordnername",
        "dlg_aur_folder_name_label": "Name des neuen Ordners:",
        "msg_aur_foldername_invalid": "Ungültiger Ordnername.",
        "msg_aur_pkgname_invalid": (
            "Ungültiger Paketname. Erlaubt sind Kleinbuchstaben, Ziffern "
            "und @ . _ + - (muss mit einem alphanumerischen Zeichen beginnen)."
        ),
        "msg_aur_url_required": "Bitte eine Projekt-URL angeben.",
        "msg_aur_folder_exists": "Der Ordner „{folder}\" existiert bereits.",
        "status_aur_creating_package": "Erstelle AUR-Paket '{pkgname}'...",
        "status_aur_creating_package_failed": "Erstellen des AUR-Pakets fehlgeschlagen",
        "status_aur_package_created": "AUR-Paket '{pkgname}' erstellt",
        "msg_aur_package_created_title": "AUR-Paket angelegt",
        "msg_aur_package_created_text": (
            "Das Grundgerüst für „{pkgname}\" (Version {version}) wurde "
            "lokal angelegt und geladen.\n\n"
            "Nächste Schritte:\n"
            "1. Passe bei Bedarf den package()-Abschnitt in der PKGBUILD an.\n"
            "2. Stelle sicher, dass auf GitHub ein Release/Tag für diese "
            "Version existiert.\n"
            "3. Klicke auf „Version aktualisieren\", um Prüfsummen und "
            ".SRCINFO zu erzeugen.\n"
            "4. Klicke auf „Commit && Push\", um das Paket erstmalig auf "
            "AUR zu veröffentlichen (dafür muss ein SSH-Schlüssel bei "
            "deinem AUR-Konto hinterlegt sein)."
        ),
        "msg_aur_package_create_error": "Fehler beim Erstellen des AUR-Pakets:\n{error}",
        "msg_aur_offer_title": "AUR-Paket anlegen?",
        "msg_aur_offer_text": (
            "Repository „{name}\" wurde erstellt.\n\n"
            "Möchtest du dafür gleich auch ein neues AUR-Paket-Grundgerüst "
            "anlegen?"
        ),

        "aur_info_none": "Kein AUR-Paket geladen",
        "aur_info": "Paket: {pkgname} – aktuell {version}-{rel}",
        "aur_version_label": "Neue Version:",
        "aur_version_placeholder": "z.B. 2.4.1",
        "btn_aur_update": "Version aktualisieren",
        "btn_aur_update_tooltip": (
            "Setzt pkgver/pkgrel in der PKGBUILD, aktualisiert die Prüfsummen "
            "(updpkgsums) und erzeugt die .SRCINFO neu"
        ),
        "aur_commit_msg_label": "Commit-Nachricht:",
        "aur_commit_msg_placeholder": "Commit-Nachricht für den AUR-Push...",
        "aur_commit_msg_default": "Update to {version}",
        "btn_aur_commit_push": "Commit && Push zum AUR",
        "btn_aur_commit_push_tooltip": "Committet PKGBUILD/.SRCINFO und pusht zum AUR",

        # ---- AUR-Tab: Status-Empfehlung ----
        "btn_aur_check_status": "Status prüfen",
        "btn_aur_check_status_tooltip": (
            "Prüft den Zustand des AUR-Ordners (Änderungen, offener Merge, "
            "Push/Pull-Bedarf) und schlägt die nächste Aktion vor"
        ),
        "btn_aur_suggested_action": "Empfohlene Aktion ausführen",
        "btn_aur_suggested_action_tooltip": "Führt die oben angezeigte empfohlene Aktion aus",
        "aur_recommendation_none": "Noch keine Analyse durchgeführt",
        "aur_recommendation_error": "Statusprüfung fehlgeschlagen",
        "aur_recommendation_merge_pending": "Offener Merge muss zuerst abgeschlossen werden",
        "aur_recommendation_commit_needed": "Commit empfohlen: {count} Änderung(en) vorhanden",
        "aur_recommendation_new_files": (
            "Versionierung empfohlen: {count} neue Datei(en) noch nicht zu Git hinzugefügt"
        ),
        "aur_recommendation_artifacts_found": (
            "Aufräumen empfohlen: {count} Build-Artefakt(e) gefunden (z.B. heruntergeladene "
            "Quell-Tarballs) – gehören nicht ins Git-Repo"
        ),
        "aur_recommendation_no_remote": "Kein Remote verknüpft – Push/Pull nicht möglich",
        "aur_recommendation_push_needed": "Push zum AUR empfohlen: {ahead} Commit(s) voraus",
        "aur_recommendation_pull_needed": "Pull vom AUR empfohlen: {behind} Commit(s) hinterher",
        "aur_recommendation_diverged": (
            "Branches divergieren: {ahead} eigene(r) / {behind} entfernte(r) Commit(s) "
            "– zuerst Pull empfohlen"
        ),
        "aur_recommendation_up_to_date": "Alles aktuell – keine Aktion nötig",
        "aur_action_btn_resolve_merge": "Merge abschließen",
        "aur_action_btn_commit": "Commit ausführen",
        "aur_action_btn_add_files": "Datei(en) versionieren",
        "aur_action_btn_cleanup": "Artefakte löschen",
        "aur_action_btn_push": "Push ausführen",
        "aur_action_btn_pull": "Pull ausführen",

        # ---- AUR-Tab: Reihenfolge-Sperre (Version -> Commit -> Push) ----
        "aur_step_indicator_done": "✓ Version in diesem Durchlauf bereits aktualisiert",
        "aur_step_indicator_pending": (
            "⚠ Version in diesem Durchlauf noch nicht aktualisiert – wird vor "
            "Commit/Push abgefragt"
        ),
        "msg_aur_order_warning_title": "Version noch nicht aktualisiert",
        "msg_aur_order_warning_text": (
            "Du hast in diesem Durchlauf noch nicht auf „Version aktualisieren“ "
            "geklickt.\n\nDie empfohlene Reihenfolge ist:\n"
            "1. Version aktualisieren\n2. Commit\n3. Push zum AUR\n\n"
            "Trotzdem jetzt committen/pushen? (z.B. sinnvoll bei einem reinen "
            "PKGBUILD-Fix ohne Versionswechsel)"
        ),

        # ---- Update-Assistent ----
        "menu_tools": "&Assistenten",
        "menu_action_update_assistant": "Update-Assistent...",
        "menu_action_update_assistant_tooltip": (
            "Öffnet einen geführten Dialog, der Schritt für Schritt durch ein "
            "komplettes Update führt: Commit → Push (GitHub) → optional ein "
            "neues Release erstellen → optional das verknüpfte AUR-Paket "
            "aktualisieren, committen und pushen. Schlägt dabei auch gleich "
            "eine neue Versionsnummer vor. Jeder Schritt muss erledigt sein, "
            "bevor es weitergeht – eine falsche Reihenfolge ist damit "
            "ausgeschlossen."
        ),
        "wizard_title": "Update-Assistent",
        "wizard_btn_back": "Zurück",
        "wizard_btn_next": "Weiter",
        "wizard_btn_close": "Abbrechen",
        "wizard_btn_finish": "Fertig",
        "wizard_btn_skip_step": "Diesen Schritt überspringen",
        "wizard_btn_run_commit": "Committen",
        "wizard_btn_run_push": "Push zu GitHub",
        "wizard_btn_run_release": "Release erstellen...",
        "wizard_btn_run_aur_version": "Version aktualisieren",
        "wizard_btn_run_aur_commit_push": "Commit && Push zum AUR",
        "wizard_progress_intro": "Schritt 0 von n – Einrichtung",
        "wizard_progress_step": "Schritt {current} von {total}",
        "wizard_intro_text": (
            "Dieser Assistent führt dich in der richtigen Reihenfolge durch "
            "ein komplettes Update: zuerst committen und zu GitHub pushen, "
            "danach optional ein GitHub-Release erstellen und optional das "
            "verknüpfte AUR-Paket aktualisieren. Jeder Schritt muss erledigt "
            "sein, bevor es weitergeht."
        ),
        "wizard_intro_no_github": (
            "Kein lokales GitHub-Repository geladen – Commit/Push werden "
            "übersprungen."
        ),
        "wizard_intro_no_aur": "Kein AUR-Ordner geladen – dieser Teil ist deaktiviert.",
        "wizard_check_release": "Am Ende ein neues GitHub-Release erstellen",
        "wizard_check_aur": "Verknüpftes AUR-Paket ebenfalls aktualisieren",
        "wizard_version_group_title": "Neue Version",
        "wizard_version_checking": "Prüfe letzten GitHub-Release...",
        "wizard_version_current_github": "Letztes GitHub-Release: {version}",
        "wizard_version_no_releases": "Noch kein GitHub-Release gefunden.",
        "wizard_version_current_aur": "Aktuell in der PKGBUILD: {version}",
        "wizard_new_version_label": "Neue Version:",
        "wizard_new_version_placeholder": "z.B. 1.3.0 oder v1.3.0",
        "wizard_btn_bump_patch": "+ Patch",
        "wizard_btn_bump_minor": "+ Minor",
        "wizard_btn_bump_major": "+ Major",
        "wizard_version_manual_hint": (
            "Aktuelle Version folgt keinem X.Y.Z-Schema – bitte die neue "
            "Version manuell eingeben."
        ),
        "msg_wizard_version_required": (
            "Bitte eine neue Version eingeben (wird für Release-Tag und/"
            "oder AUR-pkgver verwendet)."
        ),
        "wizard_close_confirm_title": "Ablauf noch nicht fertig",
        "wizard_close_confirm_text": (
            "Es sind noch nicht alle Schritte abgeschlossen (z.B. ein Push). "
            "Lokale Änderungen wie eine bereits geänderte PKGBUILD-Version "
            "wären dann noch nicht committet/gepusht.\n\n"
            "Wirklich schließen, ohne fertig zu sein?"
        ),
        "wizard_no_local_repo": "Kein lokales GitHub-Repository geladen.",
        "wizard_no_aur_repo": "Kein AUR-Ordner geladen.",
        "wizard_step_nothing_to_do": "✓ Nichts zu tun – dieser Schritt ist bereits erfüllt.",
        "wizard_step_done": "✓ Erledigt.",
        "wizard_commit_dirty_count": "{count} Änderung(en) noch nicht committet.",
        "wizard_push_ahead_count": "{ahead} Commit(s) noch nicht gepusht.",
        "wizard_push_diverged": (
            "⚠ Lokale und entfernte Commits weichen voneinander ab. Bitte "
            "zuerst im GitHub-Tab pullen/mergen, dann diesen Assistenten "
            "erneut öffnen."
        ),
        "wizard_push_merge_pending": (
            "⚠ Es ist noch ein Merge offen. Bitte zuerst im GitHub-Tab "
            "abschließen, dann diesen Assistenten erneut öffnen."
        ),
        "wizard_push_commit_needed": (
            "⚠ Es gibt wieder uncommittete Änderungen. Bitte zurückgehen "
            "und zuerst committen."
        ),
        "wizard_push_blocked": "⚠ Push aktuell nicht möglich (Status: {state}).",
        "wizard_check_failed": "Status konnte nicht geprüft werden: {error}",
        "wizard_step_commit_title": "1. GitHub: Änderungen committen",
        "wizard_step_push_title": "2. GitHub: Zu GitHub pushen",
        "wizard_step_release_title": "3. GitHub: Release erstellen",
        "wizard_step_aur_version_title": "4. AUR: Version aktualisieren",
        "wizard_step_aur_commit_push_title": "5. AUR: Commit && Push",
        "wizard_step_summary_title": "Zusammenfassung",
        "wizard_release_info": (
            "Öffnet den bekannten Release-Dialog. Der Tag sollte zum Stand "
            "passen, den du gerade gepusht hast."
        ),
        "wizard_aur_current_version": "Aktuell in der PKGBUILD: {version}",
        "wizard_summary_text": "Der Assistent ist durchgelaufen:",

        # ---- Statusleiste ----
        "status_ready": "Bereit",
        "status_token_saved_days": "Token gespeichert vor {days} Tag(en)",
        "status_checking_token": "Prüfe Token...",
        "status_token_valid": "Token gültig (Benutzer: {username})",
        "status_token_valid_days": "Token gültig (Benutzer: {username}) – gespeichert vor {days} Tag(en)",
        "status_token_invalid": "Token ist ungültig oder abgelaufen",
        "status_connecting": "Verbinde...",
        "status_connected_as": "Verbunden als {username}",
        "status_connect_failed": "Verbindung fehlgeschlagen",
        "status_loading_repos": "Lade Repositorys neu...",
        "status_repos_refreshed": "Repositorys aktualisiert",
        "status_refresh_failed": "Aktualisierung fehlgeschlagen",
        "status_creating_repo": "Erstelle Repository '{name}'...",
        "status_repo_created": "Repository '{name}' erstellt",
        "status_create_failed": "Erstellen fehlgeschlagen",
        "status_deleting_repo": "Lösche Repository '{name}'...",
        "status_repo_deleted": "Repository gelöscht",
        "status_delete_failed": "Löschen fehlgeschlagen",
        "status_creating_release": "Erstelle Release '{tag}'...",
        "status_release_created": "Release '{tag}' erstellt",
        "status_release_failed": "Release-Erstellung fehlgeschlagen",
        "status_default_folder_set": "Standardordner gesetzt: {folder}",
        "status_default_folder_changed": "Standardordner geändert: {folder}",
        "status_local_repo_loaded_no_remote": (
            "Lokales Repository geladen: {folder} – kein Remote konfiguriert. "
            "Wähle oben ein GitHub-Repository aus und klicke auf "
            "'Mit GitHub verknüpfen'."
        ),
        "status_local_repo_loaded": "Lokales Repository geladen: {folder}",
        "status_linked_to_repo": "Mit GitHub-Repository '{full_name}' verknüpft",
        "status_cloning": "Klone {name}...",
        "status_cloned": "Repository geklont: {path}",
        "status_clone_failed": "Klonen fehlgeschlagen",
        "status_init_done": "Neues Repository initialisiert und mit '{full_name}' verknüpft: {path}",
        "status_commit_in_progress": "Commit wird ausgeführt...",
        "status_commit_success": "Commit erfolgreich: {hash}",
        "status_commit_failed": "Commit fehlgeschlagen",
        "status_push_cancelled": "Push abgebrochen",
        "status_pushing": "Push wird ausgeführt...",
        "status_push_up_to_date": "Push: Branch '{branch}' war bereits aktuell – keine neuen Commits",
        "status_push_success_renamed": "Push erfolgreich: '{local}' → GitHub-Branch '{remote}'",
        "status_push_success": "Push erfolgreich (Branch: {branch})",
        "status_push_failed": "Push fehlgeschlagen",
        "status_pulling": "Pull wird ausgeführt...",
        "status_pull_success": "Pull erfolgreich von '{branch}'",
        "status_pull_failed": "Pull fehlgeschlagen",
        "status_pull_cancelled": "Pull abgebrochen",
        "status_push_needs_pull": "Push nicht möglich: Remote-Branch enthält neuere Commits",
        "status_merge_committed": "Offener Merge committet",
        "status_merge_aborted": "Offener Merge verworfen",
        "status_checking_repo_state": "Prüfe Repository-Status...",
        "status_check_done": "Statusprüfung abgeschlossen",
        "status_check_failed": "Statusprüfung fehlgeschlagen",
        "status_enter_commit_message": "Bitte zuerst eine Commit-Nachricht eingeben",
        "status_aur_folder_loaded": "AUR-Ordner geladen: {folder}",
        "status_aur_updating": "Aktualisiere PKGBUILD und Prüfsummen...",
        "status_aur_update_done": "PKGBUILD aktualisiert auf Version {version}",
        "status_aur_update_failed": "Aktualisierung der PKGBUILD fehlgeschlagen",
        "status_aur_pushing": "Push zum AUR wird ausgeführt...",
        "status_aur_push_success": "Push zum AUR erfolgreich",
        "status_aur_push_failed": "Push zum AUR fehlgeschlagen",
        "status_aur_checking_repo_state": "Prüfe AUR-Repository-Status...",
        "status_aur_check_done": "AUR-Statusprüfung abgeschlossen",
        "status_aur_check_failed": "AUR-Statusprüfung fehlgeschlagen",
        "status_aur_pulling": "Pull vom AUR wird ausgeführt...",
        "status_aur_pull_success": "Pull vom AUR erfolgreich",
        "status_aur_pull_failed": "Pull vom AUR fehlgeschlagen",
        "status_aur_files_added": "Neue Datei(en) zu Git hinzugefügt",
        "status_aur_cleanup_done": "Build-Artefakte gelöscht",

        # ---- Dateidialoge ----
        "dlg_choose_default_folder": "Standardordner auswählen",
        "dlg_choose_local_repo_folder": "Lokales Git-Repository auswählen",

        # ---- Meldungsfenster ----
        "msg_error_title": "Fehler",
        "msg_token_check_title": "Token prüfen",
        "msg_token_check_empty": "Kein Token eingegeben.",
        "msg_token_invalid_title": "Token ungültig",
        "msg_token_invalid_text": "Der Token ist ungültig. Möchtest du das Feld leeren?",
        "msg_token_check_error": "Fehler bei der Token-Prüfung:\n{error}",
        "msg_create_token_title": "Token erstellen",
        "msg_create_token_text": (
            "Die GitHub-Seite wurde geöffnet.\n\n"
            "1. Klicke auf 'Generate new token' (classic)\n"
            "2. Wähle ein Ablaufdatum\n"
            "3. Wähle die Berechtigung 'repo'\n"
            "4. Token kopieren und hier einfügen"
        ),
        "msg_username_token_required": "Bitte Benutzername und Token eingeben.",
        "msg_connect_error_title": "Verbindungsfehler",
        "msg_connect_error_text": "Fehler bei der Verbindung:\n{error}",
        "msg_repo_name_empty": "Der Repository-Name darf nicht leer sein.",
        "msg_create_error": "Fehler beim Erstellen:\n{error}",
        "msg_delete_confirm_title": "Repository löschen",
        "msg_delete_confirm_text": "Soll das Repository '{name}' wirklich gelöscht werden?",
        "msg_delete_error": "Fehler beim Löschen:\n{error}",
        "msg_no_git_repo_title": "Kein Git-Repository",
        "msg_no_git_repo_text": "'{folder}' ist kein Git-Repository.",
        "msg_load_error": "Fehler beim Laden:\n{error}",
        "msg_no_remote_title": "Kein Remote konfiguriert",
        "msg_no_remote_text": (
            "'{folder}' wurde geladen, ist aber noch nicht mit einem "
            "GitHub-Repository verknüpft (kein 'origin' Remote).\n\n"
            "Wähle oben in der Liste 'Repositorys' das passende GitHub-"
            "Repository aus und klicke dann auf 'Mit GitHub verknüpfen', "
            "um Push/Pull zu aktivieren."
        ),
        "msg_no_repo_title": "Kein Repository",
        "msg_load_local_first": "Lade zuerst ein lokales Repository.",
        "msg_no_github_repo_title": "Kein GitHub-Repository ausgewählt",
        "msg_no_github_repo_text_link": (
            "Wähle zuerst oben in der Liste 'Repositorys' das GitHub-"
            "Repository aus, mit dem verknüpft werden soll."
        ),
        "msg_no_github_repo_text_release": (
            "Wähle zuerst oben in der Liste 'Repositorys' das GitHub-"
            "Repository aus, für das ein Release erstellt werden soll."
        ),
        "msg_release_tag_empty": "Der Tag darf nicht leer sein (z.B. v1.0.0).",
        "msg_release_created_title": "Release erstellt",
        "msg_release_created_text": "Release '{tag}' wurde erfolgreich erstellt.\n\n{url}",
        "msg_release_error": "Fehler beim Erstellen des Release:\n{error}",

        # ---- GitHub-Tab: Reihenfolge-Sperre (Commit -> Push -> Release) ----
        "msg_release_order_warning_title": "Noch nicht alles gepusht",
        "msg_release_order_warning_commit": (
            "Im lokal geladenen Repository gibt es noch uncommittete "
            "Änderungen. Ein GitHub-Release taggt den Stand, der aktuell auf "
            "GitHub liegt – diese Änderungen wären darin NICHT enthalten.\n\n"
            "Empfohlene Reihenfolge:\n1. Commit\n2. Push\n3. Release erstellen\n\n"
            "Trotzdem jetzt ein Release erstellen?"
        ),
        "msg_release_order_warning_push": (
            "Im lokal geladenen Repository gibt es committete, aber noch "
            "nicht gepushte Änderungen. Ein GitHub-Release taggt den Stand, "
            "der aktuell auf GitHub liegt – diese Änderungen wären darin "
            "NICHT enthalten.\n\nEmpfohlene Reihenfolge:\n1. Commit\n2. Push\n"
            "3. Release erstellen\n\nTrotzdem jetzt ein Release erstellen?"
        ),
        "msg_release_order_warning_merge": (
            "Im lokal geladenen Repository ist noch ein Merge offen. Bitte "
            "zuerst im GitHub-Tab abschließen, committen und pushen, bevor "
            "ein Release erstellt wird.\n\nTrotzdem jetzt ein Release "
            "erstellen?"
        ),
        "msg_connect_first": "Bitte verbinde dich zuerst.",
        "msg_linked_title": "Verknüpft",
        "msg_linked_text": (
            "Das lokale Repository ist nun mit "
            "'{full_name}' verknüpft.\n\n"
            "Falls das GitHub-Repository bereits Inhalte hat und das lokale "
            "Repository noch keine gemeinsame Historie hat, zuerst "
            "'Pull von GitHub' ausführen, bevor gepusht wird."
        ),
        "msg_link_error": "Fehler beim Verknüpfen:\n{error}",
        "msg_no_default_folder_title": "Kein Standardordner",
        "msg_no_default_folder_text": "Setze zuerst einen Standardordner.",
        "msg_folder_exists_title": "Ordner existiert",
        "msg_folder_exists_text": "Der Ordner '{folder}' existiert. Überschreiben?",
        "msg_clone_error": "Fehler beim Klonen:\n{error}",
        "msg_no_github_repo_text_init": (
            "Wähle zuerst oben in der Liste 'Repositorys' das GitHub-"
            "Repository aus, mit dem das neue lokale Repository verknüpft "
            "werden soll.\n\n"
            "Falls es noch nicht existiert, lege es zuerst über "
            "'Neues Repository' an."
        ),
        "msg_repo_not_empty_title": "Repository ist nicht leer",
        "msg_repo_not_empty_text": (
            "'{name}' enthält auf GitHub bereits Dateien.\n"
            "Ein neues lokales Repository per 'git init' hat eine eigene, "
            "unabhängige Historie – der erste Push würde fehlschlagen oder "
            "einen Force-Push erfordern.\n\n"
            "Empfehlung: Stattdessen 'Repository klonen' verwenden.\n\n"
            "Trotzdem fortfahren?"
        ),
        "msg_new_repo_dialog_title": "Neues Repository",
        "msg_new_repo_dialog_label": "Name des neuen lokalen Ordners:",
        "msg_exists_title": "Existiert",
        "msg_exists_text": "Der Ordner '{folder}' existiert bereits.",
        "msg_init_error": "Fehler beim Initialisieren:\n{error}",
        "msg_no_local_repo": "Kein lokales Repository ausgewählt.",
        "msg_commit_msg_required": "Bitte eine Commit-Nachricht eingeben.",
        "msg_commit_error": "Fehler beim Commit:\n{error}",
        "msg_no_token_user": "Kein Token oder Benutzer. Bitte verbinde dich erneut.",
        "msg_branch_mismatch_title": "Branch-Abweichung",
        "msg_branch_mismatch_text": (
            "Der lokale Branch heißt '{local}', der Standard-Branch "
            "dieses Repositories auf GitHub ist aber '{default}'.\n\n"
            "Wohin soll gepusht werden?"
        ),
        "btn_push_to_default": "Auf '{branch}' pushen (empfohlen)",
        "btn_push_to_local": "Auf '{branch}' pushen",
        "btn_cancel": "Abbrechen",
        "msg_up_to_date_title": "Bereits aktuell",
        "msg_up_to_date_text": (
            "Es gab keine neuen Commits, die nach '{branch}' übertragen "
            "werden konnten.\n\nWurden die Änderungen vorher committet?"
        ),
        "msg_push_error_pull_question": (
            "Fehler beim Push:\n{error}\n\n"
            "Möchtest du jetzt einen Pull ausführen, um die Remote-Änderungen "
            "zuerst zu holen und danach erneut zu pushen?"
        ),
        "msg_push_error": "Fehler beim Push:\n{error}",
        "msg_pull_error": "Fehler beim Pull:\n{error}",
        "msg_check_status_error": "Fehler bei der Statusprüfung:\n{error}",
        "msg_remote_ahead_title": "Remote ist voraus",
        "msg_remote_ahead_text": (
            "Der Remote-Branch '{branch}' enthält Commits, die lokal "
            "nicht vorhanden sind. Ein Push ist erst nach einem Pull "
            "möglich.\n\nJetzt pullen?"
        ),
        "msg_merge_pending_title": "Unabgeschlossener Merge",
        "msg_merge_pending_text": (
            "Es liegt noch ein nicht abgeschlossener Merge vor (z.B. von "
            "einem vorherigen Pull). Alle Konflikte scheinen bereits gelöst "
            "zu sein – es fehlt nur noch der Abschluss.\n\n"
            "Merge jetzt committen oder verwerfen?"
        ),
        "msg_merge_conflicts_unresolved_text": (
            "Es liegt noch ein nicht abgeschlossener Merge mit ungelösten "
            "Konflikten vor. Bitte die betroffenen Dateien zuerst im "
            "Terminal oder Editor bereinigen (Konfliktmarker <<<<<<<, "
            "=======, >>>>>>> entfernen).\n\n"
            "Alternativ kann der Merge komplett verworfen werden – dabei "
            "gehen alle lokal noch nicht committeten Änderungen aus diesem "
            "Merge verloren."
        ),
        "msg_merge_abort_error": "Fehler beim Verwerfen des Merges:\n{error}",
        "msg_merge_resolve_error": "Fehler beim Abschließen des Merges:\n{error}",
        "btn_merge_commit": "Merge committen",
        "btn_merge_abort": "Merge verwerfen",

        # ---- Fehlermeldungen aus den Hintergrund-Worker-Funktionen ----
        "err_push_no_feedback": (
            "GitHub hat keine Rückmeldung zum Push gesendet. "
            "Es kann nicht bestätigt werden, dass die Änderungen "
            "übertragen wurden."
        ),
        "err_push_rejected": (
            "GitHub hat den Push abgelehnt:\n{summaries}\n\n"
            "Mögliche Ursache: Der Remote-Branch enthält Commits, die "
            "lokal nicht vorhanden sind (z.B. Änderungen über die GitHub-"
            "Weboberfläche). Erst 'Pull von GitHub' ausführen, dann erneut pushen."
        ),
        "err_merge_conflict_unrelated": (
            "Merge-Konflikt beim Zusammenführen der bisher "
            "unabhängigen Historien: dieselben Dateien wurden "
            "lokal und auf GitHub unterschiedlich geändert.\n\n"
            "Bitte im Terminal im Projektordner mit 'git status' "
            "prüfen, Konflikte manuell lösen und anschließend "
            "committen."
        ),
        "err_pull_failed": "Pull fehlgeschlagen:\n{error}",
        "err_merge_conflict": (
            "Merge-Konflikt beim Pull. Bitte im Terminal im "
            "Projektordner mit 'git status' prüfen, Konflikte "
            "manuell lösen und anschließend committen."
        ),
        "err_no_changes_to_commit": (
            "Keine Änderungen zum Committen gefunden.\n"
            "Prüfe, ob im richtigen Ordner gearbeitet wurde und ob die "
            "geänderten Dateien nicht durch .gitignore ausgeschlossen sind."
        ),

        # ---- AUR: Dialoge / Meldungen ----
        "dlg_choose_aur_folder": "Lokalen AUR-Repository-Ordner auswählen",
        "msg_aur_no_pkgbuild": (
            "Im Ordner '{folder}' wurde keine PKGBUILD gefunden. "
            "Bitte den lokalen Klon des AUR-Repositories auswählen "
            "(z.B. von ssh://aur@aur.archlinux.org/<paket>.git)."
        ),
        "msg_aur_no_folder": "Bitte zuerst einen AUR-Ordner auswählen.",
        "msg_aur_version_required": "Bitte eine neue Version eingeben.",
        "msg_aur_version_invalid": "Die Version darf keine Leerzeichen enthalten.",
        "msg_aur_update_error": "Fehler beim Aktualisieren der PKGBUILD:\n{error}",
        "msg_aur_push_success_title": "AUR aktualisiert",
        "msg_aur_push_success_text": "Das AUR-Paket wurde erfolgreich aktualisiert und gepusht.",
        "msg_aur_push_error": "Fehler beim Push zum AUR:\n{error}",
        "msg_aur_after_push_title": "AUR auch aktualisieren?",
        "msg_aur_after_push_text": (
            "GitHub-Push war erfolgreich. Jetzt auch das verknüpfte "
            "AUR-Paket aktualisieren?"
        ),
        "err_aur_updpkgsums_missing": (
            "Das Werkzeug 'updpkgsums' wurde nicht gefunden. Es ist Teil des "
            "Pakets 'pacman-contrib' (z.B. 'sudo pacman -S pacman-contrib')."
        ),
        "err_aur_updpkgsums_failed": "Aktualisieren der Prüfsummen fehlgeschlagen:\n{error}",
        "err_aur_makepkg_missing": (
            "Das Werkzeug 'makepkg' wurde nicht gefunden. Es ist Teil des "
            "Basispakets 'pacman' auf Arch-basierten Systemen."
        ),
        "err_aur_makepkg_failed": "Erzeugen der .SRCINFO fehlgeschlagen:\n{error}",
        "err_aur_no_remote": (
            "Kein Remote ('origin') im AUR-Ordner konfiguriert. "
            "Bitte prüfen, ob der Ordner korrekt von "
            "ssh://aur@aur.archlinux.org/<paket>.git geklont wurde."
        ),
        "msg_aur_check_status_error": "Fehler bei der AUR-Statusprüfung:\n{error}",
        "msg_aur_pull_error": "Fehler beim Pull vom AUR:\n{error}",
        "msg_aur_add_files_title": "Neue Datei(en) versionieren?",
        "msg_aur_add_files_text": (
            "Folgende Datei(en) sind noch nicht Teil des Git-Repos und werden "
            "vermutlich benötigt:\n\n{files}\n\nJetzt zu Git hinzufügen (git add)?"
        ),
        "msg_aur_add_files_error": "Fehler beim Hinzufügen der Datei(en):\n{error}",
        "msg_aur_cleanup_title": "Build-Artefakte löschen?",
        "msg_aur_cleanup_text": (
            "Folgende unversionierte Datei(en)/Ordner wurden vermutlich von "
            "'updpkgsums' oder 'makepkg' erzeugt und gehören nicht ins AUR-Git-Repo:\n\n"
            "{files}\n\nJetzt endgültig löschen?"
        ),
        "msg_aur_cleanup_partial_error": (
            "Einige Dateien/Ordner konnten nicht gelöscht werden:\n{errors}"
        ),
    },

    # ====================================================================
    # ENGLISH
    # ====================================================================
    "en": {
        # ---- Dependencies / console ----
        "deps_header": "MISSING DEPENDENCIES",
        "deps_needed": "The following modules are required but not installed: {modules}",
        "deps_distro": "Detected distribution: {distro}",
        "deps_prompt": "\nWould you like to install the missing packages automatically? (y/N): ",
        "deps_declined": "Installation declined. Please install the packages manually and restart the script.",
        "deps_install_done_restart": "\nInstallation complete. Restarting the script...",
        "deps_install_failed_manual": "\nInstallation failed. Please install the packages manually and restart the script.",
        "deps_try_system_pkg": "\nAttempting installation with system package manager: {cmd}",
        "deps_system_success": "System installation successful.",
        "deps_system_failed_try_pip": "System installation failed. Trying pip --user now...",
        "deps_no_system_mgr": "No system package manager detected. Using pip --user.",
        "deps_running": "\nRunning: {cmd}",
        "deps_pip_success": "pip installation successful.",
        "deps_pip_failed": "pip installation failed.",

        # ---- Dialog: New repository ----
        "dlg_newrepo_title": "Create New Repository",
        "dlg_newrepo_name_label": "Name:",
        "dlg_newrepo_name_placeholder": "Repository name",
        "dlg_newrepo_desc_label": "Description:",
        "dlg_newrepo_desc_placeholder": "Description (optional)",
        "dlg_newrepo_visibility_label": "Visibility:",
        "dlg_newrepo_private_checkbox": "Private",

        # ---- Dialog: New Release ----
        "dlg_newrelease_title": "Create New Release",
        "dlg_newrelease_tag_label": "Tag:",
        "dlg_newrelease_tag_placeholder": "e.g. v1.0.0",
        "dlg_newrelease_target_label": "Target branch:",
        "dlg_newrelease_target_placeholder": "Use default branch (optional)",
        "dlg_newrelease_reltitle_label": "Title:",
        "dlg_newrelease_reltitle_placeholder": "Release title (optional, defaults to tag)",
        "dlg_newrelease_notes_label": "Notes / Changelog:",
        "dlg_newrelease_notes_placeholder": "What's new in this release?",
        "dlg_newrelease_prerelease_checkbox": "Mark as pre-release",
        "dlg_newrelease_draft_checkbox": "Save as draft (do not publish)",

        # ---- Dialog: Help ----
        "dlg_help_title": "Help – GitHub Repository Manager",
        "help_html": """
<style>
  body { font-family: sans-serif; font-size: 13px; }
  h2 { color: #2a6099; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
  h3 { color: #1a4070; margin-top: 14px; margin-bottom: 4px; }
  p, li { line-height: 1.6; }
  ul { margin-top: 4px; }
  code { background: #f0f0f0; padding: 1px 4px; border-radius: 3px; font-size: 12px; }
  .hinweis { background: #fffbe6; border-left: 4px solid #f0b429;
             padding: 6px 10px; margin: 8px 0; border-radius: 3px; }
  .tipp { background: #e8f4fd; border-left: 4px solid #2a6099;
          padding: 6px 10px; margin: 8px 0; border-radius: 3px; }
</style>
<h2>GitHub Repository Manager – User Guide</h2>

<h2>1. Getting Started – Login</h2>
<p>To use the app you need a GitHub account and a
<b>Personal Access Token (PAT)</b>.</p>
<h3>Creating a token</h3>
<ul>
  <li>Click <b>"Create new token"</b> – the GitHub settings page opens.</li>
  <li>Choose <b>"Generate new token (classic)"</b>.</li>
  <li>Set an expiration date and enable the <code>repo</code> permission.</li>
  <li>Copy the generated token and paste it into the <b>"Personal Access Token"</b> field.</li>
</ul>
<h3>Connecting</h3>
<ul>
  <li>Enter your username and token, then click <b>"Connect"</b>.</li>
  <li>On success your repositories appear in the list.</li>
  <li>Credentials are saved locally (<code>~/.config/github_manager/</code>)
      and loaded automatically the next time you start the app.</li>
</ul>
<div class="tipp">
  <b>Tip:</b> Use <b>"Check token"</b> at any time to test whether your
  token is still valid without reconnecting.
</div>

<h2>2. Managing repositories</h2>
<h3>Create a new repository</h3>
<ul>
  <li>Click <b>"New repository"</b>.</li>
  <li>Enter a name and optional description, choose visibility (public/private).</li>
  <li>The repository is created on GitHub and appears in the list immediately.</li>
</ul>
<h3>Delete a repository</h3>
<ul>
  <li>Select a repository in the list, then click <b>"Delete repository"</b>.</li>
  <li>A confirmation prompt prevents accidental deletion.</li>
</ul>
<div class="hinweis">
  <b>Warning:</b> Deleting removes the repository from GitHub irreversibly,
  including all commits, issues, and pull requests.
</div>
<h3>Refresh the list</h3>
<ul>
  <li><b>"Refresh"</b> reloads the repository list from GitHub.</li>
</ul>

<h2>3. Local repository</h2>
<h3>Setting the default folder</h3>
<p>The default folder is the base folder where repositories are cloned or
initialized.</p>
<ul>
  <li><b>"Set as default"</b> – uses the currently loaded repo path as the default.</li>
  <li><b>"Change"</b> – opens a folder selection dialog.</li>
</ul>
<h3>Cloning a repository</h3>
<ul>
  <li>Select a repository in the list.</li>
  <li>Click <b>"Clone repository"</b> – the content is downloaded into the default folder.</li>
  <li>The cloned repository is automatically loaded as the active local repo.</li>
</ul>
<h3>Initializing a new local repository</h3>
<ul>
  <li>Select a <b>GitHub repository</b> in the list (the target for the later push).</li>
  <li>Click <b>"Init new repo"</b>.</li>
  <li>A new folder is created in the default directory, <code>git init</code>
      is run, and <code>origin</code> is set to the chosen GitHub repository.</li>
</ul>
<div class="hinweis">
  <b>Warning:</b> If the GitHub repository already contains files (e.g. an
  automatically created README), <b>"Clone repository"</b> is the right
  approach instead – otherwise you'll end up with divergent histories.
</div>
<h3>Loading an existing local repository</h3>
<ul>
  <li><b>"Select folder"</b> opens a folder selection dialog.</li>
  <li>Choose a folder that already contains a <code>.git</code> directory.</li>
</ul>

<h2>4. Commit, push, and pull</h2>
<h3>Commit</h3>
<ul>
  <li>Enter a commit message in the text field.</li>
  <li>Click <b>"Commit"</b> – all changes in the repo are staged and committed.</li>
</ul>
<div class="hinweis">
  <b>"No changes found"</b> means there are no changed files in the loaded
  folder. Check that you loaded the right folder and that files aren't
  excluded by <code>.gitignore</code>.
</div>
<h3>Push</h3>
<ul>
  <li><b>"Push to GitHub"</b> transfers local commits to GitHub.</li>
  <li>If the local branch name differs from the default branch on GitHub
      (e.g. <code>master</code> vs. <code>main</code>), you'll be asked
      where to push.</li>
  <li>For a rejected push (<b>non-fast-forward</b>), the app offers to
      automatically run a pull.</li>
</ul>
<h3>Pull</h3>
<ul>
  <li><b>"Pull from GitHub"</b> fetches the latest commits from the remote and merges them locally.</li>
  <li>On merge conflicts a message appears – conflicts must be resolved
      manually in a terminal (<code>git status</code>, edit files,
      then commit).</li>
</ul>
<div class="tipp">
  <b>Recommended workflow:</b><br>
  1. Run <b>Pull</b> (fetch remote changes)<br>
  2. Edit files<br>
  3. <b>Commit</b> with a meaningful message<br>
  4. <b>Push</b> to GitHub
</div>

<h2>5. Creating a release</h2>
<ul>
  <li>Select a repository in the list, then click <b>"Create release"</b>.</li>
  <li>Enter a tag (e.g. <code>v1.3.0</code>), target branch, title, and release
      notes; optionally mark it as a <b>pre-release</b> or <b>draft</b>.</li>
  <li>A release tags whatever is currently <b>on GitHub</b> – not your local
      working state.</li>
</ul>
<div class="hinweis">
  <b>Order check:</b> If the matching local repository happens to be loaded,
  the app first runs a quick status check. If there are still uncommitted
  changes, unpushed commits, or an open merge, it warns you with
  <b>"Not everything pushed yet"</b> and the recommended order
  <b>Commit → Push → Release</b>. You can still proceed, but those changes
  won't be part of the release.
</div>

<h2>6. Managing the AUR package (AUR tab)</h2>
<h3>Loading a folder</h3>
<ul>
  <li><b>"Select folder"</b> opens an existing local AUR git folder
      (containing a <code>PKGBUILD</code>).</li>
  <li>Package name, current version, and <code>pkgrel</code> are shown.</li>
</ul>
<h3>Creating a new AUR package</h3>
<ul>
  <li><b>"Create new AUR package"</b> sets up a PKGBUILD skeleton for a
      package that doesn't exist yet, linked to a GitHub repository (asks
      for name, starting version, description, URL, license, architecture,
      and dependencies).</li>
  <li>Creates the folder, initializes a git repository, and sets the remote
      to <code>ssh://aur@aur.archlinux.org/&lt;package&gt;.git</code> – the
      package is only actually published once you push it for the first
      time.</li>
  <li>Offered right after creating a <b>new GitHub repository</b>
      ("Would you also like to create an AUR package for it?"), but can also
      be started on its own from the AUR tab at any time.</li>
</ul>
<div class="hinweis">
  <b>Warning:</b> The generated <code>package()</code> section is only a
  placeholder and needs to be adapted to the specific project. Also,
  <code>source=</code> requires an existing GitHub tag – create a matching
  release first (see section 5) before running "Update version" for the new
  package. Publishing also requires an SSH key registered with your own AUR
  account.
</div>
<h3>Update version</h3>
<ul>
  <li>Enter the new version, then click <b>"Update version"</b>.</li>
  <li>This sets <code>pkgver</code> in the PKGBUILD, re-downloads the files
      referenced in <code>source=</code> via <code>updpkgsums</code> and writes
      the checksums, and regenerates <code>.SRCINFO</code>
      (<code>makepkg --printsrcinfo</code>).</li>
  <li>This step only changes <b>local</b> files – it does not commit or push
      to AUR yet.</li>
</ul>
<div class="hinweis">
  <b>Warning:</b> If <code>source=</code> points at a git tag (e.g.
  <code>archive/refs/tags/v$pkgver.tar.gz</code>), that tag must already exist
  on GitHub, or <code>updpkgsums</code> will fail. So create the matching
  GitHub release/tag first (see section 5), then update the AUR version.
</div>
<h3>Commit && push</h3>
<ul>
  <li>Commits <b>only</b> <code>PKGBUILD</code> and <code>.SRCINFO</code>
      (build artifacts such as <code>pkg/</code>, <code>src/</code>, or
      <code>*.pkg.tar.zst</code> are deliberately left out), then pushes to the
      AUR git repository.</li>
</ul>
<h3>Check status / suggested action</h3>
<ul>
  <li><b>"Check status"</b> shows what's needed next (e.g. "commit needed",
      "push needed", "up to date").</li>
  <li><b>"Run suggested action"</b> runs the suggested action directly.</li>
</ul>
<div class="hinweis">
  <b>Order lock:</b> A label under the version field shows whether "Update
  version" has already run in this pass (✓/⚠). If you try to commit/push
  without having updated the version first, the app will ask for confirmation
  – this prevents the wrong order of "push first, then commit, then version".
  For a plain PKGBUILD fix with no version change you can still confirm and
  continue.
</div>

<h2>7. Update assistant</h2>
<p>Via the menu <b>"Assistants → Update assistant..."</b>, a guided dialog
walks you through a complete update step by step, in the right order – the
"Next" button only becomes active once the current step is done.</p>
<h3>Flow</h3>
<ol>
  <li><b>Start page:</b> choose whether to create a GitHub release and/or
      update the linked AUR package at the end.</li>
  <li><b>New version:</b> shows the currently detected version (latest GitHub
      release resp. current PKGBUILD version) and suggests a new one
      automatically. Use <b>"+ Patch"</b>, <b>"+ Minor"</b>, and
      <b>"+ Major"</b> to bump it with one click (following the
      Major.Minor.Patch scheme), or enter it manually. This single version is
      then used as the suggested tag for the release and the suggested
      <code>pkgver</code> for the AUR package.</li>
  <li><b>Commit</b> (GitHub) → <b>Push</b> (GitHub) → optionally
      <b>Create release</b> → optionally <b>Update AUR version</b> →
      optionally <b>AUR commit && push</b> → summary.</li>
</ol>
<div class="hinweis">
  If you close the assistant mid-flow while steps are still open, it warns
  you first – otherwise a locally updated but never-pushed AUR version could
  go unnoticed.
</div>

<h2>8. Common error messages</h2>
<h3>"Need to specify how to reconcile divergent branches"</h3>
<p>The local and remote branches have a different commit history.
Run a <b>Pull</b> first.</p>
<h3>"rejected (non-fast-forward)"</h3>
<p>GitHub has commits that are missing locally (e.g. direct changes made via
the web interface). <b>Pull</b> first, then <b>Push</b> again.</p>
<h3>"No changes to commit"</h3>
<p>There is nothing to commit. Possible causes: wrong folder loaded,
files not yet saved, or excluded by <code>.gitignore</code>.</p>
<h3>"Token invalid / 401"</h3>
<p>The token has expired or is incorrect. Create a new token on GitHub and enter it.</p>
<h3>"Not everything pushed yet" (when creating a release)</h3>
<p>The locally loaded repository still has uncommitted or unpushed changes
that would be missing from the planned release. Commit and push first, then
create the release – or proceed deliberately anyway.</p>
<h3>"Version not updated yet" (in the AUR tab)</h3>
<p>You tried to commit/push to AUR without having run <b>"Update version"</b>
first. Usually a sign the order got mixed up – unless it's a deliberate
plain PKGBUILD fix with no version change.</p>
        """,

        # ---- Dialog: About ----
        "dlg_about_title": "About GitHub Repository Manager",
        "about_app_title": "GitHub Repository Manager",
        "about_version": "Version 1.07",
        "about_author_block": (
            "<b>Author:</b> Jürg Rechsteiner<br>"
            "<b>Website:</b> <a href='https://www.computer-experte.ch'>computer-experte.ch</a><br>"
            "<b>Region:</b> St. Gallen / Thurgau, Switzerland"
        ),
        "about_desc": (
            "<br><i>A PyQt6-based GitHub Repository Manager<br>"
            "for Linux – developed with Python and GitPython.</i>"
        ),

        # ---- Main window: title / menu ----
        "main_window_title": "GitHub Repository Manager 1.07",
        "menu_help": "&Help",
        "menu_action_manual": "&User Guide",
        "menu_action_manual_tooltip": (
            "Opens the full user guide covering login, repository "
            "management, commit/push/pull, creating releases, the AUR tab, "
            "and the update assistant, plus a list of common error messages."
        ),
        "menu_action_about": "&About...",
        "menu_action_about_tooltip": (
            "Shows the version number, author, and contact information for "
            "this application."
        ),
        "menu_language": "&Language",
        "menu_language_item_tooltip": (
            "Switches the interface language to {language} immediately – no "
            "restart needed."
        ),

        # ---- Tabs ----
        "tab_github": "GitHub",
        "tab_aur": "AUR",

        # ---- Login ----
        "login_group_title": "GitHub Login",
        "login_username_label": "Username:",
        "login_username_placeholder": "GitHub username",
        "login_username_tooltip": "Enter your GitHub username",
        "login_token_label": "Personal Access Token:",
        "login_token_placeholder": "ghp_...",
        "login_token_tooltip": "Enter your Personal Access Token (PAT).",
        "btn_connect": "Connect",
        "btn_connect_tooltip": "Connect to GitHub",
        "btn_check_token": "Check token",
        "btn_check_token_tooltip": "Checks whether the token is valid",
        "btn_create_token": "Create new token",
        "btn_create_token_tooltip": "Opens the GitHub page for creating a token",

        # ---- Repository list ----
        "repolist_group_title": "Repositories",
        "repolist_tooltip": "List of all GitHub repositories",
        "btn_new_repo": "New repository",
        "btn_new_repo_tooltip": "Creates a new repository on GitHub",
        "btn_delete_repo": "Delete repository",
        "btn_delete_repo_tooltip": "Deletes the selected repository",
        "btn_refresh": "Refresh",
        "btn_refresh_tooltip": "Refreshes the repository list",

        # ---- Local repository ----
        "local_group_title": "Local Repository",
        "local_default_folder_label": "Default folder:",
        "local_default_folder_placeholder": "No default folder set",
        "btn_set_default": "Set as default",
        "btn_set_default_tooltip": "Sets the current folder as default",
        "btn_change_default": "Change",
        "btn_change_default_tooltip": "Choose a new default folder",
        "btn_clone": "Clone repository",
        "btn_clone_tooltip": "Clones the selected repository into the default folder",
        "btn_init": "Init new repo",
        "btn_init_tooltip": (
            "Creates a new local Git repository (git init) and links it to "
            "the GitHub repository selected above"
        ),
        "btn_browse": "Select folder",
        "btn_browse_tooltip": "Selects a local folder as a Git repository",
        "local_loaded_label": "Loaded:",
        "local_loaded_placeholder": "No repository loaded",
        "local_commit_msg_label": "Commit message:",
        "local_commit_msg_placeholder": "Describe changes...",
        "btn_commit": "Commit",
        "btn_commit_tooltip": "Stages all changes and creates a commit",
        "btn_push": "Push to GitHub",
        "btn_push_tooltip": "Pushes commits to GitHub",
        "btn_pull": "Pull from GitHub",
        "btn_pull_tooltip": "Fetches changes from GitHub",
        "btn_link_remote": "Link to GitHub",
        "btn_release": "Create Release",
        "btn_release_tooltip": "Creates a new GitHub release (with tag) for the selected repository",
        "btn_link_remote_tooltip": (
            "Sets the 'origin' remote of the loaded local repository to "
            "the GitHub repository selected above"
        ),
        "branch_label_empty": "Branch: –",
        "branch_label": "Branch: {branch}",
        "btn_check_status": "Check status",
        "btn_check_status_tooltip": (
            "Checks the current repository state (changes, open merge, "
            "push/pull requirements) and suggests the next sensible action"
        ),
        "btn_suggested_action": "Run suggested action",
        "btn_suggested_action_tooltip": "Runs the recommended action shown above",

        # ---- Suggested action ----
        "recommendation_none": "No analysis run yet",
        "recommendation_error": "Status check failed",
        "recommendation_merge_pending": "An open merge needs to be resolved first",
        "recommendation_commit_needed": "Commit recommended: {count} change(s) found",
        "recommendation_no_remote": "No remote linked – push/pull not possible",
        "recommendation_no_auth": "Not signed in – push/pull status cannot be checked",
        "recommendation_push_needed": "Push recommended: {ahead} commit(s) ahead",
        "recommendation_pull_needed": "Pull recommended: {behind} commit(s) behind",
        "recommendation_diverged": (
            "Branches diverged: {ahead} local / {behind} remote commit(s) "
            "– pull recommended first"
        ),
        "recommendation_up_to_date": "Everything up to date – nothing to do",
        "action_btn_resolve_merge": "Resolve merge",
        "action_btn_commit": "Run commit",
        "action_btn_push": "Run push",
        "action_btn_pull": "Run pull",

        # ---- AUR tab ----
        "aur_group_title": "Update AUR package",
        "aur_intro_text": (
            "Updates an already locally cloned AUR package: sets the new "
            "version (and pkgrel) in the PKGBUILD, re-downloads the sources "
            "to recompute checksums (updpkgsums), regenerates .SRCINFO, and "
            "commits + pushes to the AUR."
        ),
        "aur_folder_label": "AUR folder:",
        "aur_folder_placeholder": "No AUR folder loaded",
        "btn_aur_browse": "Choose folder",
        "btn_aur_browse_tooltip": (
            "Selects the local clone of an AUR repository "
            "(e.g. from ssh://aur@aur.archlinux.org/<package>.git)"
        ),
        "btn_aur_new_package": "Create new AUR package",
        "btn_aur_new_package_tooltip": (
            "Creates a brand-new AUR package: sets up a folder with a "
            "PKGBUILD skeleton, initializes a git repository, and sets the "
            "AUR remote (ssh://aur@aur.archlinux.org/<package>.git). The "
            "package is only actually published once you push it for the "
            "first time."
        ),

        # ---- New AUR package (dialog) ----
        "dlg_newaur_title": "New AUR package",
        "dlg_newaur_intro": (
            "Creates a PKGBUILD skeleton for a new AUR package linked to a "
            "GitHub repository. Afterwards you can edit it as usual in the "
            "AUR tab, compute checksums with \"Update version\", and publish "
            "it to AUR with \"Commit && push\"."
        ),
        "dlg_newaur_pkgname_label": "Package name:",
        "dlg_newaur_pkgname_placeholder": "e.g. my-tool (only a-z, 0-9, @._+-)",
        "dlg_newaur_pkgver_label": "Starting version:",
        "dlg_newaur_pkgdesc_label": "Description:",
        "dlg_newaur_pkgdesc_placeholder": "Short description of the package",
        "dlg_newaur_url_label": "Project URL:",
        "dlg_newaur_url_tooltip": (
            "The GitHub repository URL (e.g. https://github.com/name/repo).\n"
            "Used twice: as the \"url=\" field in the PKGBUILD and as the base "
            "for the auto-generated source URL for the version tag "
            "(<URL>/archive/refs/tags/v<version>.tar.gz). So it must be the "
            "actual GitHub repo, not just a general project homepage."
        ),
        "dlg_newaur_license_label": "License:",
        "dlg_newaur_license_custom_option": "Custom / enter SPDX expression manually…",
        "dlg_newaur_license_custom_placeholder": "e.g. LicenseRef-MyLicense or a custom SPDX expression",
        "dlg_newaur_arch_label": "Architecture(s):",
        "dlg_newaur_arch_placeholder": "e.g. x86_64 or any (comma-separated)",
        "dlg_newaur_depends_label": "Dependencies:",
        "dlg_newaur_depends_placeholder": "comma-separated, e.g. python, git",
        "dlg_newaur_hint": (
            "Note: the source in the PKGBUILD points at a GitHub tag (e.g. "
            "v1.0.0). That tag must exist on GitHub before \"Update version\" "
            "can compute checksums – create a matching release first. You'll "
            "likely want to adjust the generated package() section for your "
            "project afterwards."
        ),

        # ---- New AUR package: messages ----
        "dlg_choose_aur_base_folder": "Choose base folder for AUR packages",
        "dlg_choose_aur_location": "Choose a location for the new AUR package folder",
        "dlg_aur_folder_name_title": "Folder name",
        "dlg_aur_folder_name_label": "Name of the new folder:",
        "msg_aur_foldername_invalid": "Invalid folder name.",
        "msg_aur_pkgname_invalid": (
            "Invalid package name. Allowed are lowercase letters, digits, "
            "and @ . _ + - (must start with an alphanumeric character)."
        ),
        "msg_aur_url_required": "Please enter a project URL.",
        "msg_aur_folder_exists": "The folder \"{folder}\" already exists.",
        "status_aur_creating_package": "Creating AUR package '{pkgname}'...",
        "status_aur_creating_package_failed": "Failed to create the AUR package",
        "status_aur_package_created": "AUR package '{pkgname}' created",
        "msg_aur_package_created_title": "AUR package created",
        "msg_aur_package_created_text": (
            "The skeleton for \"{pkgname}\" (version {version}) has been "
            "created and loaded locally.\n\n"
            "Next steps:\n"
            "1. Adjust the package() section in the PKGBUILD if needed.\n"
            "2. Make sure a GitHub release/tag exists for this version.\n"
            "3. Click \"Update version\" to generate checksums and "
            ".SRCINFO.\n"
            "4. Click \"Commit && push\" to publish the package to AUR for "
            "the first time (requires an SSH key registered with your AUR "
            "account)."
        ),
        "msg_aur_package_create_error": "Error creating the AUR package:\n{error}",
        "msg_aur_offer_title": "Create AUR package?",
        "msg_aur_offer_text": (
            "Repository \"{name}\" was created.\n\n"
            "Would you also like to create a new AUR package skeleton for it?"
        ),

        "aur_info_none": "No AUR package loaded",
        "aur_info": "Package: {pkgname} – currently {version}-{rel}",
        "aur_version_label": "New version:",
        "aur_version_placeholder": "e.g. 2.4.1",
        "btn_aur_update": "Update version",
        "btn_aur_update_tooltip": (
            "Sets pkgver/pkgrel in the PKGBUILD, updates checksums "
            "(updpkgsums), and regenerates .SRCINFO"
        ),
        "aur_commit_msg_label": "Commit message:",
        "aur_commit_msg_placeholder": "Commit message for the AUR push...",
        "aur_commit_msg_default": "Update to {version}",
        "btn_aur_commit_push": "Commit && push to AUR",
        "btn_aur_commit_push_tooltip": "Commits PKGBUILD/.SRCINFO and pushes to the AUR",

        # ---- AUR tab: status recommendation ----
        "btn_aur_check_status": "Check status",
        "btn_aur_check_status_tooltip": (
            "Checks the state of the AUR folder (changes, open merge, "
            "push/pull requirements) and suggests the next action"
        ),
        "btn_aur_suggested_action": "Run suggested action",
        "btn_aur_suggested_action_tooltip": "Runs the recommended action shown above",
        "aur_recommendation_none": "No analysis run yet",
        "aur_recommendation_error": "Status check failed",
        "aur_recommendation_merge_pending": "An open merge needs to be resolved first",
        "aur_recommendation_commit_needed": "Commit recommended: {count} change(s) found",
        "aur_recommendation_new_files": (
            "Adding to git recommended: {count} new file(s) not yet added to git"
        ),
        "aur_recommendation_artifacts_found": (
            "Cleanup recommended: {count} build artifact(s) found (e.g. downloaded "
            "source tarballs) – do not belong in the git repo"
        ),
        "aur_recommendation_no_remote": "No remote linked – push/pull not possible",
        "aur_recommendation_push_needed": "Push to AUR recommended: {ahead} commit(s) ahead",
        "aur_recommendation_pull_needed": "Pull from AUR recommended: {behind} commit(s) behind",
        "aur_recommendation_diverged": (
            "Branches diverged: {ahead} local / {behind} remote commit(s) "
            "– pull recommended first"
        ),
        "aur_recommendation_up_to_date": "Everything up to date – nothing to do",
        "aur_action_btn_resolve_merge": "Resolve merge",
        "aur_action_btn_commit": "Run commit",
        "aur_action_btn_add_files": "Add file(s) to git",
        "aur_action_btn_cleanup": "Delete artifacts",
        "aur_action_btn_push": "Run push",
        "aur_action_btn_pull": "Run pull",

        # ---- AUR tab: order lock (version -> commit -> push) ----
        "aur_step_indicator_done": "✓ Version already updated in this run",
        "aur_step_indicator_pending": (
            "⚠ Version not updated in this run yet – you'll be asked before "
            "commit/push"
        ),
        "msg_aur_order_warning_title": "Version not updated yet",
        "msg_aur_order_warning_text": (
            "You haven't clicked \"Update version\" in this run yet.\n\n"
            "The recommended order is:\n"
            "1. Update version\n2. Commit\n3. Push to AUR\n\n"
            "Commit/push anyway? (e.g. fine for a plain PKGBUILD fix with no "
            "version change)"
        ),

        # ---- Update assistant ----
        "menu_tools": "&Assistants",
        "menu_action_update_assistant": "Update assistant...",
        "menu_action_update_assistant_tooltip": (
            "Opens a guided dialog that walks you through a complete update "
            "step by step: commit → push (GitHub) → optionally create a new "
            "release → optionally update, commit, and push the linked AUR "
            "package. Also suggests a new version number along the way. Each "
            "step must be completed before you can move on, so the order "
            "can't get mixed up."
        ),
        "wizard_title": "Update assistant",
        "wizard_btn_back": "Back",
        "wizard_btn_next": "Next",
        "wizard_btn_close": "Cancel",
        "wizard_btn_finish": "Finish",
        "wizard_btn_skip_step": "Skip this step",
        "wizard_btn_run_commit": "Commit",
        "wizard_btn_run_push": "Push to GitHub",
        "wizard_btn_run_release": "Create release...",
        "wizard_btn_run_aur_version": "Update version",
        "wizard_btn_run_aur_commit_push": "Commit && push to AUR",
        "wizard_progress_intro": "Step 0 of n – setup",
        "wizard_progress_step": "Step {current} of {total}",
        "wizard_intro_text": (
            "This assistant walks you through a complete update in the "
            "right order: commit and push to GitHub first, then optionally "
            "create a GitHub release, then optionally update the linked AUR "
            "package. Each step must be completed before moving on."
        ),
        "wizard_intro_no_github": (
            "No local GitHub repository loaded – commit/push will be "
            "skipped."
        ),
        "wizard_intro_no_aur": "No AUR folder loaded – this part is disabled.",
        "wizard_check_release": "Create a new GitHub release at the end",
        "wizard_check_aur": "Also update the linked AUR package",
        "wizard_version_group_title": "New version",
        "wizard_version_checking": "Checking latest GitHub release...",
        "wizard_version_current_github": "Latest GitHub release: {version}",
        "wizard_version_no_releases": "No GitHub release found yet.",
        "wizard_version_current_aur": "Currently in the PKGBUILD: {version}",
        "wizard_new_version_label": "New version:",
        "wizard_new_version_placeholder": "e.g. 1.3.0 or v1.3.0",
        "wizard_btn_bump_patch": "+ Patch",
        "wizard_btn_bump_minor": "+ Minor",
        "wizard_btn_bump_major": "+ Major",
        "wizard_version_manual_hint": (
            "Current version doesn't follow an X.Y.Z scheme – please enter "
            "the new version manually."
        ),
        "msg_wizard_version_required": (
            "Please enter a new version (used for the release tag and/or "
            "the AUR pkgver)."
        ),
        "wizard_close_confirm_title": "Not finished yet",
        "wizard_close_confirm_text": (
            "Not all steps are complete yet (e.g. a push). Local changes "
            "such as an already-updated PKGBUILD version would not be "
            "committed/pushed yet.\n\n"
            "Really close without finishing?"
        ),
        "wizard_no_local_repo": "No local GitHub repository loaded.",
        "wizard_no_aur_repo": "No AUR folder loaded.",
        "wizard_step_nothing_to_do": "✓ Nothing to do – this step is already satisfied.",
        "wizard_step_done": "✓ Done.",
        "wizard_commit_dirty_count": "{count} change(s) not committed yet.",
        "wizard_push_ahead_count": "{ahead} commit(s) not pushed yet.",
        "wizard_push_diverged": (
            "⚠ Local and remote commits have diverged. Please pull/merge in "
            "the GitHub tab first, then reopen this assistant."
        ),
        "wizard_push_merge_pending": (
            "⚠ There's still an open merge. Please finish it in the GitHub "
            "tab first, then reopen this assistant."
        ),
        "wizard_push_commit_needed": (
            "⚠ There are uncommitted changes again. Please go back and "
            "commit first."
        ),
        "wizard_push_blocked": "⚠ Push not possible right now (state: {state}).",
        "wizard_check_failed": "Could not check status: {error}",
        "wizard_step_commit_title": "1. GitHub: commit changes",
        "wizard_step_push_title": "2. GitHub: push to GitHub",
        "wizard_step_release_title": "3. GitHub: create release",
        "wizard_step_aur_version_title": "4. AUR: update version",
        "wizard_step_aur_commit_push_title": "5. AUR: commit && push",
        "wizard_step_summary_title": "Summary",
        "wizard_release_info": (
            "Opens the familiar release dialog. The tag should match the "
            "state you just pushed."
        ),
        "wizard_aur_current_version": "Currently in the PKGBUILD: {version}",
        "wizard_summary_text": "The assistant has finished:",

        # ---- Status bar ----
        "status_ready": "Ready",
        "status_token_saved_days": "Token saved {days} day(s) ago",
        "status_checking_token": "Checking token...",
        "status_token_valid": "Token valid (user: {username})",
        "status_token_valid_days": "Token valid (user: {username}) – saved {days} day(s) ago",
        "status_token_invalid": "Token is invalid or expired",
        "status_connecting": "Connecting...",
        "status_connected_as": "Connected as {username}",
        "status_connect_failed": "Connection failed",
        "status_loading_repos": "Reloading repositories...",
        "status_repos_refreshed": "Repositories refreshed",
        "status_refresh_failed": "Refresh failed",
        "status_creating_repo": "Creating repository '{name}'...",
        "status_repo_created": "Repository '{name}' created",
        "status_create_failed": "Creation failed",
        "status_deleting_repo": "Deleting repository '{name}'...",
        "status_repo_deleted": "Repository deleted",
        "status_delete_failed": "Deletion failed",
        "status_creating_release": "Creating release '{tag}'...",
        "status_release_created": "Release '{tag}' created",
        "status_release_failed": "Release creation failed",
        "status_default_folder_set": "Default folder set: {folder}",
        "status_default_folder_changed": "Default folder changed: {folder}",
        "status_local_repo_loaded_no_remote": (
            "Local repository loaded: {folder} – no remote configured. "
            "Select a GitHub repository above and click "
            "'Link to GitHub'."
        ),
        "status_local_repo_loaded": "Local repository loaded: {folder}",
        "status_linked_to_repo": "Linked to GitHub repository '{full_name}'",
        "status_cloning": "Cloning {name}...",
        "status_cloned": "Repository cloned: {path}",
        "status_clone_failed": "Cloning failed",
        "status_init_done": "New repository initialized and linked to '{full_name}': {path}",
        "status_commit_in_progress": "Committing...",
        "status_commit_success": "Commit successful: {hash}",
        "status_commit_failed": "Commit failed",
        "status_push_cancelled": "Push cancelled",
        "status_pushing": "Pushing...",
        "status_push_up_to_date": "Push: branch '{branch}' was already up to date – no new commits",
        "status_push_success_renamed": "Push successful: '{local}' → GitHub branch '{remote}'",
        "status_push_success": "Push successful (branch: {branch})",
        "status_push_failed": "Push failed",
        "status_pull_cancelled": "Pull cancelled",
        "status_push_needs_pull": "Push not possible: remote branch has newer commits",
        "status_merge_committed": "Pending merge committed",
        "status_merge_aborted": "Pending merge discarded",
        "status_checking_repo_state": "Checking repository status...",
        "status_check_done": "Status check complete",
        "status_check_failed": "Status check failed",
        "status_enter_commit_message": "Please enter a commit message first",
        "status_aur_folder_loaded": "AUR folder loaded: {folder}",
        "status_aur_updating": "Updating PKGBUILD and checksums...",
        "status_aur_update_done": "PKGBUILD updated to version {version}",
        "status_aur_update_failed": "Updating the PKGBUILD failed",
        "status_aur_pushing": "Pushing to the AUR...",
        "status_aur_push_success": "Push to the AUR successful",
        "status_aur_push_failed": "Push to the AUR failed",
        "status_aur_checking_repo_state": "Checking AUR repository status...",
        "status_aur_check_done": "AUR status check complete",
        "status_aur_check_failed": "AUR status check failed",
        "status_aur_pulling": "Pulling from the AUR...",
        "status_aur_pull_success": "Pull from the AUR successful",
        "status_aur_pull_failed": "Pull from the AUR failed",
        "status_aur_files_added": "New file(s) added to git",
        "status_aur_cleanup_done": "Build artifacts deleted",
        "status_pulling": "Pulling...",
        "status_pull_success": "Pull successful from '{branch}'",
        "status_pull_failed": "Pull failed",

        # ---- File dialogs ----
        "dlg_choose_default_folder": "Select default folder",
        "dlg_choose_local_repo_folder": "Select local Git repository",

        # ---- Message boxes ----
        "msg_error_title": "Error",
        "msg_token_check_title": "Check token",
        "msg_token_check_empty": "No token entered.",
        "msg_token_invalid_title": "Invalid token",
        "msg_token_invalid_text": "The token is invalid. Would you like to clear the field?",
        "msg_token_check_error": "Error during token check:\n{error}",
        "msg_create_token_title": "Create token",
        "msg_create_token_text": (
            "The GitHub page has been opened.\n\n"
            "1. Click 'Generate new token' (classic)\n"
            "2. Choose an expiration date\n"
            "3. Select the 'repo' permission\n"
            "4. Copy the token and paste it here"
        ),
        "msg_username_token_required": "Please enter username and token.",
        "msg_connect_error_title": "Connection error",
        "msg_connect_error_text": "Connection error:\n{error}",
        "msg_repo_name_empty": "The repository name must not be empty.",
        "msg_create_error": "Error during creation:\n{error}",
        "msg_delete_confirm_title": "Delete repository",
        "msg_delete_confirm_text": "Do you really want to delete the repository '{name}'?",
        "msg_delete_error": "Error during deletion:\n{error}",
        "msg_no_git_repo_title": "Not a Git repository",
        "msg_no_git_repo_text": "'{folder}' is not a Git repository.",
        "msg_load_error": "Error loading:\n{error}",
        "msg_no_remote_title": "No remote configured",
        "msg_no_remote_text": (
            "'{folder}' was loaded, but is not yet linked to a "
            "GitHub repository (no 'origin' remote).\n\n"
            "Select the matching GitHub repository in the 'Repositories' "
            "list above and then click 'Link to GitHub' "
            "to enable push/pull."
        ),
        "msg_no_repo_title": "No repository",
        "msg_load_local_first": "First load a local repository.",
        "msg_no_github_repo_title": "No GitHub repository selected",
        "msg_no_github_repo_text_link": (
            "First select the GitHub repository you want to link to in the "
            "'Repositories' list above."
        ),
        "msg_no_github_repo_text_release": (
            "First select the GitHub repository you want to create a "
            "release for in the 'Repositories' list above."
        ),
        "msg_release_tag_empty": "The tag must not be empty (e.g. v1.0.0).",
        "msg_release_created_title": "Release created",
        "msg_release_created_text": "Release '{tag}' was created successfully.\n\n{url}",
        "msg_release_error": "Error creating release:\n{error}",

        # ---- GitHub tab: order lock (commit -> push -> release) ----
        "msg_release_order_warning_title": "Not everything pushed yet",
        "msg_release_order_warning_commit": (
            "The locally loaded repository still has uncommitted changes. "
            "A GitHub release tags whatever is currently on GitHub - these "
            "changes would NOT be included.\n\nRecommended order:\n"
            "1. Commit\n2. Push\n3. Create release\n\n"
            "Create the release anyway?"
        ),
        "msg_release_order_warning_push": (
            "The locally loaded repository has committed changes that "
            "haven't been pushed yet. A GitHub release tags whatever is "
            "currently on GitHub - these changes would NOT be included.\n\n"
            "Recommended order:\n1. Commit\n2. Push\n3. Create release\n\n"
            "Create the release anyway?"
        ),
        "msg_release_order_warning_merge": (
            "The locally loaded repository still has an open merge. Please "
            "finish it, commit, and push in the GitHub tab first before "
            "creating a release.\n\nCreate the release anyway?"
        ),
        "msg_connect_first": "Please connect first.",
        "msg_linked_title": "Linked",
        "msg_linked_text": (
            "The local repository is now linked to "
            "'{full_name}'.\n\n"
            "If the GitHub repository already has content and the local "
            "repository does not yet share a common history, run "
            "'Pull from GitHub' first before pushing."
        ),
        "msg_link_error": "Error linking:\n{error}",
        "msg_no_default_folder_title": "No default folder",
        "msg_no_default_folder_text": "First set a default folder.",
        "msg_folder_exists_title": "Folder exists",
        "msg_folder_exists_text": "The folder '{folder}' already exists. Overwrite?",
        "msg_clone_error": "Error cloning:\n{error}",
        "msg_no_github_repo_text_init": (
            "First select the GitHub repository in the 'Repositories' "
            "list above that the new local repository should be linked "
            "to.\n\n"
            "If it doesn't exist yet, create it first using "
            "'New repository'."
        ),
        "msg_repo_not_empty_title": "Repository is not empty",
        "msg_repo_not_empty_text": (
            "'{name}' already contains files on GitHub.\n"
            "A new local repository created with 'git init' has its own, "
            "independent history – the first push would fail or "
            "require a force push.\n\n"
            "Recommendation: use 'Clone repository' instead.\n\n"
            "Continue anyway?"
        ),
        "msg_new_repo_dialog_title": "New repository",
        "msg_new_repo_dialog_label": "Name of the new local folder:",
        "msg_exists_title": "Already exists",
        "msg_exists_text": "The folder '{folder}' already exists.",
        "msg_init_error": "Error initializing:\n{error}",
        "msg_no_local_repo": "No local repository selected.",
        "msg_commit_msg_required": "Please enter a commit message.",
        "msg_commit_error": "Error during commit:\n{error}",
        "msg_no_token_user": "No token or user. Please connect again.",
        "msg_branch_mismatch_title": "Branch mismatch",
        "msg_branch_mismatch_text": (
            "The local branch is named '{local}', but the default branch "
            "of this repository on GitHub is '{default}'.\n\n"
            "Where should this be pushed?"
        ),
        "btn_push_to_default": "Push to '{branch}' (recommended)",
        "btn_push_to_local": "Push to '{branch}'",
        "btn_cancel": "Cancel",
        "msg_up_to_date_title": "Already up to date",
        "msg_up_to_date_text": (
            "There were no new commits to transfer to '{branch}'.\n\n"
            "Were the changes committed beforehand?"
        ),
        "msg_push_error_pull_question": (
            "Push error:\n{error}\n\n"
            "Would you like to run a pull now to fetch the remote changes "
            "first and then push again?"
        ),
        "msg_push_error": "Push error:\n{error}",
        "msg_pull_error": "Pull error:\n{error}",
        "msg_check_status_error": "Error during status check:\n{error}",
        "msg_remote_ahead_title": "Remote is ahead",
        "msg_remote_ahead_text": (
            "The remote branch '{branch}' contains commits that are not "
            "present locally. A push is only possible after a pull.\n\n"
            "Pull now?"
        ),
        "msg_merge_pending_title": "Unfinished merge",
        "msg_merge_pending_text": (
            "There is an unfinished merge (e.g. from a previous pull). "
            "All conflicts appear to be resolved already – it just needs "
            "to be concluded.\n\n"
            "Commit the merge now, or discard it?"
        ),
        "msg_merge_conflicts_unresolved_text": (
            "There is an unfinished merge with unresolved conflicts. "
            "Please clean up the affected files first in a terminal or "
            "editor (remove the conflict markers <<<<<<<, =======, "
            ">>>>>>>).\n\n"
            "Alternatively, the merge can be discarded entirely – this "
            "will lose any locally uncommitted changes from this merge."
        ),
        "msg_merge_abort_error": "Error discarding the merge:\n{error}",
        "msg_merge_resolve_error": "Error concluding the merge:\n{error}",
        "btn_merge_commit": "Commit merge",
        "btn_merge_abort": "Discard merge",

        # ---- Errors from background worker functions ----
        "err_push_no_feedback": (
            "GitHub did not return any feedback for the push. "
            "It cannot be confirmed that the changes were "
            "transferred."
        ),
        "err_push_rejected": (
            "GitHub rejected the push:\n{summaries}\n\n"
            "Possible cause: the remote branch contains commits that are "
            "not present locally (e.g. changes made via the GitHub "
            "web interface). Run 'Pull from GitHub' first, then push again."
        ),
        "err_merge_conflict_unrelated": (
            "Merge conflict while merging the previously "
            "unrelated histories: the same files were changed "
            "differently locally and on GitHub.\n\n"
            "Please check with 'git status' in the project folder "
            "in a terminal, resolve conflicts manually, and then "
            "commit."
        ),
        "err_pull_failed": "Pull failed:\n{error}",
        "err_merge_conflict": (
            "Merge conflict during pull. Please check with "
            "'git status' in the project folder in a terminal, "
            "resolve conflicts manually, and then commit."
        ),
        "err_no_changes_to_commit": (
            "No changes found to commit.\n"
            "Check whether you are working in the correct folder and "
            "whether the changed files are excluded by .gitignore."
        ),

        # ---- AUR: dialogs / messages ----
        "dlg_choose_aur_folder": "Select local AUR repository folder",
        "msg_aur_no_pkgbuild": (
            "No PKGBUILD was found in folder '{folder}'. "
            "Please select the local clone of the AUR repository "
            "(e.g. from ssh://aur@aur.archlinux.org/<package>.git)."
        ),
        "msg_aur_no_folder": "Please select an AUR folder first.",
        "msg_aur_version_required": "Please enter a new version.",
        "msg_aur_version_invalid": "The version must not contain whitespace.",
        "msg_aur_update_error": "Error updating the PKGBUILD:\n{error}",
        "msg_aur_push_success_title": "AUR updated",
        "msg_aur_push_success_text": "The AUR package was updated and pushed successfully.",
        "msg_aur_push_error": "Error pushing to the AUR:\n{error}",
        "msg_aur_after_push_title": "Update AUR too?",
        "msg_aur_after_push_text": (
            "GitHub push was successful. Also update the linked "
            "AUR package now?"
        ),
        "err_aur_updpkgsums_missing": (
            "The 'updpkgsums' tool was not found. It is part of the "
            "'pacman-contrib' package (e.g. 'sudo pacman -S pacman-contrib')."
        ),
        "err_aur_updpkgsums_failed": "Updating checksums failed:\n{error}",
        "err_aur_makepkg_missing": (
            "The 'makepkg' tool was not found. It is part of the base "
            "'pacman' package on Arch-based systems."
        ),
        "err_aur_makepkg_failed": "Generating .SRCINFO failed:\n{error}",
        "err_aur_no_remote": (
            "No remote ('origin') configured in the AUR folder. "
            "Please check whether the folder was correctly cloned from "
            "ssh://aur@aur.archlinux.org/<package>.git."
        ),
        "msg_aur_check_status_error": "Error during AUR status check:\n{error}",
        "msg_aur_pull_error": "Error pulling from the AUR:\n{error}",
        "msg_aur_add_files_title": "Add new file(s) to git?",
        "msg_aur_add_files_text": (
            "The following file(s) are not yet part of the git repo and are "
            "likely needed:\n\n{files}\n\nAdd them to git now (git add)?"
        ),
        "msg_aur_add_files_error": "Error adding the file(s):\n{error}",
        "msg_aur_cleanup_title": "Delete build artifacts?",
        "msg_aur_cleanup_text": (
            "The following untracked file(s)/folder(s) were likely created by "
            "'updpkgsums' or 'makepkg' and do not belong in the AUR git repo:\n\n"
            "{files}\n\nDelete them permanently now?"
        ),
        "msg_aur_cleanup_partial_error": (
            "Some files/folders could not be deleted:\n{errors}"
        ),
    },
}

_current_language = None


def _detect_system_language():
    """Ermittelt die Systemsprache als Fallback (z.B. beim ersten Start)."""
    try:
        lang = locale.getlocale()[0] or locale.getdefaultlocale()[0] or ""
    except Exception:
        lang = ""
    lang = (lang or "").lower()
    for code in TRANSLATIONS:
        if lang.startswith(code):
            return code
    return DEFAULT_LANGUAGE


def _load_saved_language():
    if not os.path.exists(SETTINGS_FILE):
        return None
    try:
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
        lang = data.get("language")
        if lang in TRANSLATIONS:
            return lang
    except (json.JSONDecodeError, IOError):
        pass
    return None


def get_current_language():
    """Liefert den aktuell aktiven Sprachcode (gespeicherte Auswahl > Systemsprache)."""
    global _current_language
    if _current_language is None:
        _current_language = _load_saved_language() or _detect_system_language()
    return _current_language


def set_language(lang_code):
    """Setzt die aktive Sprache und speichert sie dauerhaft in settings.json."""
    global _current_language
    if lang_code not in TRANSLATIONS:
        return
    _current_language = lang_code
    os.makedirs(CONFIG_DIR, exist_ok=True)
    data = {}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
    data["language"] = lang_code
    with open(SETTINGS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def tr(key, **kwargs):
    """Übersetzt einen Schlüssel in die aktuell aktive Sprache.
    Fällt auf Deutsch zurück, falls der Schlüssel in der aktiven Sprache
    fehlt, und auf den Schlüssel selbst, falls er nirgends existiert."""
    lang = get_current_language()
    table = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key)
    if text is None:
        text = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text

