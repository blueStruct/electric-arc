#!/usr/bin/python3

from curses import *
from curses.ascii import isprint
from queue import Empty
import subprocess
import os

from lib import start_bg_thread, handle_input


## constants
PROMPT = '> '
PADDING_X = 2
PADDING_Y = 1
PADDING_I = 1
H_TEXT = 2
H_INPUT = 1
LINES_OUTPUT_HISTORY = 100

Y_INPUT = PADDING_Y + H_TEXT
Y_OUTPUT = PADDING_Y + H_TEXT + H_INPUT + (PADDING_I*2+3)


class AppState:
    fg_state = 'aur_helper'
    password_mode = False

    bg_thread = None
    task_chan = None        # submit tasks to bg-thread
    status_chan = None      # submit current task back to ui
    out_chan = None         # submit pipes of bg-thread to ui
    done_chan = None        # tell ui that task done and to get new pipe
    pipe = None             # current pipe to read bg-output from
    pipe_pos = 0

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
            self.out_chan,
            self.done_chan,
        ) = start_bg_thread()


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
            state.status_msg = 'Exiting...'
            state.task_chan.put(None)
            state.bg_thread.join()
            break
        else:
            state.text = handle_input(
                state.commited_user_input,
                state.fg_state,
                state.task_chan,
            )
            state.commited_user_input = ''


        ## get status message from status channel
        try:
            state.status_msg = state.status_chan.get_nowait()
        except Empty:
            pass


        ## get output from out channel and do line wrapping
        # remove old pipe when done
        try:
            if state.done_chan.get_nowait():
                state.pipe = None
        except Empty:
            pass

        # try to get new pipe if needed
        if state.pipe == None:
            try:
                state.pipe = state.out_chan.get_nowait()
                state.pipe_pos = 0
            except Empty:
                pass
        # get output from pipe, increase line counter
        else:
            if len(state.pipe) > state.pipe_pos:
                state.bg_output.append(state.pipe[state.pipe_pos:])
                state.pipe_pos = len(state.pipe)
                # remove superfluous lines from output buffer
                state.bg_output = state.bg_output[-LINES_OUTPUT_HISTORY:]

            # TODO
            # for line in state.pipe:
            #     div, mod = divmod(len(line), b_sub)
            #     for i in range(div+1):
            #         if i == div:
            #             state.bg_output.append(line[(b_sub*i):(b_sub*i + mod)])
            #         else:
            #             state.bg_output.append(line[(b_sub*i):(b_sub*(i+1))])


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
        screen.addstr(Y_INPUT, PADDING_X, PROMPT)
        screen.attroff(cyan)

        # print user_input
        screen.attron(white)
        for i in range(b_input):
            screen.delch(Y_INPUT, PADDING_X + len(PROMPT) + i)
        if not state.password_mode:
            screen.addnstr(Y_INPUT, PADDING_X + len(PROMPT), state.user_input, b_input)
        else:
            for (i, _) in enumerate(state.user_input):
                screen.addch(Y_INPUT, PADDING_X + len(PROMPT) + i, '*')
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
            screen.addnstr(Y_OUTPUT + i, PADDING_X, line, b_sub)


wrapper(main)
