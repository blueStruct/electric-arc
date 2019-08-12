from threading import Thread
from queue import Queue
import subprocess


questions = {
    'aur-helper': (
        'Which AUR-helper do you want?',
    ),
    'powerpill': (
        'Do you want to use Powerpill?',
    )
}


def is_true(v):
    if v in ('true', 'yes', 'y'):
        return True
    else:
        return False


def run(user_input):
    if user_input == 'test':
        sh('notify-send test')




