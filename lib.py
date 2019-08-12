from threading import Thread
from queue import Queue
import subprocess

import os.path
import os


QUESTIONS = {
    'aur_helper': (
        'Which AUR-helper do you want to use?',
    ),
    'powerpill': (
        'Do you want to use Powerpill?',
    ),
    'pacman_cache': (
        'Do you want your system to provide a pacman cache on your LAN?',
    ),
    'fixed_ip': (
        'You should choose a fixed IP address on your LAN, so the clients can easily',
        'reach your pacman cache. Do you want a fixed IP address?',
    ),
    'ufw_open_ports': (
        'Do you want ufw to allow access from your LAN, so your cache can be reached?',
    ),
    'user_account': (
        'Let\'s setup your user account',
    ),
    'user_name': (
        'enter username',
    ),
    'hide_pw': (
        'For your password entry:',
        'Do you want to see asterisks?',
    ),
    'pw': (
        'enter password',
    ),
    'pw_again': (
        'enter password again'
    ),
    'pw_not_match': (
        'Entries did not match. Try again'
    ),
    'sudo': (
        'Should this user account have sudo access?',
    ),
    'shell': (
        'Which shell do you want to use?',
    ),
}


STATUS_MSG = {
    'waiting': 'waiting for user input...',
    'aur_helper': 'installing AUR-Helper...',
}


TEST = True


## types of tasks
class HelperTask:
    func = None
    args = ()

    def __init__(self, f, a):
        self.func = f
        self.args = a


class ShellTask:
    cmd = ''
    status_msg = ''

    def __init__(self, c, s):
        self.cmd = c
        self.status_msg = s


## helper functions
def is_true(v):
    if v in ('true', 'yes', 'y'):
        return True
    else:
        return False


def sh(cmd):
    return subprocess.run(cmd, shell=True)


def test_function(func):
    def disabled():
        pass

    if TEST == True:
        return disabled
    else:
        return func


def check_installed(pack):
    if sh('pacman -Qq {} 2> /dev/null'.format(pack)).returncode:
        return True
    else:
        return False


#TODO can't run makepkg as root
@test_function
def install_aur_helper(pack):
    sh((
        'cd /tmp;'
        'git clone https://aur.archlinux.org/{}.git;'
        'cd {};'
        'makepkg -si'
        'cd /root'
    ).format(pack))


def install_pck(prog, pack):
    sh('{} --noconfirm --needed -S {}'.format(prog, pack))
    return 'installing {}...'.format(pack)


def batch_install(prog, packages):
    sh('cat {} | {} --noconfirm --needed -S -'.format(packages, prog))


def setup_system():
    pass #TODO


def change_system_configs():
    pass #TODO


def place_systemd_units():
    sh((
        'for i in custom-systemd-units/*;'
        'do cp -i $i /etc/systemd/system;'
        'done'
    ))


def setup_lan_pacman_cache():
    msg('setting up LAN Pacman Cache')
    install_pck('powerpill', 'darkhttpd')
    sh('ln -s /var/lib/pacman/sync/*.db /var/cache/pacman/pkg')
    # placing/enabling the unit file along with the others
    # in custom-systemd-units


def enable_services():
    # systemd units provided by upstream
    if os.path.exists('services'):
        sh((
            'for i in $(cat services);'
            'do systemctl --now enable $i;'
            'done'
        ))

    # custom systemd unit
    sh((
        'for i in custom-systemd-units/*;'
        'do systemctl --now enable $i;'
        'done'
    ))


## run functions
def run_bg_thread(task_chan, status_chan, out_chan):
    while True:
        task = task_chan.get()
        if task is None:
            break
        if type(task) == HelperTask:
            task.func(task.args)
            task_chan.task_done()
        elif type(task) == ShellTask:
            proc = subprocess.Popen(task.cmd, shell=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT)
            pipe, _ = proc.communicate()
            out_chan.put(pipe)
            status_chan.put(task.status_msg)
            proc.wait()
            task_chan.task_done()


def start_bg_thread():
    task_chan = Queue()
    status_chan = Queue()
    out_chan = Queue()
    bg_thread = Thread(target=run_bg_thread,
                       args=(task_chan, status_chan, out_chan))

    return bg_thread, task_chan, status_chan, out_chan


def handle_input(user_input, fg_state, bg_state):
    if user_input == 'test':
        sh('notify-send test')
    # if fg_state == 'aur_helper':
    #     bg_state = 'aur_helper'

    return QUESTIONS[fg_state]




