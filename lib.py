from threading import Thread
from queue import Queue, Empty
import subprocess
import pexpect

from time import sleep
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
def sh(cmd):
    return subprocess.run(cmd, shell=True)

def dbg(obj, filename='debug'):
    with open(filename, mode='w') as f:
        f.write(str(obj))

def notify(t: str):
    sh('notify-send "{}"'.format(t))


def is_true(v):
    if v in ('true', 'yes', 'y'):
        return True
    else:
        return False


def test_function(func):
    def disabled():
        pass

    if TEST == True:
        return disabled
    else:
        return func


@test_function
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


@test_function
def install_pck(prog, pack):
    sh('{} --noconfirm --needed -S {}'.format(prog, pack))
    return 'installing {}...'.format(pack)


@test_function
def batch_install(prog, packages):
    sh('cat {} | {} --noconfirm --needed -S -'.format(packages, prog))


@test_function
def setup_system():
    pass #TODO


@test_function
def change_system_configs():
    pass #TODO


@test_function
def place_systemd_units():
    sh((
        'for i in custom-systemd-units/*;'
        'do cp -i $i /etc/systemd/system;'
        'done'
    ))


@test_function
def setup_lan_pacman_cache():
    msg('setting up LAN Pacman Cache')
    install_pck('powerpill', 'darkhttpd')
    sh('ln -s /var/lib/pacman/sync/*.db /var/cache/pacman/pkg')
    # placing/enabling the unit file along with the others
    # in custom-systemd-units


@test_function
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
def run_bg_thread(task_chan, status_chan, out_chan, kill_chan):
    while True:
        status_chan.put(STATUS_MSG['waiting'])
        task = task_chan.get()

        if task is None:
            break
        elif type(task) == HelperTask:
            task.func(task.args)
        elif type(task) == ShellTask:
            sh = pexpect.spawn("/usr/bin/sh -c '{}'".format(task.cmd), encoding='utf-8')
            sh.timeout = 1/1000
            status_chan.put(task.status_msg)

            while True:
                # send out new lines with channel
                try:
                    sh.expect('\r\n')
                    out_chan.put(sh.before + '\n')
                # task finished
                except pexpect.EOF:
                    break
                # no new lines, so carry on
                except pexpect.TIMEOUT:
                    pass
                # check for kill signal and react
                try:
                    if kill_chan.get_nowait():
                        sh.terminate(force=True)
                        sh.wait()
                        return
                except Empty:
                    pass

                sleep(10/1000)

        task_chan.task_done()


def start_bg_thread():
    task_chan = Queue()
    status_chan = Queue()
    out_chan = Queue()
    kill_chan = Queue()
    bg_thread = Thread(target=run_bg_thread,
                       args=(task_chan, status_chan, out_chan, kill_chan))
    bg_thread.start()

    return bg_thread, task_chan, status_chan, out_chan, kill_chan


def handle_input(user_input, fg_state, task_chan):
    if user_input == 'sleep':
        task = ShellTask('sleep 10', 'sleeping for 10 secs...')
        task_chan.put(task)
    elif user_input != '':
        task = ShellTask('echo {}'.format(user_input), '')
        task_chan.put(task)

    return QUESTIONS[fg_state]
