#!/usr/bin/python3

from curses import *
from curses.ascii import isprint
from queue import Empty
import subprocess
import os

from lib import start_bg_thread, handle_input


## constants ###################################################################
PROMPT = '> '
PADDING_X = 2
PADDING_Y = 1
PADDING_I = 1
H_TEXT = 2
H_INPUT = 1
MIN_H = H_TEXT + H_INPUT + 6
LINES_OUTPUT_HISTORY = 100

Y_INPUT = PADDING_Y + H_TEXT
Y_DIVIDER = PADDING_Y + H_TEXT + H_INPUT + PADDING_I
Y_STATUS_MSG = PADDING_Y + H_TEXT + H_INPUT + 2*PADDING_I + 1
Y_OUTPUT = PADDING_Y + H_TEXT + H_INPUT + (PADDING_I*2+3)


class AppState:
    fg_state = 'aur_helper'
    password_mode = False
    exiting = False

    bg_thread = None
    task_chan = None        # submit tasks to bg-thread
    status_chan = None      # submit current status back to ui
    out_chan = None         # submit output lines from bg-thread to ui
    kill_chan = None        # send kill signal to bg-thread

    user_input = ''
    commited_user_input = ''

    text = ('',)
    status_msg = ''
    bg_output = []

    def __init__(self):
        (
            self.bg_thread,
            self.task_chan,
            self.status_chan,
            self.out_chan,
            self.kill_chan,
        ) = start_bg_thread()


def main(screen):
    ## setup ncurses ##########################################################
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

    # mainloop, wrapped in try statement to catch keyboard interrupt
    try:
        while True:
            ## exit when requested and bg-thread is closed #####################
            if state.exiting and not state.bg_thread.is_alive():
                break


            ## user input ######################################################
            # calculate b_input
            h, b = screen.getmaxyx()
            b_sub = b - 2*PADDING_X
            b_input = b_sub - len(PROMPT)

            # get keys
            key = screen.getch()
            # Tab disabled
            if key == 9:
                pass
            # add printable characters to user_input
            elif isprint(key) and len(state.user_input) < b_input:
                state.user_input += chr(key)
            # Backspace
            elif key in (KEY_BACKSPACE, 127):
                state.user_input = state.user_input[:-1]
            # Enter: commit user input
            elif key in (KEY_ENTER, 10):
                state.commited_user_input = state.user_input
                state.user_input = ''

            # exit
            if state.commited_user_input in ('exit', 'quit'):
                state.status_msg = ('Waiting for tasks to finish then exiting...'
                                    ' (cancel for immediate exit)')
                state.task_chan.put(None)
                state.exiting = True
            # cancel
            elif state.commited_user_input in ('cancel', 'abort'):
                state.task_chan.put(None)
                state.kill_chan.put(True)
                state.exiting = True
            # normal user input, disabled when exiting
            elif not state.exiting:
                state.text = handle_input(
                    state.commited_user_input,
                    state.fg_state,
                    state.task_chan,
                )

            # reset commited user input after handling it
            state.commited_user_input = ''


            ## rendering #######################################################
            # update window dimensions and b_sub
            h, b = screen.getmaxyx()
            b_sub = b - 2*PADDING_X

            # only print anything if window big enough
            if h > MIN_H:
                # print text
                for i in range(b_sub):
                    screen.delch(PADDING_Y, PADDING_X + i)
                    screen.delch(PADDING_Y + 1, PADDING_X + i)

                screen.attron(cyan)
                if len(state.text) == 2:
                    screen.addnstr(PADDING_Y, PADDING_X, state.text[0], b_sub)
                    screen.addnstr(PADDING_Y + 1, PADDING_X, state.text[1], b_sub)
                else:
                    screen.addnstr(PADDING_Y + 1, PADDING_X, state.text[0], b_sub)
                screen.attroff(cyan)

                # print prompt
                screen.attron(cyan)
                screen.addstr(Y_INPUT, PADDING_X, PROMPT)
                screen.attroff(cyan)

                # update window dimensions, b_sub and b_input
                h, b = screen.getmaxyx()
                b_sub = b - 2*PADDING_X
                b_input = b_sub - len(PROMPT)

                # print user_input
                for i in range(b_input):
                    screen.delch(Y_INPUT, PADDING_X + len(PROMPT) + i)

                screen.attron(white)
                if not state.password_mode:
                    screen.addnstr(Y_INPUT, PADDING_X + len(PROMPT),
                                   state.user_input, b_input)
                else:
                    screen.addstr(Y_INPUT, PADDING_X + len(PROMPT),
                                  '*' * len(state.user_input))
                screen.attroff(white)

                # print divider
                screen.attron(white)
                screen.addstr(Y_DIVIDER, PADDING_X, '\u2500' * b_sub)
                screen.attroff(white)

                # get status message from status channel
                try:
                    state.status_msg = state.status_chan.get_nowait()
                except Empty:
                    pass

                # print status message
                for i in range(b_sub):
                    screen.delch(Y_STATUS_MSG, PADDING_X + i)
                screen.attron(cyan)
                screen.addnstr(Y_STATUS_MSG, PADDING_X, state.status_msg, b_sub)
                screen.attroff(cyan)

                # get new output line
                try:
                    new_line = state.out_chan.get_nowait()
                    state.bg_output.append(new_line)
                    # remove old lines from output buffer
                    state.bg_output = state.bg_output[-LINES_OUTPUT_HISTORY:]
                except Empty:
                    pass

                # update h_output
                h, b = screen.getmaxyx()
                h_output = h - H_TEXT - H_INPUT - (PADDING_I*2+3) - 2*PADDING_Y

                # print output
                for (y, line) in enumerate(state.bg_output[-h_output:]):
                    for x in range(b_sub):
                        screen.delch(Y_OUTPUT + y, PADDING_X + x)
                    screen.addnstr(Y_OUTPUT + y, PADDING_X, line, b_sub)
            else:
                pass

    # cancel when keyboard interrupt
    except KeyboardInterrupt:
        state.task_chan.put(None)
        state.kill_chan.put(True)
        state.exiting = True

wrapper(main)
