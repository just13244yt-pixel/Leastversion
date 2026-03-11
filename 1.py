#!/usr/bin/env python3
import os
import curses
import shutil
import json
import subprocess
import platform

COMMANDS_FILE = "commands.json"

# ---------- Helferfunktionen ----------
def get_items(path):
    try:
        items = os.listdir(path)
        items.sort()
        return items
    except PermissionError:
        return []

def human_size(size):
    for unit in ['B','KB','MB','GB','TB']:
        if size < 1024:
            return f"{size} {unit}"
        size /= 1024
    return f"{size} TB"

def save_command(cmd):
    with open(COMMANDS_FILE, "w") as f:
        json.dump({"command": cmd}, f)

def load_command():
    if os.path.exists(COMMANDS_FILE):
        with open(COMMANDS_FILE, "r") as f:
            data = json.load(f)
            return data.get("command", "")
    return ""

def draw_window(stdscr, current_path, items, selected, system_platform, offset):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    visible_height = height - 13  # Platz für Befehle und Titel

    # Titel
    stdscr.addstr(0, 0, f"Pfad: {current_path}"[:width-1], curses.A_BOLD)

    # Dateien (sichtbarer Bereich)
    for idx in range(offset, min(offset + visible_height, len(items))):
        line_y = idx - offset + 2
        item = items[idx]
        item_path = os.path.join(current_path, item)
        size_str = ""
        if os.path.isdir(item_path):
            icon = "[DIR]" if system_platform == "Windows" else "📁"
        else:
            icon = "[FIL]" if system_platform == "Windows" else "📄"
            try:
                size_str = human_size(os.path.getsize(item_path))
            except:
                size_str = ""
        line = f"{icon} {item:<40} {size_str:>10}"[:width-1]
        if idx == selected:
            stdscr.addstr(line_y, 0, line, curses.color_pair(1))
        else:
            stdscr.addstr(line_y, 0, line)

    # Befehle unten
    help_start = max(visible_height + 2, len(items) - offset + 3)
    stdscr.hline(help_start-1, 0, "-", width)
    commands = [
        ("↑ / ↓", "Auswahl bewegen"),
        ("Enter", "Ordner öffnen / Datei öffnen"),
        ("Backspace", "In übergeordneten Ordner"),
        ("d", "Löschen"),
        ("c", "Kopieren"),
        ("x", "Ausschneiden"),
        ("v", "Einfügen"),
        ("r", "Umbenennen"),
        ("e", "Editieren"),
        ("n", "Neue Datei erstellen"),
        ("f", "Neuen Ordner erstellen"),
        ("Ctrl+A", "Eigenen Befehl eingeben (JSON)"),
        ("ESC", "Befehl ausführen"),
        ("q", "Beenden"),
    ]
    for i, (key, desc) in enumerate(commands):
        line_y = help_start + i
        if line_y >= height:
            break
        line = f"{key:<12} : {desc}"[:width-1]
        stdscr.addstr(line_y, 0, line)

    stdscr.refresh()

# ---------- Hauptfunktion ----------
def main(stdscr):
    curses.curs_set(0)
    curses.start_color()
    curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)

    current_path = os.getcwd()
    selected = 0
    clipboard = None
    clipboard_cut = False
    system_platform = platform.system()
    offset = 0  # für Scrollen

    while True:
        items = get_items(current_path)
        height, _ = stdscr.getmaxyx()
        visible_height = height - 13

        # Offset anpassen für Scrollen
        if selected < offset:
            offset = selected
        elif selected >= offset + visible_height:
            offset = selected - visible_height + 1

        draw_window(stdscr, current_path, items, selected, system_platform, offset)
        key = stdscr.getch()

        # Navigation
        if key == curses.KEY_UP:
            selected = max(0, selected-1)
        elif key == curses.KEY_DOWN:
            selected = min(len(items)-1, selected+1)
        elif key in [curses.KEY_ENTER, 10, 13]:
            if len(items) == 0: continue
            chosen_path = os.path.join(current_path, items[selected])
            if os.path.isdir(chosen_path):
                current_path = chosen_path
                selected = 0
                offset = 0
        elif key in [curses.KEY_BACKSPACE, 127, 8]:
            parent = os.path.dirname(current_path)
            if os.path.exists(parent) and parent != current_path:
                current_path = parent
                selected = 0
                offset = 0
        elif key == ord('q'):
            break

        # Dateiaktionen
        elif key == ord('d'):
            if len(items) == 0: continue
            chosen_path = os.path.join(current_path, items[selected])
            curses.echo()
            stdscr.addstr(visible_height+3, 0, f"Willst du '{items[selected]}' wirklich löschen? (j/n): ")
            stdscr.refresh()
            answer = stdscr.getstr().decode().lower()
            curses.noecho()
            if answer == "j":
                try:
                    if os.path.isdir(chosen_path):
                        shutil.rmtree(chosen_path)
                    else:
                        os.remove(chosen_path)
                    selected = 0
                except Exception as e:
                    stdscr.addstr(visible_height+4, 0, f"Fehler: {e}"[:curses.COLS-1])
                    stdscr.getch()
        elif key == ord('c'):
            if len(items) == 0: continue
            clipboard = os.path.join(current_path, items[selected])
            clipboard_cut = False
        elif key == ord('x'):
            if len(items) == 0: continue
            clipboard = os.path.join(current_path, items[selected])
            clipboard_cut = True
        elif key == ord('v'):
            if clipboard:
                dest = os.path.join(current_path, os.path.basename(clipboard))
                try:
                    if os.path.isdir(clipboard):
                        if clipboard_cut:
                            shutil.move(clipboard, dest)
                        else:
                            shutil.copytree(clipboard, dest)
                    else:
                        if clipboard_cut:
                            shutil.move(clipboard, dest)
                        else:
                            shutil.copy2(clipboard, dest)
                    if clipboard_cut:
                        clipboard = None
                except Exception as e:
                    stdscr.addstr(visible_height+3, 0, f"Fehler: {e}"[:curses.COLS-1])
                    stdscr.getch()
        elif key == ord('r'):
            if len(items) == 0: continue
            chosen = items[selected]
            stdscr.addstr(visible_height+3, 0, "Neuer Name: " + " "*50)
            curses.echo()
            new_name = stdscr.getstr(visible_height+3, 12, 50).decode()
            curses.noecho()
            if new_name:
                try:
                    os.rename(os.path.join(current_path, chosen), os.path.join(current_path, new_name))
                except Exception as e:
                    stdscr.addstr(visible_height+4, 0, f"Fehler: {e}"[:curses.COLS-1])
                    stdscr.getch()
        elif key == ord('e'):
            if len(items) == 0: continue
            chosen = items[selected]
            chosen_path = os.path.join(current_path, chosen)
            curses.endwin()
            if system_platform == "Windows":
                os.system(f'notepad "{chosen_path}"')
            else:
                os.system(f'nano "{chosen_path}"')
            stdscr = curses.initscr()

        # Neue Datei erstellen
        elif key == ord('n'):
            curses.echo()
            stdscr.addstr(visible_height+3, 0, "Dateiname (inkl. Endung z.B. .txt): " + " "*50)
            stdscr.move(visible_height+3, 35)
            filename = stdscr.getstr().decode()
            curses.noecho()
            if filename:
                try:
                    open(os.path.join(current_path, filename), 'w').close()
                except Exception as e:
                    stdscr.addstr(visible_height+4, 0, f"Fehler: {e}"[:curses.COLS-1])
                    stdscr.getch()

        # Neuer Ordner erstellen
        elif key == ord('f'):
            curses.echo()
            stdscr.addstr(visible_height+3, 0, "Name des neuen Ordners: " + " "*50)
            stdscr.move(visible_height+3, 28)
            foldername = stdscr.getstr().decode()
            curses.noecho()
            if foldername:
                try:
                    os.mkdir(os.path.join(current_path, foldername))
                except Exception as e:
                    stdscr.addstr(visible_height+4, 0, f"Fehler: {e}"[:curses.COLS-1])
                    stdscr.getch()

        # STRG+A für eigenen Befehl
        elif key == 1:  # Ctrl+A
            curses.echo()
            stdscr.addstr(visible_height+3, 0, "Eigenen Befehl eingeben: " + " "*50)
            stdscr.move(visible_height+3, 27)
            cmd = stdscr.getstr().decode()
            save_command(cmd)
            curses.noecho()
            stdscr.addstr(visible_height+4, 0, f"Befehl gespeichert in {COMMANDS_FILE}"[:curses.COLS-1])
            stdscr.getch()

        # ESC für Befehl ausführen
        elif key == 27:  # ESC
            cmd = load_command()
            if cmd:
                curses.endwin()
                print(f"Führe Befehl aus: {cmd}")
                subprocess.call(cmd, shell=True)
                input("Drücke Enter um zurückzukehren...")
                stdscr = curses.initscr()

if __name__ == "__main__":
    try:
        import curses
    except ImportError:
        if platform.system() == "Windows":
            print("Bitte installieren Sie 'windows-curses' mit pip: pip install windows-curses")
        raise
    curses.wrapper(main)