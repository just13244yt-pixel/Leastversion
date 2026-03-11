import curses
import subprocess
import os
import sys
import json

MENU_FILE = "menus.json"
menus = []


def load_menus():
    global menus
    if os.path.exists(MENU_FILE):
        try:
            with open(MENU_FILE, "r") as f:
                menus = json.load(f)
        except:
            menus = []
    else:
        menus = []


def save_menus():
    with open(MENU_FILE, "w") as f:
        json.dump(menus, f, indent=4)


def draw_main(stdscr, selected):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)

    title = "JUST OS"
    stdscr.attron(curses.color_pair(1))
    stdscr.addstr(1, w//2 - len(title)//2, title)
    stdscr.attroff(curses.color_pair(1))

    for i, menu in enumerate(menus):
        x = w//2 - 10
        y = 4 + i

        if i == selected:
            stdscr.attron(curses.A_REVERSE)
            stdscr.addstr(y, x, menu["name"])
            stdscr.attroff(curses.A_REVERSE)
        else:
            stdscr.addstr(y, x, menu["name"])

    hint = "B = Menü hinzufügen | ENTER = Start | ESC = Neustart"
    stdscr.addstr(h-2, w-len(hint)-2, hint)

    stdscr.refresh()


def input_screen(stdscr, text):
    stdscr.clear()
    h, w = stdscr.getmaxyx()

    stdscr.addstr(h//2 - 1, w//2 - len(text)//2, text)

    curses.echo()
    value = stdscr.getstr(h//2 + 1, w//2 - 20, 40).decode()
    curses.noecho()

    return value


def restart_justos():
    curses.endwin()
    os.execv(sys.executable, [sys.executable] + sys.argv)


def run_menu(cmd):
    curses.endwin()

    try:
        subprocess.run(cmd, shell=True)
    except Exception as e:
        print("Fehler beim Starten:", e)

    input("ENTER drücken um zurückzukehren...")


def main(stdscr):

    curses.curs_set(0)
    curses.start_color()

    selected = 0

    while True:

        draw_main(stdscr, selected)

        key = stdscr.getch()

        if key == 27:  # ESC
            restart_justos()

        elif key == curses.KEY_UP and menus:
            selected = (selected - 1) % len(menus)

        elif key == curses.KEY_DOWN and menus:
            selected = (selected + 1) % len(menus)

        elif key == ord("b") or key == ord("B"):

            name = input_screen(stdscr, "Name eingeben")
            cmd = input_screen(stdscr, "Befehl eingeben")

            menus.append({
                "name": name,
                "cmd": cmd
            })

            save_menus()  # SOFORT SPEICHERN

        elif key == curses.KEY_ENTER or key == 10 or key == 13:

            if menus:
                run_menu(menus[selected]["cmd"])
                stdscr.clear()

        elif key == ord("q") or key == ord("Q"):
            restart_justos()


load_menus()

while True:
    curses.wrapper(main)