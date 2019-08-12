#!/usr/bin/python3

from curses import *
from curses.ascii import isprint

from lib import run


PROMPT = '> '
PADDING_X = 2
PADDING_Y = 1
PADDING_I = 1
H_TEXT = 2
H_INPUT = 1


def main(s):
    ## setup ncurses
    s.nodelay(True)
    use_default_colors()
    curs_set(0)

    init_color(COLOR_RED, 1000, 0, 0)    # redefine red
    init_color(COLOR_CYAN, 0, 900, 1000) # redefine cyan

    init_pair(1, COLOR_RED, -1)
    init_pair(2, COLOR_CYAN, -1)

    white = color_pair(0)
    red = color_pair(1)
    cyan = color_pair(2)

    ## application state
    user_input = ''
    commited_user_input = ''
    password_mode = False


    while True:
        ## geometry and setup
        h, b = s.getmaxyx()
        b_sub = b - 2*PADDING_X
        b_input = b_sub - len(PROMPT)

        h_output = h - H_TEXT - H_INPUT - (PADDING_I*2+3) - 2*PADDING_Y
        y_input = PADDING_Y + H_TEXT
        y_output = PADDING_Y + H_TEXT + H_INPUT + (PADDING_I*2+3)


        ## handle input and call run function
        key = s.getch()
        if key == 9: # TAB disabled
            pass
        elif isprint(key) and len(user_input) < b_input: # printable keys
            user_input += chr(key)
        elif key in (KEY_ENTER, 10): # ENTER
            commited_user_input = user_input
            user_input = ''
        elif key in (KEY_BACKSPACE, 127): # BACKSPACE
            user_input = user_input[:-1]

        if commited_user_input in ('exit', 'quit', 'q'):
            break
        else:
            run(commited_user_input)
            commited_user_input = ''


        ## define text
        text = ['Hello World!', '']         # get from run function
        status = 'downloading packages...'  # get from bg thread
        output = []                         # get from bg thread


        ## do line wrapping on output
        with open('lorem-ipsum') as f:
            for line in f:
                div, mod = divmod(len(line), b_sub)
                for i in range(div+1):
                    if i == div:
                        output.append(line[(b_sub*i):(b_sub*i + mod)])
                    else:
                        output.append(line[(b_sub*i):(b_sub*(i+1))])


        ## window content
        # print text
        s.attron(cyan)
        if text[1] != '':
            s.addnstr(PADDING_Y, PADDING_X, text[0], b_sub)
            s.addnstr(PADDING_Y + 1, PADDING_X, text[1], b_sub)
        else:
            s.redrawln(PADDING_Y, 1)
            s.addnstr(PADDING_Y + 1, PADDING_X, text[0], b_sub)
        s.attroff(cyan)

        # print prompt
        s.attron(cyan)
        s.addstr(y_input, PADDING_X, PROMPT)
        s.attroff(cyan)

        # print user_input
        s.attron(white)
        for i in range(b_input):
            s.delch(y_input, PADDING_X + len(PROMPT) + i)
        if not password_mode:
            s.addnstr(y_input, PADDING_X + len(PROMPT), user_input, b_input)
        else:
            for (i, _) in enumerate(user_input):
                s.addch(y_input, PADDING_X + len(PROMPT) + i, '*')
        s.attroff(white)

        # print divider
        s.attron(white)
        for i in range(b_sub):
            s.addch(PADDING_Y + H_TEXT + H_INPUT + PADDING_I, PADDING_X + i, '\u2500')
        s.attroff(white)

        # print status message
        s.attron(cyan)
        s.addnstr(PADDING_Y + H_TEXT + H_INPUT + 2*PADDING_I + 1, PADDING_X, status, b_sub)
        s.attroff(cyan)

        # print output
        for (i, line) in enumerate(output):
            s.addnstr(y_output + i, PADDING_X, line, b_sub)


wrapper(main)
