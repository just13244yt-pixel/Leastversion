import curses
import subprocess
import os
import json

MENU_FILE = "menu_data.json"
menus = []
user_name = ""

def load_data():
    global menus, user_name
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r") as f:
                data = json.load(f)
                menus = data.get("menus", [])
                user_name = data.get("user_name", "")
        except:
            menus = []
            user_name = ""
    else:
        menus = []
        user_name = ""

def save_data():
    with open(MENU_FILE, "w") as f:
        json.dump({"user_name": user_name, "menus": menus}, f, indent=4)

def draw_screen(stdscr, selected):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
    stdscr.attron(curses.color_pair(1))
    if user_name:
        stdscr.addstr(0, w//2 - len(f"Name: {user_name}")//2, f"Name: {user_name}")
    stdscr.attroff(curses.color_pair(1))

    for i, menu in enumerate(menus):
        x = w//2 - 20
        y = 2 + i
        line = f"{menu['name']} -> {menu['cmd']}"
        if i == selected:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, x, line)
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(y, x, line)

    hint = "B = Eintrag hinzufügen | ESC = Befehl eingeben+speichern | ENTER = Start"
    stdscr.addstr(h-2, 2, hint)
    stdscr.refresh()

def input_screen(stdscr, prompt):
    stdscr.clear()
    h, w = stdscr.getmaxyx()
    stdscr.addstr(h//2 - 1, w//2 - len(prompt)//2, prompt)
    curses.echo()
    value = stdscr.getstr(h//2 + 1, w//2 - 20, 60).decode()
    curses.noecho()
    return value

def run_command(cmd):
    curses.endwin()
    try:
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print("Fehler:", e)
    input("ENTER drücken um zurückzukehren...")

def main(stdscr):
    global user_name
    curses.curs_set(0)
    selected = 0

    if not user_name:
        user_name = input_screen(stdscr, "Bitte deinen Namen eingeben")
        save_data()

    while True:
        draw_screen(stdscr, selected)
        key = stdscr.getch()

        if key in (ord('b'), ord('B')):
            # Menüeintrag hinzufügen
            name = input_screen(stdscr, "Name für Menüeintrag eingeben")
            cmd = input_screen(stdscr, "Befehl eingeben")
            menus.append({"name": name, "cmd": cmd})
            save_data()

        elif key == 27:  # ESC
            # ESC führt jetzt Ctrl+A aus: Befehl eingeben, speichern und ausführen
            cmd = input_screen(stdscr, "Befehl eingeben und speichern")
            menus.append({"name": f"{user_name}'s Befehl", "cmd": cmd})
            save_data()
            run_command(cmd)

        elif key in (curses.KEY_UP, curses.KEY_DOWN) and menus:
            if key == curses.KEY_UP:
                selected = (selected - 1) % len(menus)
            else:
                selected = (selected + 1) % len(menus)

        elif key in (curses.KEY_ENTER, 10, 13) and menus:
            run_command(menus[selected]["cmd"])

load_data()
curses.wrapper(main)