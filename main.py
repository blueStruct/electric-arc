#!/usr/bin/python3

from curses import *
from curses.ascii import isprint
import subprocess

from lib import start_bg_thread, handle_input


## constants
PROMPT = '> '
PADDING_X = 2
PADDING_Y = 1
PADDING_I = 1
H_TEXT = 2
H_INPUT = 1


class AppState:
    fg_state = 'aur_helper'
    bg_state = 'waiting'
    password_mode = False

    bg_thread = None
    task_chan = None
    status_chan = None
    out_chan = None
    pipe = None

    user_input = ''
    commited_user_input = ''

    text = ('Hello World!',)
    status_msg = ''
    bg_output = ['test output']

    def __init__(self):
        (
            self.bg_thread,
            self.task_chan,
            self.status_chan,
            self.out_chan
        ) = start_bg_thread()



def sh(p):
    subprocess.run(p, shell=True)


def dbg(t):
    with open('debug', mode='w') as f:
        f.write(str(t))


def main(screen):
    ## setup ncurses
    screen.nodelay(True)
    use_default_colors()
    curs_set(0)

    init_color(COLOR_RED, 1000, 0, 0)    # redefine red
    init_color(COLOR_CYAN, 0, 900, 1000) # redefine cyan

    init_pair(1, COLOR_RED, -1)
    init_pair(2, COLOR_CYAN, -1)

    white = color_pair(0)
    red = color_pair(1)
    cyan = color_pair(2)

    state = AppState()


    while True:
        ## geometry and setup
        h, b = screen.getmaxyx()
        b_sub = b - 2*PADDING_X
        b_input = b_sub - len(PROMPT)

        h_output = h - H_TEXT - H_INPUT - (PADDING_I*2+3) - 2*PADDING_Y
        y_input = PADDING_Y + H_TEXT
        y_output = PADDING_Y + H_TEXT + H_INPUT + (PADDING_I*2+3)


        ## handle input and call run function
        key = screen.getch()
        if key == 9: # TAB disabled
            pass
        elif isprint(key) and len(state.user_input) < b_input:
            state.user_input += chr(key)
        elif key in (KEY_ENTER, 10):
            state.commited_user_input = state.user_input
            state.user_input = ''
        elif key in (KEY_BACKSPACE, 127):
            state.user_input = state.user_input[:-1]

        if state.commited_user_input in ('exit', 'quit', 'q'):
            break
        else:
            (
                state.text,
                state.status_msg,
                state.bg_output
            ) = handle_input(
                state.commited_user_input,
                state.fg_state,
                state.bg_state
            )
            state.commited_user_input = ''


        ## get status message from status channel
        try:
            state.status_msg = state.status_chan.get(block=False)
        except Empty:
            pass


        ## get output from out channel and do line wrapping
        if state.pipe == None:
            try:
                state.pipe = state.out_chan.get(block=False)
            except Empty:
                pass
        if state.pipe != None:
            with open(state.pipe) as f:
                for line in f:
                    div, mod = divmod(len(line), b_sub)
                    for i in range(div+1):
                        if i == div:
                            state.bg_output.append(line[(b_sub*i):(b_sub*i + mod)])
                        else:
                            state.bg_output.append(line[(b_sub*i):(b_sub*(i+1))])

                state.bg_output = state.bg_output[-100:]


        ## window content
        # print text
        screen.attron(cyan)
        if len(state.text) == 2:
            screen.addnstr(PADDING_Y, PADDING_X, state.text[0], b_sub)
            screen.addnstr(PADDING_Y + 1, PADDING_X, state.text[1], b_sub)
        else:
            screen.redrawln(PADDING_Y, 1)
            screen.addnstr(PADDING_Y + 1, PADDING_X, state.text[0], b_sub)
        screen.attroff(cyan)

        # print prompt
        screen.attron(cyan)
        screen.addstr(y_input, PADDING_X, PROMPT)
        screen.attroff(cyan)

        # print user_input
        screen.attron(white)
        for i in range(b_input):
            screen.delch(y_input, PADDING_X + len(PROMPT) + i)
        if not state.password_mode:
            screen.addnstr(y_input, PADDING_X + len(PROMPT), state.user_input, b_input)
        else:
            for (i, _) in enumerate(state.user_input):
                screen.addch(y_input, PADDING_X + len(PROMPT) + i, '*')
        screen.attroff(white)

        # print divider
        screen.attron(white)
        for i in range(b_sub):
            screen.addch(PADDING_Y + H_TEXT + H_INPUT + PADDING_I, PADDING_X + i, '\u2500')
        screen.attroff(white)

        # print status message
        screen.attron(cyan)
        screen.addnstr(PADDING_Y + H_TEXT + H_INPUT + 2*PADDING_I + 1, PADDING_X,
                  state.status_msg, b_sub)
        screen.attroff(cyan)

        # print output
        for (i, line) in enumerate(state.bg_output[-h_output:]):
            screen.addnstr(y_output + i, PADDING_X, line, b_sub)


wrapper(main)
